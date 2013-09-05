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
    
Created on Aug 31, 2013

@author: Stefan Guna
'''
from django.contrib.auth.models import User
from django.db import models
from habitam.entities.models import Apartment, ApartmentGroup
from habitam.financial.models import OperationDoc


ORDER_STATUS = (
    ('submitted', 'submitted'),
    ('completed', 'completed'),
)

class Order(models.Model):
    building = models.ForeignKey(ApartmentGroup)
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(default='submitted', max_length=10,
                                  choices=ORDER_STATUS)
    user = models.ForeignKey(User)


class ApartmentAmount(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)    
    apartment = models.ForeignKey(Apartment)
    order = models.ForeignKey(Order)


class OrderComplete(models.Model):
    apartment_amount = models.ForeignKey(ApartmentAmount)
    operation_doc = models.ForeignKey(OperationDoc)
    
