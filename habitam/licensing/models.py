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
    
Created on Apr 24, 2013

@author: Stefan Guna
'''
from datetime import date
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.db import models
from django.db.models.aggregates import Count
from django.db.models.query_utils import Q
from django.utils import timezone
from habitam.entities.accessor import building_for_account
from habitam.entities.models import ApartmentGroup, Supplier, Apartment, Person
from habitam.financial.models import Account


class License(models.Model):
    buildings = models.ManyToManyField(ApartmentGroup,
        limit_choices_to={'parent': None}, blank=True, null=True)
    max_apartments = models.IntegerField()
    months_back = models.IntegerField()
    suppliers = models.ManyToManyField(Supplier, blank=True, null=True)
    valid_until = models.DateField()
    
    @classmethod
    def for_building(cls, building):
        licenses = License.objects.filter(buildings=building)[:1]
        return licenses[0]
    
    @classmethod
    def for_fund(cls, fund):
        account = Account.objects.get(fund.pk)
        building = building_for_account(account)
        return License.for_building(building)
    
    @classmethod
    def for_owner(cls, owner):
        ap = Apartment.objects.filter(owner=owner)[:1]
        return License.for_building(ap.building())

    @classmethod
    def for_supplier(cls, supplier):
        licenses = License.objects.filter(suppliers=supplier)[:1]
        return licenses[0]
    
    def __latest(self):
        today = date.today()
        crnt = date(day=1, month=today.month, year=today.year)
        return crnt - relativedelta(months=self.months_back)
    
    def add_entity(self, entity, entity_cls):
        entity_collections = {ApartmentGroup: self.buildings,
                              Supplier: self.suppliers}
        entity_collections[entity_cls].add(entity)
        self.save()
    
    def apartment_count(self):
        no = 0
        for b in self.buildings.all():
            no = no + len(b.apartments())
        return no
    
    def available_buildings(self):
        b = self.buildings.all()
        return b.annotate(apartment_count=Count('apartmentgroup__apartment'))
    
    def available_months(self):
        result = []
        today = date.today()
        crnt = date(day=1, month=today.month, year=today.year)
        for i in range(self.months_back):
            tmp = crnt - relativedelta(months=i)
            result.append(tmp)
        return result
    
    def available_funds(self):
        return Account.objects.filter(accountlink__holder__license=self)
    
    def available_owners(self):
        return Person.objects.filter(owner__parent__parent__license=self)
    
    def available_suppliers(self):
        q = Q(~Q(archived=True) | Q(archive_date__gt=self.__latest()))
        q = Q(q & ~Q(one_time=True))
        s = self.suppliers.filter(q)
        return s.annotate(service_count=Count('service'))
    
    def top_buildings(self):
        return self.available_buildings().order_by('-apartment_count')
    
    def top_suppliers(self):
        return self.available_suppliers().order_by('-service_count')

    def usage_ratio(self):
        return self.apartment_count() * 100 / self.max_apartments
    
    def validate_month(self, building, month):
        crnt = date.today()
        if month > crnt:
            raise ValueError('Received a future value')
        first = crnt - relativedelta(months=self.months_back)
        if month < first:
            raise ValueError('Received a value outside of the licensed range')
        
    def valid_timestamp(self, ts):
        today = timezone.now()
        limit = today - relativedelta(months=self.months_back)
        return ts >= limit
    
    
class Administrator(models.Model):
    user = models.OneToOneField(User)
    license = models.ForeignKey(License)
    
    
