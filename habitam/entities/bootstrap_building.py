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
    
Created on Aug 12, 2013

@author: Stefan Guna
'''
from datetime import date
from habitam.entities.models import ApartmentGroup, Person, Apartment, \
    AccountLink
from habitam.financial.models import Account


def __create_building(name, daily_penalty=None, close_day=None,
                    payment_due_days=None):
    default_account = Account.objects.create(type='std')
    penalties_account = Account.objects.create(type='penalties')
    building = ApartmentGroup.objects.create(name=name, type='building',
                            default_account=default_account,
                            penalties_account=penalties_account,
                            daily_penalty=daily_penalty,
                            close_day=close_day,
                            payment_due_days=payment_due_days)
    
    AccountLink.objects.create(holder=building, account=default_account)
    default_account.name = building.__unicode__()
    default_account.save()
    
    AccountLink.objects.create(holder=building, account=penalties_account)
    penalties_account.name = building.__unicode__()
    penalties_account.save()
    
    return building

def __create_staircase(name, parent, daily_penalty=None, close_day=None,
                    payment_due_days=None):
    staircase = ApartmentGroup.objects.create(name=name, parent=parent,
                            type='stair', daily_penalty=daily_penalty,
                            close_day=close_day,
                            payment_due_days=payment_due_days)
    staircase.save()
    
    return staircase


def bootstrap_building(user_license, name, staircases, apartments,
                       apartment_offset, daily_penalty, close_day,
                       payment_due_days):
    per_staircase = apartments / staircases
    remainder = apartments % staircases
    
    building = __create_building(name=name,
                    daily_penalty=daily_penalty,
                    close_day=close_day,
                    payment_due_days=payment_due_days)
    ap_idx = apartment_offset
    today = date.today()
    for i in range(staircases):
        staircase = __create_staircase(parent=building, name=str(i + 1))
        for j in range(per_staircase):
            name = str(ap_idx)
            owner = Person.bootstrap_owner(name)
            Apartment.objects.create(name=name, parent=staircase,
                                     owner=owner, no_penalties_since=today)
            ap_idx = ap_idx + 1
        if i + 1 < staircases:
            continue
        for j in range(remainder):
            name = str(ap_idx)
            owner = Person.bootstrap_owner(name)
            Apartment.objects.create(name=name, parent=staircase,
                                     owner=owner, no_penalties_since=today)
            ap_idx = ap_idx + 1
    if user_license != None:
        user_license.add_entity(building, ApartmentGroup)
    else:
        building.save()
    return building
