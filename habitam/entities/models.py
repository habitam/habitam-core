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
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models.query_utils import Q
from django.utils import timezone
from habitam.financial.models import Account, Quota
from habitam.settings import MAX_ISSUANCE_DAY, MAX_PAYMENT_DUE_DAYS, \
    MAX_PENALTY_PER_DAY, PENALTY_START_DAYS, EPS
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
    
    def __init__(self, account_type, *args, **kwargs):
        if 'name' in kwargs.keys():
            account = Account.objects.create(name=kwargs['name'],
                                             type=account_type)
            kwargs.setdefault('account', account)
        super(SingleAccountEntity, self).__init__(*args, **kwargs)

    def balance(self):
        return self.account.balance()

    class Meta:
        abstract = True
        
    def save(self, account_type, **kwargs):
        try:
            self.account.name = self.__unicode__()
            self.account.save()
        except Account.DoesNotExist:
            self.account = Account.objects.create(holder=self.__unicode__(),
            self.account = Account.objects.create(name=self.__unicode__(),
                                                  type=account_type)
        
        self.account.name = self.name     
        super(SingleAccountEntity, self).save(**kwargs)


class ApartmentGroup(Entity):
    TYPES = (
             ('stair', 'staircase'),
             ('building', 'building')
    )

    default_account = models.ForeignKey(Account, null=True, blank=True,
                                        related_name='default_account')
    issuance_day = models.SmallIntegerField(null=True, blank=True,
            validators=[MaxValueValidator(MAX_ISSUANCE_DAY)])
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
                           apartment_offset, daily_penalty, issuance_day,
                           payment_due_days):
        per_staircase = apartments / staircases
        remainder = apartments % staircases
        
        building = ApartmentGroup.building_create(name=name,
                        daily_penalty=daily_penalty,
                        issuance_day=issuance_day,
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
            user_license.buildings.add(building)
            user_license.save()
        else:
            building.save()
        return building.id
    
    
    @classmethod
    def building_create(cls, name, daily_penalty=None, issuance_day=None,
                        payment_due_days=None):
        default_account = Account.objects.create(type='std')
        penalties_account = Account.objects.create(type='penalties')
        building = ApartmentGroup.objects.create(name=name, type='building',
                                default_account=default_account,
                                penalties_account=penalties_account,
                                daily_penalty=daily_penalty,
                                issuance_day=issuance_day,
                                payment_due_days=payment_due_days)
        
        AccountLink.objects.create(holder=building, account=default_account)
        default_account.name = building.__unicode__()
        default_account.save()
        
        AccountLink.objects.create(holder=building, account=penalties_account)
        penalties_account.name = building.__unicode__()
        penalties_account.save()
        
        return building
    
    
    @classmethod
    def staircase_create(cls, name, parent, daily_penalty=None, issuance_day=None,
                        payment_due_days=None):
        staircase = ApartmentGroup.objects.create(name=name, parent=parent,
                                type='stair', daily_penalty=daily_penalty,
                                issuance_day=issuance_day,
                                payment_due_days=payment_due_days)
        staircase.save()
        
        return staircase
    
    
    def __init__(self, *args, **kwargs):       
        super(ApartmentGroup, self).__init__(*args, **kwargs) 
        self._old_unicode = self.__unicode__()
       
        
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
        return self.account.name
   
    
class Consumption(models.Model):
    consumed = models.DecimalField(null=True, blank=True,
            decimal_places=2, max_digits=4)
    timestamp = models.DateTimeField(auto_now_add=True)

    
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
    
    @classmethod
    def for_account(cls, account):
        logger.debug('Searching apartment for %s' % account)
        try:
            return Apartment.objects.get(account=account)
        except Apartment.DoesNotExist:
            return None

    def __init__(self, *args, **kwargs):       
        super(Apartment, self).__init__('apart', *args, **kwargs) 
        self._old_name = self.name
        self._old_parent = self.parent
        
        
    def __unicode__(self):
        return 'Apartament ' + self.name


    def balance(self):
        penalties_account = self.building().penalties_account
        return self.account.balance(src_exclude=Q(dest=penalties_account))
        
        
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
        
    
    def __monthly_penalties(self, cp, begin, end, day=date.today()):
        building = self.building()
        
        begin_balance = self.account.balance(begin)
        end_balance = self.account.balance(end)
        monthly_debt = end_balance - begin_balance
        next_day = day + relativedelta(days=1)
        payments = self.account.payments(end, next_day, building.penalties_account)
        balance = monthly_debt + payments - cp

        logger.debug('%s -> %s' % (begin_balance, end_balance))
        if balance >= 0:
            logger.debug('No debts at %s %f' % (end, balance))
            return 0, payments
        
        count_since = end + relativedelta(days=building.payment_due_days)
        count_since = count_since + relativedelta(days=PENALTY_START_DAYS)
        days = (day - count_since).days
        
        if days < 0:
            logger.debug('Not enough time (%d) for penalties at %s %f' % 
                         (days, day, balance))
            return 0, payments
        
        penalties = days * building.daily_penalty * balance * -1 / 100 
        
        logger.debug('Penalties %s -> %s are %f for debts are %f in %d days, the monthly debt is %f' % 
                     (begin, end, penalties, balance, days, monthly_debt))
        
        return penalties, payments
     
     
    def penalties(self, day=date.today()):
        logger.debug('Computing penalties for %s at %s' % (self, day))
        building = self.building()
        if building.issuance_day == None:
            return None
        
        last = date(day=building.issuance_day, month=day.month,
                    year=day.year)
        last = last - relativedelta(days=building.payment_due_days)
        last = last - relativedelta(days=PENALTY_START_DAYS)
        
        iterator = date(day=building.issuance_day,
                   month=self.no_penalties_since.month,
                   year=self.no_penalties_since.year)
        nps = start = iterator
        p, cp = 0, 0
        penalties_found = False
        while iterator < last:
            following = iterator + relativedelta(months=1)
            m, cp = self.__monthly_penalties(cp, iterator, following, day)
            p = p + m
            
            if m > 0:
                penalties_found = True
            if not penalties_found:
                nps = iterator
            
            iterator = following
            
            
        if nps != start:
            logger.info('Increment nps for %s(pk=%d) from %s to %s' % 
                        (self, self.pk, start, nps))
            self.no_penalties_since = nps
            self.save()
        
        logger.debug('Penalties for %s at %s are %f' % (self, day, p))    
        p = Decimal(p).quantize(EPS) * -1
        if p == 0:
            return None
        return p
    
    
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
        
        super(Apartment, self).save('apart', **kwargs)
        
        if self._old_parent != self.parent: 
            logger.info('Moving apartment %s from %s to %s, updating quotas',
                        self, self._old_parent, self.parent)
            if self._old_parent != None:
                self._old_parent.update_quotas()
            self.parent.update_quotas()


class ApartmentConsumption(Consumption):
    apartment = models.ForeignKey(Apartment)


class Service(SingleAccountEntity):
    QUOTA_TYPES = (
        ('equally', 'în mod egal'),
        ('inhabitance', 'după număr persoane'),
        ('area', 'după suprafață'),
        ('rooms', 'după număr camere'),
        ('consumption', 'după consum'),
        ('manual', 'cotă indiviză'),
        ('noquota', 'la fiecare introducere'),
    )
    SERVICE_TYPE = (
        ('general', 'serviciu'),
        ('collecting', 'colectare'),
    )
    
    billed = models.ForeignKey(ApartmentGroup)
    quota_type = models.CharField(max_length=15, choices=QUOTA_TYPES)
    service_type = models.CharField(max_length=10, choices=SERVICE_TYPE)
    
    @classmethod
    def for_account(cls, account):
        try:
            return Service.objects.get(account=account)
        except Service.DoesNotExist:
            return None        
   
    def __init__(self, *args, **kwargs): 
        super(Service, self).__init__('std', *args, **kwargs) 
        try:
            self._old_billed = self.billed
        except:
            self._old_billed = None
        try:
            self._old_quota_type = self.quota_type
        except:
            self._old_quota_type = None
            
    def __change_quotas(self):
        if self.quota_type in ['noquota', 'consumption']:
            return False
        return self.quota_type == 'manual' or self._old_billed != self.billed \
            or self._old_quota_type != self.quota_type
    
    def __change_billed(self):
        return self._old_billed != self.billed and self._old_billed != None
    
    def __charge_type(self):
        charge_type = 'invoice'
        if self.service_type == 'collecting':
            charge_type = 'collection'
        return charge_type
    
    def __new_charge_with_quotas(self, amount, no, date):
        accounts = [] 
        for ap in self.billed.apartments():
            accounts.append(ap.account)
        self.account.new_charge(amount, date, no, self.billed.default_account,
                                 accounts, self.__charge_type())
        
    def __new_charge_with_consumptions(self, amount, no, ap_consumptions,
                                       consumption, date):
        ops = []
        db_ap_consumptions = []
        declared = sum(ap_consumptions.values())
        per_unit = amount / consumption
        logger.info('Declared consumption is %f, price per unit is %f' % 
                    (declared, per_unit))
        for k, v in ap_consumptions.items():
            ap = Apartment.objects.get(pk=k)
            total_ap = Decimal(v) / declared * amount
            loss = total_ap - v * per_unit
            logger.info('Consumption for %s is %f, total to pay %f, lost %f' % 
                        (ap, v, total_ap, loss))
            ops.append((ap.account, total_ap, loss))
            db_ap_consumptions.append(ApartmentConsumption(consumed=v,
                                                           apartment=ap))
            
        self.account.new_multi_transfer(no, self.billed.default_account, ops,
                                        date, self.__charge_type())
        
        svc_consumption = ServiceConsumption(consumed=consumption,
                                             service=self)
        
        svc_consumption.save()
        for ap_consumption in db_ap_consumptions:
            ap_consumption.save()
        
         
    def __new_charge_without_quotas(self, ap_sums, no, date):
        ops = []
        for k, v in ap_sums.items():
            ap = Apartment.objects.get(pk=k)
            ops.append((ap.account, v))
        self.account.new_multi_transfer(no, self.billed.default_account, ops,
                                        date, self.__charge_type())
        
    def __unicode__(self):
        return self.name
    
    def __update_quotas(self, ap_quotas):
        if ap_quotas != None and self.quota_type == 'manual':
            self.set_manual_quota(ap_quotas)
            return
        self.set_quota()
        
    def balance(self):
        if self.service_type == 'general':
            return super(Service, self).balance()
        received = self.account.received()
        transferred = self.account.transferred()
        return received - transferred
        
    def building(self):
        return self.billed.building() 
    
    def can_delete(self):
        return self.account.can_delete()
    
    def initial_operation(self):
        return {'amount': 0}
    
    def new_inbound_operation(self, amount, no, ap_sums=None,
                        ap_consumptions=None, consumption=None,
                        date=timezone.now()):
        logger.info('new inbound op for %s amount=%f no=%s ap_sums=%s ap_consumptions=%s consumption=%s date=%s' % 
                    (self, amount, no, ap_sums, ap_consumptions, consumption, date))
        if self.quota_type == 'consumption':
            self.__new_charge_with_consumptions(amount, no, ap_consumptions,
                                                consumption, date)
        elif self.quota_type == 'noquota': 
            self.__new_charge_without_quotas(ap_sums, no, date)
        else:
            self.__new_charge_with_quotas(amount, no, date)

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
        ap_quotas = None
        if 'ap_quotas' in kwargs.keys():
            ap_quotas = kwargs['ap_quotas']
            del kwargs['ap_quotas']
        
        super(Service, self).save('std', **kwargs)
       
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
            raise NameError('Invalid quota type')
        
        for k, v in ap_quotas.items():
            a = Apartment.objects.get(pk=k)
            Quota.set_quota(self.account, a.account, v)
    
    def set_quota(self):
        logger.info('Setting quota %s on %s', self.quota_type, self)
        found = False
        for qt in Service.QUOTA_TYPES:
            if qt[0] == self.quota_type:
                found = True
        if self.quota_type == 'manual' or not found:
            logger.error('Quota type %s is invalid', self.quota_type)
            raise NameError('Invalid quota type')
        
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


class ServiceConsumption(Consumption):
    service = models.ForeignKey(Service)
