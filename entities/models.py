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
    
Created on Apr 8, 2013

@author: Stefan Guna
'''
from decimal import Decimal
from django.db import models
from services.models import Account, Quota
import logging

logger = logging.getLogger(__name__)
    
class Entity(models.Model):
    TYPES = (
             ('apart', 'apartment'),
             ('stair', 'staircase'),
             ('block', 'block')
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=5, choices=TYPES)
    
    class Meta:
        abstract = True 
   
    
class ApartmentGroup(Entity):
    parent = models.ForeignKey('self', null=True, blank=True)
    
    def apartments(self):
        result = []
        for ap in self.apartment_set.all():
            result.append(ap)
        for ag in self.apartmentgroup_set.all():
            result[len(result):] = ag.apartments()
        return result
    

class Person(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()


class Apartment(Entity):
    account = models.ForeignKey(Account, null=True, blank=True)
    owner = models.ForeignKey(Person, related_name='owner', null=True,
                              blank=True)
    parent = models.ForeignKey(ApartmentGroup, null=True, blank=True)
    rented_to = models.ForeignKey(Person, related_name='rented_to',
                                  null=True, blank=True)
    inhabitance = models.SmallIntegerField()
    surface = models.DecimalField(decimal_places=4, max_digits=6)
    rooms = models.SmallIntegerField() 
    floor = models.SmallIntegerField()

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('type', 'apart')
        super(Apartment, self).__init__(*args, **kwargs)

    def balance(self):
        return self.account.balance()
    
    def weight(self, quota_type=None):
        if quota_type == None:
            return 1
        return getattr(self, quota_type)

 
class Service(models.Model):
    name = models.CharField(max_length=100)
    account = models.ForeignKey(Account)
    billed = models.ForeignKey(ApartmentGroup)
    
    def new_invoice(self, new_amount, new_date, new_no):
        accounts = [] 
        for ap in self.billed.apartments():
            accounts.append(ap.account)
        self.account.new_invoice(new_amount, new_date, new_no, accounts)

    def set_quota(self, quota_type=None):
        logger.info('Setting quota ', quota_type, ' on ', self)
        apartments = self.billed.apartments()
        total = reduce(lambda t, a: t + a.weight(quota_type), apartments, 0)
        for a in apartments:
            Quota.set_quota(self.account, a.account,
                            Decimal(a.weight(quota_type)) / Decimal(total))
        
        
