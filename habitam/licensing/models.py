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
from django.utils import timezone
from habitam.entities.models import ApartmentGroup, Supplier


class License(models.Model):
    buildings = models.ManyToManyField(ApartmentGroup,
        limit_choices_to={'parent': None}, blank=True, null=True)
    max_apartments = models.IntegerField()
    months_back = models.IntegerField()
    suppliers = models.ManyToManyField(Supplier, blank=True, null=True)
    valid_until = models.DateField()
    
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
        return self.buildings.all()
    
    def available_months(self):
        result = []
        today = date.today()
        crnt = date(day=1, month=today.month, year=today.year)
        for i in range(self.months_back):
            tmp = crnt - relativedelta(months=i)
            result.append(tmp)
        return result
    
    def available_suppliers(self):
        return self.suppliers.all()

    def usage_ratio(self):
        return self.apartment_count() * 100 / self.max_apartments
    
    def validate_month(self, building, month):
        today = date.today()
        crnt = date(day=building.close_day, month=today.month, year=today.year)
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
    
    
