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
from habitam.entities.base import Entity, SingleAccountEntity, FiscalEntity
from habitam.entities.billable import Billable
from habitam.entities.penalties import penalties, apartment_payments
from habitam.financial.models import Account, OperationDoc
from habitam.settings import MAX_CLOSE_DAY, MAX_PAYMENT_DUE_DAYS, \
    MAX_PENALTY_PER_DAY
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
    type = models.CharField(max_length=10, choices=TYPES)
    parent = models.ForeignKey('self', null=True, blank=True)
    payment_due_days = models.SmallIntegerField(null=True, blank=True,
            validators=[MaxValueValidator(MAX_PAYMENT_DUE_DAYS)])
    penalties_account = models.ForeignKey(Account, null=True, blank=True,
                                          related_name='penalties_account')
    daily_penalty = models.DecimalField(null=True, blank=True,
            decimal_places=2, max_digits=4,
            validators=[MaxValueValidator(MAX_PENALTY_PER_DAY)])
    
    class LicenseMeta:
        license_accessor = 'for_building'
        license_collection = 'available_buildings'
    
    @classmethod
    def can_add(cls, user_license):
        return user_license.apartment_count() < user_license.max_apartments
    
    @classmethod
    def can_archive(cls, user_license):
        return False
    
    
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
    
    
    def collecting_funds(self):
        return self.__billable(CollectingFund)

    
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
            
    
    def needs_bootstrap(self):
        ap_accounts = (a.account for a in self.apartments())
        for account in ap_accounts:
            if account.has_operations():
                return False
        return True
        
    
    def owned_apartments(self, email):
        in_building = Q(parent__parent=self)
        owned = Q(owner__email=email)
        return Apartment.objects.filter(Q(in_building & owned))
    
    
    def owner_debt(self, email):
        now = timezone.now()
        ts = date(day=self.close_day, month=now.month, year=now.year)
        if ts >= datetime.date(now):
            ts = ts - relativedelta(months=1)
        return reduce(lambda s, ap: s + ap.debt(ts),
                      self.owned_apartments(email), 0)
    
    
    def funds(self):
        apartment_groups = self.apartment_groups()
        result = []
        for a in apartment_groups:
            links = AccountLink.objects.filter(holder=a)
            for link in links:
                result.append(link.account)
        return result 
    
    
    def payments_service(self):
        for s in self.services():
            if s.online_payments:
                return s
        return None
    
    
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
         
            
    def view_fields(self):
        return {
            'Adresa' : self.buildingdetails.address,
            'Nr. înregistrare fiscală': self.buildingdetails.fiscal_id,
            'Nr. registrul comerțului': self.buildingdetails.registration_id,
            'Observații': self.buildingdetails.notes,
        }


class AccountLink(models.Model):
    holder = models.ForeignKey(ApartmentGroup)
    account = models.ForeignKey(Account)
    
    
    def __unicode__(self):
        return self.account.name
    
    
class BuildingDetails(FiscalEntity):
    apartment_group = models.OneToOneField(ApartmentGroup)
    notes = models.CharField(max_length=200)
    
    
class Consumption(models.Model):
    consumed = models.DecimalField(null=True, blank=True,
            decimal_places=2, max_digits=6)
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
    first_name = models.CharField(max_length=200, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    
    class LicenseMeta:
        license_accessor = 'for_owner'
        license_collection = 'available_owners'
    
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
    
    @classmethod
    def by_owner(cls, email):
        return Apartment.objects.filter(Q(owner__email=email))
        

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
    
    def debt(self, ts):
        until = timezone.now() + relativedelta(days=1)
        b = -apartment_payments(self, ts, until) - self.balance(ts)
        return 0 if b < 0 else b
   
    
    def delete(self):
        self.owner.delete()
        super(Apartment, self).delete()
        
    
    def initial_operation(self):
        amount = self.balance()
        penalties = self.penalties()
        if penalties != None:
            amount = amount + penalties
        amount = -1 * amount
        if amount < 0:
            amount = 0
        return {'amount' : amount}
     
    # TODO test this as per https://trello.com/c/djqGiRgQ 
    def penalties(self, when=date.today()):
        return penalties(self, when)
    
    
    def weight(self, quota_type='equally'):
        if quota_type == 'equally':
            return 1
        return getattr(self, quota_type)


    def new_inbound_operation(self, no, amount, receipt, dest_account,
                              date=timezone.now()):
        building = self.building()
        penalties = self.penalties(date)
        if penalties != None:
            penalties = penalties * -1
        else:
            penalties = 0
        logger.info('New payment %s from %s worth %f + %f penalties' % 
                    (no, self, amount, penalties))
        self.account.new_multi_transfer(no, dest_account,
                                [(dest_account, amount - penalties),
                                 (building.penalties_account, penalties)],
                                date, 'transfer', receipt)


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


class Supplier(FiscalEntity):
    archived = models.BooleanField(default=False)
    archive_date = models.DateTimeField(null=True, blank=True) 
    bank = models.CharField(max_length=30, null=True, blank=True)
    county = models.CharField(max_length=30, null=True, blank=True)
    iban = models.CharField(max_length=30, null=True, blank=True)
    legal_representative = models.CharField(max_length=200, null=True, blank=True)
    one_time = models.BooleanField(default=False)
    
    class LicenseMeta:
        license_accessor = 'for_supplier'
        license_collection = 'available_suppliers'
        
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
        
    def view_fields(self):
        return {
            'Adresa' : self.address,
            'Județ': self.county,
            'Nr. înregistrare fiscală': self.fiscal_id,
            'Nr. registrul comerțului': self.registration_id,
            'Bank': self.bank,
            'IBAN': self.iban,
        }
       

class CollectingFund(Billable):
    def charge_type(self):    
        return 'collection'
    
    def balance(self, month=None):
        received = self.account.received(month)
        transferred = self.account.transferred(month)
        return received - transferred  
    
     
class Service(Billable):
    contact = models.CharField(max_length=200, null=True, blank=True)    
    client_id = models.CharField(max_length=50, null=True, blank=True)    
    contract_date = models.DateTimeField(null=True, blank=True) 
    contract_details = models.CharField(max_length=200, null=True, blank=True)    
    contract_id = models.CharField(max_length=50, null=True, blank=True)    
    email = models.EmailField(null=True, blank=True)
    invoice_date = models.IntegerField(null=True, blank=True)
    online_payments = models.BooleanField(default=False) 
    supplier = models.ForeignKey('Supplier', null=True, blank=True) 
    phone = models.CharField(max_length=20, null=True, blank=True)    
    one_time = models.BooleanField(default=False)
    support_phone = models.CharField(max_length=20, null=True, blank=True)    
    
    def can_delete(self):
        if self.online_payments:
            return False
        return super(Service, self).can_delete()
    
    def charge_type(self):
        return 'invoice'
    
    def balance(self, month=None):
        return super(Billable, self).balance(month)

    def without_invoice(self, begin, end):
        return self.account.count_src_operations(begin, end) == 0     
     

class ServiceConsumption(Consumption):
    service = models.ForeignKey(Service)


