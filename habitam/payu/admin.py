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
from habitam.payu.models import Order, ApartmentAmount, OrderComplete
from habitam.payu.payu import complete_order

def order_amount(order):
    r = ApartmentAmount.objects.filter(order=order).aggregate(Sum('amount'))
    return r['amount__sum']
order_amount.short_description = 'Suma'

class OrderAdmin(admin.ModelAdmin):
    list_display = ('created', 'status', 'user', 'building', order_amount)
    
    actions = ['complete_payu_payment']
    
    def complete_payu_payment(self, request, queryset):
        updated = 0
        for l in queryset:
            try:
                complete_order(l.id)
            except Exception as e:
                self.message_user(request, 'Operation failed for %s because "%s"' % (str(l), str(e)))
                return
            updated += 1
        self.message_user(request, 'Completed %d payments' % updated)
            
    complete_payu_payment.short_description = '[DEBUG] Complete PAYU payments'
    
class OrderCompleteAdmin(admin.ModelAdmin):
    pass

admin.site.register(Order, OrderAdmin)    
admin.site.register(OrderComplete, OrderCompleteAdmin)    
    
