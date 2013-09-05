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
    
Created on Sep 5, 2013

@author: Stefan Guna
'''
from habitam.entities.models import Supplier, Service


PAYU_DETAILS = {
    'name': u'PayU',
    'address': 'Opera Center II, Dr. Nicolae Staicovici nr. 2, Et. 6, Sector 5, Bucuresti 050558',
    'fiscal_id': None,
    'registration_id': None,
    'bank': None,
    'county': 'Bucuresti',
    'iban': None,
    'legal_representative': None
}


def __create_payu_supplier(l):
    supplier = Supplier.objects.create(**PAYU_DETAILS)
    supplier.save()
    l.add_entity(supplier, Supplier)
    
def __create_payu_service(l, building, supplier):
    service = Service.objects.create(name=u'plăți online',
                        supplier=supplier, one_time=False,
                        billed=building, quota_type='equally')    
    service.save(money_type='3rd party', account_type='special')
    service.account.online_payments = True
    service.set_quota()
    service.save()
    return service

def set_payu_payments(l):
    try:
        supplier = l.available_suppliers().get(name=PAYU_DETAILS['name'])
    except Supplier.DoesNotExist:
        supplier = __create_payu_supplier(l)
        
    for b in l.available_buildings():
        found = False
        for service in b.services():
            if service.account.online_payments:
                found = True
                break
        if not found:
            __create_payu_service(l, b, supplier)

    
