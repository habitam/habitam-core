# -*- coding: utf-8 -*-
'''
This file is part of Habitam.

Habitam is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as 
published by the Free Software Foundation, either version 3 of 
the License, or (at your option) any later version.

Habitam is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public
License along with Habitam. If not, see 
<http://www.gnu.org/licenses/>.
    
Created on Aug 31, 2013

@author: Stefan Guna
'''
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from django.contrib.sites.models import Site
from django.db.models.query_utils import Q
from django.utils import timezone
from django.utils.translation import ugettext as _
from habitam.licensing.models import License
from habitam.payu.models import Order, ApartmentAmount, OrderComplete
from habitam.settings import PAYU_TIMEOUT, PAYU_DEBUG, PAYU_TRANSACTION_CHARGE
import hmac
import logging


DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
EXCLUDE = ('TESTORDER',)


logger = logging.getLogger(__name__)


def complete_order(order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.error('Callback with an invalid order id %d' % order_id)
        return
    amount = 0
    account = order.building.payments_account()
    service = order.building.payments_service()
    for aa in ApartmentAmount.objects.filter(order=order):
        description = _(u'Plată întreținere online %s') % aa.apartment.name
        doc = aa.apartment.new_inbound_operation(description=description,
                    amount=aa.amount, receipt=None, dest_account=account)
        OrderComplete.objects.create(apartment_amount=aa,
                                     operation_doc=doc).save()
        amount = amount + aa.amount
    
    payu_tax = PAYU_TRANSACTION_CHARGE * amount
    description = _(u'Comision tranzacție online')
    service.new_inbound_operation(payu_tax, description=description)
    description = _(u'Plată comision tranzacție online')
    account.new_transfer(payu_tax, description=description,
                         dest_account=service.account)
    order.status = 'completed'
    order.save()  
    

def __create_order(building, user):
    ts = __timestamp(building)
    apartments = building.owned_apartments(user.email)
    
    amount = 0
    order = Order.objects.create(user=user, building=building)
    for ap in apartments:
        debt = ap.debt(ts)
        amount = amount + debt
        ApartmentAmount.objects.create(amount=debt, apartment=ap,
                                       order=order).save
    order.save()
    
    return order, amount

def __sign(key, order):
    s = ''.join(map(lambda (k, v): str(len(v)) + v, order))
    return hmac.new(key, s).hexdigest()

def __timestamp(building):
    now = timezone.now()
    ts = date(day=building.close_day, month=now.month, year=now.year)
    if ts >= datetime.date(now):
        ts = ts - relativedelta(months=1)
    return ts

def __clean_pending(user):
    threshold = timezone.now() - relativedelta(minutes=PAYU_TIMEOUT)
    qt = Q(created__lt=threshold)
    qu = Q(user=user)
    qs = Q(status='submitted')
    Order.objects.filter(Q(qt & qu & qs)).delete()
    

def payform(building, user):
    if pending_payments(building, user):
        raise Exception(_(u'Nu mai pot fi efectuate plăți până când nu se proceseaza cele în derulare'))
    order, amount = __create_order(building, user)
    logger.info('Online payment order %d for building %s on behalf of %s worth %d' % (order.id, building, user, amount))
    l = License.for_building(building)
    
    if not l.payu_available() or building.payments_service() == None:
        raise Exception(_(u'Nu a fost configurată plata pentru această clădire'))
    
    order = [
        ('MERCHANT', l.payu_merchant_id),
        ('ORDER_REF' , 'Habitam ' + str(order.id)),
        ('ORDER_DATE', timezone.now().strftime(DATE_FORMAT)),
        ('ORDER_PNAME[]', 'Intretinere pentru %s' % str(building.name)),
        ('ORDER_PCODE[]', 'Cladire ' + str(building.pk)),
        ('ORDER_PRICE[]', str(amount)),
        ('ORDER_QTY[]', str(1)),
        ('ORDER_VAT[]', str(0)),
        ('ORDER_SHIPPING', str(0)),
        ('ORDER_PRICE_TYPE[]', 'GROSS')
    ] 
    order.extend([
        ('ORDER_HASH', __sign(str(l.payu_merchant_key), order)),
        ('BACK_REF', Site.objects.get_current().domain + '/ui'),
    ])
    
    if PAYU_DEBUG:
        order.append(('TESTORDER', 'TRUE'))
   
    return order   


def pending_payments(building, user):
    __clean_pending(user)
    qb = Q(building=building)
    qu = Q(user=user)
    qs = Q(status='submitted') 
    return Order.objects.filter(Q(qb & qu & qs)).count() > 0 
