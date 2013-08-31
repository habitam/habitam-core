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
from django.contrib import admin
from django.db.models.aggregates import Sum
from habitam.payu.models import Order, ApartmentAmount

def order_amount(order):
    r = ApartmentAmount.objects.filter(order=order).aggregate(Sum('amount'))
    return r['amount__sum']
order_amount.short_description = 'Suma'

class OrderAdmin(admin.ModelAdmin):
    list_display = ('created', 'status', 'user', order_amount)

admin.site.register(Order, OrderAdmin)        
    
