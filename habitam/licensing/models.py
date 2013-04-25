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
from django.contrib.auth.models import User
from django.db import models
from habitam.entities.models import ApartmentGroup


class License(models.Model):
    buildings = models.ManyToManyField(ApartmentGroup,
                                       limit_choices_to={'parent': None})
    max_apartments = models.IntegerField()
    valid_until = models.DateField()
    
    def apartment_count(self):
        no = 0
        for b in self.buildings.all():
            no = no + len(b.apartments())
        return no
    
    def usage_ratio(self):
        return self.apartment_count() * 100 / self.max_apartments
    
    
class Administrator(models.Model):
    user = models.OneToOneField(User)
    license = models.ForeignKey(License)
    
    
