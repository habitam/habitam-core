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
    
Created on Apr 8, 2013

@author: Stefan Guna
'''
from decimal import Decimal
from django.db import models
from django.utils import timezone
from habitam.services.models import Account, Quota
from uuid import uuid1
import logging

logger = logging.getLogger(__name__)

    
class Entity(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True 


class SingleAccountEntity(Entity):   
    account = models.ForeignKey(Account)
    
    def __init__(self, *args, **kwargs):
        if 'name' in kwargs.keys():
            kwargs.setdefault('account', Account.objects.create(holder=kwargs['name']))
        super(SingleAccountEntity, self).__init__(*args, **kwargs)

    def balance(self):
        return self.account.balance()

    class Meta:
        abstract = True 


class ApartmentGroup(Entity):
    TYPES = (
             ('stair', 'staircase'),
             ('building', 'building')
    )

    parent = models.ForeignKey('self', null=True, blank=True)
    type = models.CharField(max_length=5, choices=TYPES)
    default_account = models.ForeignKey(Account)
  
    @classmethod
    def bootstrap_building(cls, name, staircases, apartments, apartment_offset):
        per_staircase = apartments / staircases
        remainder = apartments % staircases
        
        building = ApartmentGroup.bootstrap(None, name, 'building') 
        ap_idx = apartment_offset
        for i in range(staircases):
            staircase = ApartmentGroup.bootstrap(building, str(i + 1), 'stair')
            for j in range(per_staircase):
                Apartment.objects.create(name=str(ap_idx), parent=staircase)
                ap_idx = ap_idx + 1
            if i + 1 < staircases:
                continue
            for j in range(remainder):
                Apartment.objects.create(name=str(ap_idx), parent=staircase)
                ap_idx = ap_idx + 1
        building.save()
    
    
    
    @classmethod
    def bootstrap(cls, parent, name, group_type):
        account = Account.objects.create()
        apGroup = ApartmentGroup.objects.create(parent=parent, name=name,
                                type=group_type, default_account=account)
        AccountLink.objects.create(holder=apGroup, account=account)
        return apGroup
    
    
    def __unicode__(self):
        if self.type == 'building':
            return 'Block ' + self.name
        if self.type == 'stair':
            return 'Scara ' + self.name
        return self.name
    
    
    def balance(self):
        links = self.accountlink_set.all()
        mine = reduce(lambda s, l: s + l.account.balance(), links, 0)
        ags = self.apartmentgroup_set.all()
        if ags == None:
            return mine
        return reduce(lambda s, ag: s + ag.balance(), ags, mine)
    
    
    def building(self):
        if self.type == 'building':
            return self
        return self.parent.building()
    
    
    def apartment_groups(self):
        result = [self]
        for ag in self.apartmentgroup_set.all():
            result.extend(ag.apartment_groups())
        return result                  
        
                      
    def apartments(self):
        result = []
        for ap in self.apartment_set.all():
            result.append(ap)
        for ag in self.apartmentgroup_set.all():
            result.extend(ag.apartments())
        return result
   
    
    def add_service(self, name, quota_type=None):
        try:
            Service.objects.get(name=name, billed=self)
            raise NameError('Service ' + name + ' already exists')
        except Service.DoesNotExist:
            pass
        
        service = Service.objects.create(name=name, billed=self,
                                         quota_type=quota_type)
        service.set_quota(quota_type)
        service.save()
        
    
    def services(self):
        result = []
        result.extend(self.service_set.all())
        for ag in self.apartmentgroup_set.all():
            result.extend(ag.services())
        return result
    
    
    def update_quotas(self):
        for svc in self.services_set.all():
            svc.set_quota()


class AccountLink(models.Model):
    holder = models.ForeignKey(ApartmentGroup)
    account = models.ForeignKey(Account) 
   
    
class Person(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()


class Apartment(SingleAccountEntity):
    owner = models.ForeignKey(Person, related_name='owner', null=True,
                              blank=True)
    parent = models.ForeignKey(ApartmentGroup, null=True, blank=True)
    rented_to = models.ForeignKey(Person, related_name='rented_to',
                                  null=True, blank=True)
    inhabitance = models.SmallIntegerField(default=0)
    area = models.DecimalField(default=1, decimal_places=4, max_digits=6)
    rooms = models.SmallIntegerField(default=1) 
    floor = models.SmallIntegerField(null=True, blank=True)

    
    def building(self):
        return self.parent.building()


    def weight(self, quota_type='equally'):
        if quota_type == 'equally':
            return 1
        return getattr(self, quota_type)


    def new_payment(self, amount, date=timezone.now()):
        no = uuid1()
        self.account.new_transfer(amount, date, no, self.parent.account)
    
 
class Service(SingleAccountEntity):
    QUOTA_TYPES = (
        ('equally', 'în mod egal'),
        ('inhabitance', 'după număr persoane'),
        ('area', 'după suprafață'),
        ('rooms', 'după număr camere')
    )
    billed = models.ForeignKey(ApartmentGroup)
    quota_type = models.CharField(max_length=15, choices=QUOTA_TYPES)
   
    
    def new_invoice(self, amount, no, date=timezone.now()):
        accounts = [] 
        for ap in self.billed.apartments():
            accounts.append(ap.account)
        self.account.new_invoice(amount, date, no, self.billed.default_account,
                                 accounts)

    
    def new_payment(self, amount, no, date=timezone.now()):
        self.billed.account.new_payment(amount, date, no, self.account)
        
        
    def drop_quota(self):
        logger.info('Pruning all quotas on %s', self)
        Quota.del_quota(self.account)
    
    
    def set_quota(self):
        self.drop_quota()
        
        logger.info('Setting quota %s on %s', self.quota_type, self)
        found = False
        for qt in Service.QUOTA_TYPES:
            if qt[0] == self.quota_type:
                found = True
        if not found:
            logger.error('Quota type %s is invalid', self.quota_type)
            raise NameError('Invalid quota type')
        
        apartments = self.billed.apartments()
        total = reduce(lambda t, a: t + a.weight(self.quota_type), apartments,
                       0)
        for a in apartments:
            Quota.set_quota(self.account, a.account,
                        Decimal(a.weight(self.quota_type)) / Decimal(total))
