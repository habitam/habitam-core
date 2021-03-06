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
    
Created on Jul 15, 2013

@author: Stefan Guna
'''
from datetime import datetime
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _
from habitam.entities.accessor import apartment_by_pk, apartment_consumption, \
    service_consumption
from habitam.entities.base import SingleAccountEntity
from habitam.financial.models import Quota
import logging

logger = logging.getLogger(__name__)

class Billable(SingleAccountEntity):
    QUOTA_TYPES = (
        ('equally', _(u'în mod egal')),
        ('inhabitance', _(u'după număr persoane')),
        ('area', _(u'după suprafață')),
        ('rooms', _(u'după număr camere')),
        ('consumption', _(u'după consum')),
        ('manual', _(u'cotă indiviză')),
        ('noquota', _('la fiecare introducere')),
    )
    
    archived = models.BooleanField(default=False)
    archive_date = models.DateTimeField(null=True, blank=True) 
    billed = models.ForeignKey('ApartmentGroup')
    quota_type = models.CharField(max_length=15, choices=QUOTA_TYPES)    
    
    class Meta:
        abstract = True
        
    def __init__(self, *args, **kwargs):
        money_type = kwargs['money_type'] if 'money_type' in kwargs else 'money_type'
        account_type = kwargs['account_type'] if 'account_type' in kwargs else 'std'
        if 'account_type' in kwargs: del kwargs['account_type']
        if 'money_type' in kwargs: del kwargs['money_type']
        super(Billable, self).__init__(account_type, money_type, *args, **kwargs) 
        try:
            self._old_billed = self.billed
        except:
            self._old_billed = None
        try:
            self._old_quota_type = self.quota_type
        except:
            self._old_quota_type = None
        self._old_archived = self.archived
            
    def __change_quotas(self):
        if self.quota_type in ['noquota', 'consumption']:
            return False
        return self.quota_type == 'manual' or self._old_billed != self.billed \
            or self._old_quota_type != self.quota_type
    
    def __change_billed(self):
        return self._old_billed != self.billed and self._old_billed != None
    
    def __new_charge_with_quotas(self, amount, description, date, invoice):
        accounts = [] 
        for ap in self.billed.apartments():
            accounts.append(ap.account)
        mine = self.billed.default_account
        account = mine if mine != None else self.building().default_account
        self.account.new_charge(amount, date, description, account, accounts,
                                self.charge_type(), invoice)
        
    def __new_charge_with_consumptions(self, amount, description, ap_consumptions,
                                       consumption, date, invoice):
        ops = []
        db_ap_consumptions = []
        declared = sum(ap_consumptions.values())
        if declared > consumption:
            raise NameError(_('Ceva e ciudat cu consumul declarat! E mai mare decat cel de pe document! Declarat de locatari=') + str(declared))
        per_unit = amount / consumption
        logger.info('Declared consumption is %f, price per unit is %f' % 
                    (declared, per_unit))
        for k, v in ap_consumptions.items():
            ap = apartment_by_pk(k)
            total_ap = Decimal(v) / declared * amount
            loss = total_ap - v * per_unit
            logger.info('Consumption for %s is %f, total to pay %f, lost %f' % 
                        (ap, v, total_ap, loss))
            ops.append((ap.account, total_ap, loss))
            db_ap_consumptions.append(apartment_consumption(v, ap))
            
        doc = self.account.new_multi_transfer(description, self.billed.default_account,
                                        ops, date, self.charge_type(),
                                        invoice=invoice)
        
        svc_consumption = service_consumption(consumption, self, doc)
        
        svc_consumption.save()
        for ap_consumption in db_ap_consumptions:
            ap_consumption.doc = doc
            ap_consumption.save()
        
         
    def __new_charge_without_quotas(self, ap_sums, description, date, invoice):
        ops = []
        for k, v in ap_sums.items():
            ap = apartment_by_pk(k)
            ops.append((ap.account, v))
        self.account.new_multi_transfer(description, self.billed.default_account, ops,
                                        date, self.charge_type(),
                                        invoice=invoice)
        
    def __unicode__(self):
        return self.name
    
    def __update_archived(self):
        if self.archived == False:
            self.archive_date = None
            return
        if self.archived == self._old_archived:
            return
        self.archive_date = datetime.now()
        
    def __update_quotas(self, ap_quotas):
        if ap_quotas != None and self.quota_type == 'manual':
            self.set_manual_quota(ap_quotas)
            return
        self.set_quota()
        
    def building(self):
        return self.billed.building() 
    
    def can_delete(self):
        return self.account.can_delete()
    
    def initial_operation(self):
        return {'amount': 0}
    
    def new_inbound_operation(self, amount, description, invoice=None, ap_sums=None,
                        ap_consumptions=None, consumption=None,
                        date=timezone.now()):
        logger.info(u'new inbound op for %s amount=%f description=%s ap_sums=%s ap_consumptions=%s consumption=%s date=%s' % 
                    (self, amount, description, ap_sums, ap_consumptions, consumption, date))
        if ap_consumptions != None:
            self.__new_charge_with_consumptions(amount, description, ap_consumptions,
                                                consumption, date, invoice)
        elif ap_sums != None: 
            self.__new_charge_without_quotas(ap_sums, description, date, invoice)
        else:
            self.__new_charge_with_quotas(amount, description, date, invoice)

    def delete(self):
        if not self.can_delete():
            raise ValueError(_(u'Acest serviciu nu se poate șterge'))
        Quota.del_quota(self.account)
        self.account.delete()
        super(Billable, self).delete()

    def drop_quota(self):
        logger.info('Pruning all quotas on %s', self)
        Quota.del_quota(self.account)

    def save(self, **kwargs):
        ap_quotas = None
        if 'ap_quotas' in kwargs.keys():
            ap_quotas = kwargs['ap_quotas']
            del kwargs['ap_quotas']
        self.__update_archived()
        
        #TODO this is a hack
        if not 'money_type' in kwargs:
            kwargs['money_type'] = 'cash'
        if not 'account_type' in kwargs:
            kwargs['account_type'] = 'special'
 
        super(Billable, self).save(**kwargs)
       
        if self.__change_billed() or self.__change_quotas() or \
            self.quota_type in ['noquota', 'consumption']:
            self.drop_quota()
        if self.__change_quotas():
            self.__update_quotas(ap_quotas)
    
    def set_manual_quota(self, ap_quotas):            
        logger.info('Setting quota %s (%s) on %s', self.quota_type, ap_quotas,
                     self)
        if self.quota_type != 'manual':
            logger.error('Quota type %s is invalid', self.quota_type)
            raise NameError(_(u'Tipul de cotă este invalid'))
        
        for k, v in ap_quotas.items():
            a = apartment_by_pk(k)
            Quota.set_quota(self.account, a.account, v)
    
    def set_quota(self):
        logger.info('Setting quota %s on %s', self.quota_type, self)
        found = False
        for qt in Billable.QUOTA_TYPES:
            if qt[0] == self.quota_type:
                found = True
        if self.quota_type in ['manual', 'noquota'] or not found:
            logger.error('Quota type %s is invalid', self.quota_type)
            raise NameError(_(u'Tipul de cotă este invalid'))
        
        apartments = self.billed.apartments()
        total = reduce(lambda t, a: t + a.weight(self.quota_type), apartments,
                       0)
        for a in apartments:
            Quota.set_quota(self.account, a.account,
                        Decimal(a.weight(self.quota_type)) / Decimal(total))

    def to_collect(self):
        charged = self.account.charged()
        received = self.account.received()
        return charged - received

