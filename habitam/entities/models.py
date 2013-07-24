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
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models.query_utils import Q
from django.utils import timezone
from habitam.entities.base import Entity, SingleAccountEntity
from habitam.entities.billable import Billable
from habitam.entities.penalties import penalties
from habitam.financial.models import Account, OperationDoc
from habitam.settings import MAX_CLOSE_DAY, MAX_PAYMENT_DUE_DAYS, \
    MAX_PENALTY_PER_DAY
from uuid import uuid1
import logging

logger = logging.getLogger(__name__)


class ApartmentGroup(Entity):
    TYPES = (
             ('stair', 'staircase'),
             ('building', 'building')
    )

    close_day = models.SmallIntegerField(null=True, blank=True,
            validators=[MaxValueValidator(MAX_CLOSE_DAY)])
    default_account = models.ForeignKey(Account, null=True, blank=True,
                                        related_name='default_account')
    type = models.CharField(max_length=5, choices=TYPES)
    parent = models.ForeignKey('self', null=True, blank=True)
    payment_due_days = models.SmallIntegerField(null=True, blank=True,
            validators=[MaxValueValidator(MAX_PAYMENT_DUE_DAYS)])
    penalties_account = models.ForeignKey(Account, null=True, blank=True,
                                          related_name='penalties_account')
    daily_penalty = models.DecimalField(null=True, blank=True,
            decimal_places=2, max_digits=4,
            validators=[MaxValueValidator(MAX_PENALTY_PER_DAY)])
  
    @classmethod
    def bootstrap_building(cls, user_license, name, staircases, apartments,
                           apartment_offset, daily_penalty, close_day,
                           payment_due_days):
        per_staircase = apartments / staircases
        remainder = apartments % staircases
        
        building = ApartmentGroup.building_create(name=name,
                        daily_penalty=daily_penalty,
                        close_day=close_day,
                        payment_due_days=payment_due_days)
        ap_idx = apartment_offset
        today = date.today()
        for i in range(staircases):
            staircase = ApartmentGroup.staircase_create(parent=building,
                                                        name=str(i + 1))
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
        return building.id
    
    
    @classmethod
    def building_create(cls, name, daily_penalty=None, close_day=None,
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
    
    @classmethod
    def can_add(cls, user_license):
        return user_license.apartment_count() < user_license.max_apartments
    
    @classmethod
    def can_archive(cls, user_license):
        return False
     
    @classmethod
    def staircase_create(cls, name, parent, daily_penalty=None, close_day=None,
                        payment_due_days=None):
        staircase = ApartmentGroup.objects.create(name=name, parent=parent,
                                type='stair', daily_penalty=daily_penalty,
                                close_day=close_day,
                                payment_due_days=payment_due_days)
        staircase.save()
        
        return staircase
    
    
    def __billable(self, billable_type):
        result = []
        result.extend(billable_type.objects.filter(billed=self))
        for ag in self.apartmentgroup_set.all():
            result.extend(ag.__billable(billable_type))
        return result
        
    
    def __init__(self, *args, **kwargs):       
        super(ApartmentGroup, self).__init__(*args, **kwargs) 
        self._old_unicode = self.__unicode__()
       
        
    def __unicode__(self):
        if self.type == 'building':
            return 'Block ' + self.name
        if self.type == 'stair':
            return 'Scara ' + self.name
        return self.name
    
    
    def available_list_months(self, months_back):
        result = []
        today = date.today()
        crnt = date(day=self.close_day, month=today.month, year=today.year)
        for i in range(1, months_back):
            tmp = crnt - relativedelta(months=i)
            result.append(tmp)
        return result
    
    
    def balance(self, month=None):
        links = self.accountlink_set.all()
        mine = reduce(lambda s, l: s + l.account.balance(month), links, 0)
        ags = self.apartmentgroup_set.all()
        if ags == None:
            return mine
        return reduce(lambda s, ag: s + ag.balance(month), ags, mine)
    
    
    def balance_by_type(self, account_selector, month):
        accounts = filter(account_selector, self.funds())
        balance = reduce(lambda s, ac: s + ac.balance(month), accounts, 0)
        
        collecting_accounts = map(lambda cf: cf.account, self.collecting_funds())
        collecting_funds = filter(account_selector, collecting_accounts)
        balance = reduce(lambda s, ac: s + ac.balance(month), collecting_funds, balance)
        
        return balance
    
    
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
    
    
    def collecting_funds(self):
        return self.__billable(CollectingFund)
    
        
    def display_dates(self, since, until):
        q = self.displaydate_set.filter(Q(timestamp__gt=since) & 
                                        Q(timestamp__lt=until))
        print '####', since, until
        return q.order_by('month') 
    
    def list_downloaded(self, month):
        month = date(day=self.close_day, month=month.month, year=month.year)
        try:
            self.displaydate_set.get(month=month)
        except DisplayDate.DoesNotExist:
            return False
        return True

        
    def mark_display(self, month):
        month = date(day=self.close_day, month=month.month, year=month.year)
        # TODO(Stefan) need to synchronize this https://trello.com/c/KztkJ8mt
        try:
            self.displaydate_set.get(month=month)
        except DisplayDate.DoesNotExist:
            dd = DisplayDate.objects.create(building=self, month=month,
                                            timestamp=datetime.now())
            dd.save()
        

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
            if self.default_account.name == self._old_unicode:
                self.default_account.name = self.__unicode__()
                self.default_account.save()
        except AttributeError:
            pass
        try:
            if self.penalties_account.name == self._old_unicode:
                self.penalties_account.name = self.__unicode__()
                self.penalties_account.save()
        except AttributeError:
            pass
        
        if 'building' in kwargs.keys():
            self.parent = kwargs['building']
            del kwargs['building']
        if 'type' in kwargs.keys():
            self.type = kwargs['type']
            del kwargs['type'] 
        super(ApartmentGroup, self).save(**kwargs)
        self._old_unicode = self.__unicode__()
    
    
    def services(self):
        return self.__billable(Service)
    

    def services_without_invoice(self, month):
        begin = date(day=self.close_day, month=month.month, year=month.year)
        end = begin + relativedelta(months=1)
        return filter(lambda x: x.without_invoice(begin, end), self.services())
    
       
    def update_quotas(self):
        for svc in self.service_set.all():
            svc.set_quota()


class AccountLink(models.Model):
    holder = models.ForeignKey(ApartmentGroup)
    account = models.ForeignKey(Account)
    
    
    def __unicode__(self):
        return self.account.name
   
    
class Consumption(models.Model):
    consumed = models.DecimalField(null=True, blank=True,
            decimal_places=2, max_digits=4)
    doc = models.ForeignKey(OperationDoc) 


class DisplayDate(models.Model):
    building = models.ForeignKey(ApartmentGroup)
    timestamp = models.DateTimeField()
    month = models.DateField()
    
    def buildingdisplay_date(self):
        ts = self.timestamp
        return date(day=ts.day, month=ts.month, year=ts.year)
    
    
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
    area = models.DecimalField(default=1, decimal_places=2, max_digits=6)
    floor = models.SmallIntegerField(null=True, blank=True)
    inhabitance = models.SmallIntegerField(default=0)
    no_penalties_since = models.DateField()
    owner = models.ForeignKey(Person, related_name='owner')
    parent = models.ForeignKey(ApartmentGroup, null=True, blank=True)
    rented_to = models.ForeignKey(Person, related_name='rented_to',
                                  null=True, blank=True)
    rooms = models.SmallIntegerField(default=1)

    def __init__(self, *args, **kwargs):       
        super(Apartment, self).__init__('apart', '3rd party', *args, **kwargs)
        self._old_name = self.name
        self._old_parent = self.parent
        
        
    def __unicode__(self):
        return 'Apartament ' + self.name


    def balance(self, month=None):
        penalties_account = self.building().penalties_account
        return self.account.balance(month, Q(dest=penalties_account))
        
        
    def building(self):
        return self.parent.building()


    def can_delete(self):
        return self.account.can_delete() and not self.account.has_quotas()
   
    
    def delete(self):
        self.owner.delete()
        super(Apartment, self).delete()
        
    
    def initial_operation(self):
        amount = self.balance()
        penalties = self.penalties()
        if penalties != None:
            amount = amount + penalties
        return {'amount' :-1 * amount}
     
    # TODO test this as per https://trello.com/c/djqGiRgQ 
    def penalties(self, day=date.today()):
        penalties(self, day)
    
    
    def weight(self, quota_type='equally'):
        if quota_type == 'equally':
            return 1
        return getattr(self, quota_type)


    def new_inbound_operation(self, amount, dest_account, date=timezone.now()):
        no = uuid1()
        building = self.building()
        penalties = self.penalties()
        if penalties != None:
            penalties = penalties * -1
        else:
            penalties = 0
        logger.info('New payment %s from %s worth %f + %f penalties' % 
                    (no, self, amount, penalties))
        self.account.new_multi_transfer(no, dest_account,
                                [(dest_account, amount - penalties),
                                 (building.penalties_account, penalties)],
                                date)


    def save(self, **kwargs):
        try:
            if self.owner.name == Person.default_owner_name(self._old_name):
                self.owner.name = Person.default_owner_name(self.name)
                self.owner.save()
        except Person.DoesNotExist:
            self.owner = Person.bootstrap_owner(self.name)
             
        if self.no_penalties_since == None:
            self.no_penalties_since = date.today() 
        
        super(Apartment, self).save('apart', '3rd party', **kwargs)
        
        if self._old_parent != self.parent: 
            logger.info('Moving apartment %s from %s to %s, updating quotas',
                        self, self._old_parent, self.parent)
            if self._old_parent != None:
                self._old_parent.update_quotas()
            self.parent.update_quotas()


class ApartmentConsumption(Consumption):
    apartment = models.ForeignKey(Apartment)


class Supplier(models.Model):
    archived = models.BooleanField(default=False)
    archive_date = models.DateTimeField(null=True, blank=True) 
    name = models.CharField(max_length=200)
    one_time = models.BooleanField(default=False)
   
    @classmethod
    def can_add(cls, user_license):
        return True 
    
    @classmethod
    def can_archive(cls, user_license):
        return True
    
    @classmethod
    def use_license(cls):
        return True
    
    def __init__(self, *args, **kwargs):
        super(Supplier, self).__init__(*args, **kwargs)
        self._old_archived = self.archived
        
    def __unicode__(self):
        return self.name
    
    def __update_archived(self):
        if self.archived == False:
            self.archive_date = None
            return
        if self.archived == self._old_archived:
            return
        self.archive_date = datetime.now()
    
    def is_archivable(self):
        return self.service_set.exclude(archived=True).count() == 0
    
    def can_delete(self):
        return self.service_set.count() == 0
    
    def save(self, **kwargs):
        self.__update_archived()
        super(Supplier, self).save(**kwargs) 
       

class CollectingFund(Billable):
    def charge_type(self):    
        return 'collection'
    
    def balance(self, month=None):
        received = self.account.received(month)
        transferred = self.account.transferred(month)
        return received - transferred  
    
     
class Service(Billable):
    supplier = models.ForeignKey('Supplier', null=True, blank=True) 
    one_time = models.BooleanField(default=False)
    
    def charge_type(self):
        return 'invoice'
    
    def balance(self, month):
        return super(Billable, self).balance(month)

    def without_invoice(self, begin, end):
        return self.account.count_src_operations(begin, end) == 0     
     

class ServiceConsumption(Consumption):
    service = models.ForeignKey(Service)


