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
        
    def save(self, **kwargs):
        try:
            self.account.holder = self.__unicode__()
            self.account.save()
        except Account.DoesNotExist:
            self.account = Account.objects.create(holder=self.__unicode__())
        
        self.account.holder = self.name     
        super(SingleAccountEntity, self).save(**kwargs)


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
        
        building = ApartmentGroup.create(parent=None, name=name,
                                         group_type='building') 
        ap_idx = apartment_offset
        for i in range(staircases):
            staircase = ApartmentGroup.create(parent=building, name=str(i + 1),
                                              group_type='stair')
            for j in range(per_staircase):
                name = str(ap_idx)
                owner = Person.bootstrap_owner(name)
                Apartment.objects.create(name=name, parent=staircase, owner=owner)
                ap_idx = ap_idx + 1
            if i + 1 < staircases:
                continue
            for j in range(remainder):
                name = str(ap_idx)
                owner = Person.bootstrap_owner(name)
                Apartment.objects.create(name=name, parent=staircase, owner=owner)
                ap_idx = ap_idx + 1
        building.save()
        return building.id
    
    
    @classmethod
    def create(cls, name, group_type, parent=None):
        account = Account.objects.create()
        apGroup = ApartmentGroup.objects.create(parent=parent, name=name,
                                type=group_type, default_account=account)
        AccountLink.objects.create(holder=apGroup, account=account)
        account.holder = apGroup.__unicode__()
        account.save()
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
    
    
    def can_delete(self):
        if len(self.apartments()) > 0 or len(self.apartment_groups()) > 1:
            return False
        if len(self.services()) > 0:
            return False
        for account in self.funds():
            if not account.can_delete():
                return False
        return True
    
    
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
        
        
    def funds(self):
        apartment_groups = self.apartment_groups()
        result = []
        for a in apartment_groups:
            links = AccountLink.objects.filter(holder=a)
            for link in links:
                result.append(link.account)
        return result 
    
    
    def save(self, **kwargs):
        try:
            self.default_account.holder = self.__unicode__()
            self.default_account.save()
            account_created = False
        except Account.DoesNotExist:
            account = Account.objects.create(holder=self.__unicode__())
            self.default_account = account
            account_created = True 
        
        if 'building' in kwargs.keys():
            self.parent = kwargs['building']
            del kwargs['building']
        if 'type' in kwargs.keys():
            self.type = kwargs['type']
            del kwargs['type'] 
        super(ApartmentGroup, self).save(**kwargs)
        
        if account_created:
            default_link = AccountLink.objects.create(holder=self, account=account)
            default_link.save()
    
    def services(self):
        result = []
        result.extend(self.service_set.all())
        for ag in self.apartmentgroup_set.all():
            result.extend(ag.services())
        return result
    
       
    def update_quotas(self):
        for svc in self.service_set.all():
            svc.set_quota()


class AccountLink(models.Model):
    holder = models.ForeignKey(ApartmentGroup)
    account = models.ForeignKey(Account)
    
    
    def __unicode__(self):
        return self.account.holder
   
    
class Person(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(null=True, blank=True)
   
    @classmethod
    def bootstrap_owner(cls, name):
        return Person.objects.create(name=Person.default_owner_name(name))
    
    @classmethod 
    def default_owner_name(cls, name): 
        return 'Proprietar ' + name
    
    def __unicode__(self):
        return self.name
    
    def can_delete(self):
        return False


class Apartment(SingleAccountEntity):
    owner = models.ForeignKey(Person, related_name='owner')
    parent = models.ForeignKey(ApartmentGroup, null=True, blank=True)
    rented_to = models.ForeignKey(Person, related_name='rented_to',
                                  null=True, blank=True)
    inhabitance = models.SmallIntegerField(default=0)
    area = models.DecimalField(default=1, decimal_places=2, max_digits=6)
    rooms = models.SmallIntegerField(default=1) 
    floor = models.SmallIntegerField(null=True, blank=True)

    def __init__(self, *args, **kwargs):       
        super(Apartment, self).__init__(*args, **kwargs) 
        self._old_name = self.name
        self._old_parent = self.parent
        
        
    def __unicode__(self):
        return 'Apartament ' + self.name
        
        
    def building(self):
        return self.parent.building()


    def can_delete(self):
        return self.account.can_delete() and not self.account.has_quotas()
   
    
    def delete(self):
        self.owner.delete()
        super(Apartment, self).delete()
        
    
    def weight(self, quota_type='equally'):
        if quota_type == 'equally':
            return 1
        return getattr(self, quota_type)


    def new_inbound_operation(self, amount, date=timezone.now()):
        no = uuid1()
        building = self.building()
        logger.info('New payment %s from %s to %s worth %f', no, self, building,
                    amount)
        self.account.new_transfer(amount, no, building.default_account, date)


    def save(self, **kwargs):
        try:
            if self.owner.name == Person.default_owner_name(self._old_name):
                self.owner.name = Person.default_owner_name(self.name)
                self.owner.save()
        except Person.DoesNotExist:
            self.owner = Person.bootstrap_owner(self.name) 
        
        super(Apartment, self).save(**kwargs)
        print self.parent
        
        if self._old_parent != self.parent: 
            logger.info('Moving apartment %s from %s to %s, updating quotas',
                        self, self._old_parent, self.parent)
            if self._old_parent != None:
                self._old_parent.update_quotas()
            self.parent.update_quotas()
            
 
class Service(SingleAccountEntity):
    QUOTA_TYPES = (
        ('equally', 'în mod egal'),
        ('inhabitance', 'după număr persoane'),
        ('area', 'după suprafață'),
        ('rooms', 'după număr camere')
    )
    billed = models.ForeignKey(ApartmentGroup)
    quota_type = models.CharField(max_length=15, choices=QUOTA_TYPES)

   
    def __init__(self, *args, **kwargs): 
        super(Service, self).__init__(*args, **kwargs) 
        try:
            self._old_billed = self.billed
        except:
            self._old_billed = None
        try:
            self._old_quota_type = self.quota_type
        except:
            self._old_quota_type = None
    
    def __unicode__(self):
        return self.name
        
    def building(self):
        return self.billed.building() 
    
    def can_delete(self):
        return self.account.can_delete()
    
    def new_inbound_operation(self, amount, no, date=timezone.now()):
        accounts = [] 
        for ap in self.billed.apartments():
            accounts.append(ap.account)
        self.account.new_invoice(amount, date, no, self.billed.default_account,
                                 accounts)

    def delete(self):
        if not self.can_delete():
            raise ValueError('Cannot delete this service')
        Quota.del_quota(self.account)
        self.account.delete()
        super(Service, self).delete()

    def drop_quota(self):
        logger.info('Pruning all quotas on %s', self)
        Quota.del_quota(self.account)

    def save(self, **kwargs):
        super(Service, self).save(**kwargs)
       
        if self._old_billed != self.billed and self._old_billed != None:
            self.drop_quota()
        if self._old_billed != self.billed or self._old_quota_type != self.quota_type:
            self.set_quota()
    
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
