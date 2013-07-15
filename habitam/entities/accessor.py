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


def apartment_by_pk(pk):
    from habitam.entities.models import Apartment
    return Apartment.objects.get(pk=pk)


def apartment_consumption(consumed, ap):
    from habitam.entities.models import ApartmentConsumption
    return ApartmentConsumption(consumed=consumed, apartment=ap)


def building_for_account(account):
    from habitam.entities.models import Service, CollectingFund, Apartment, \
        AccountLink
    billable_types = [Service, CollectingFund]
    for billable_type in billable_types:
        try:
            entity = billable_type.objects.get(account=account)
            return entity.billed.building()
        except billable_type.DoesNotExist:
            pass
    try:
        apartment = Apartment.objects.get(account=account)
        return apartment.building()
    except Apartment.DoesNotExist:
        pass
    try:
        account_link = AccountLink.objects.get(account=account)
        return account_link.holder.building()
    except AccountLink.DoesNotExist:
        pass
    return None


def service_consumption(consumed, service, doc):
    from habitam.entities.models import ServiceConsumption
    return ServiceConsumption(consumed=consumed, service=service, doc=doc)


def entity_for_account(cls, account):
    try:
        return cls.objects.get(account=account)
    except cls.DoesNotExist:
        return None   