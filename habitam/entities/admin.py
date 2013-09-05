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
    
Created on Apr 13, 2013

@author: Stefan Guna
'''

from django.contrib import admin
from habitam.entities.models import ApartmentGroup, Apartment, Person, Service, \
    ServiceConsumption, ApartmentConsumption, DisplayDate, Supplier, CollectingFund

class ApartmentGroupAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'type', 'parent')
    
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'parent', 'owner', 'no_penalties_since')
    
class ApartmentConsumptionAdmin(admin.ModelAdmin):
    list_display = ('apartment', 'doc', 'consumed')
    
class BillableAdmin(admin.ModelAdmin):
    actions = ['set_quota']
    
    def set_quota(self, request, queryset):
        updated = 0
        for b in queryset:
            try:
                b.set_quota()
            except Exception as e:
                self.message_user(request, 'Operation failed for %s because "%s"' % (str(b), str(e)))
                return
            updated += 1
        self.message_user(request, 'Set the quota for %d entities' % updated)
            
    set_quota.short_description = 'Reset the quota for this entity'
        

class CollectingFundAdmin(BillableAdmin):
    list_display = ('name', 'billed', 'quota_type', 'archived', 'archive_date')
    
class DisplayDateAdmin(admin.ModelAdmin):
    list_display = ('building', 'month', 'timestamp')
     
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')

class ServiceAdmin(BillableAdmin):
    list_display = ('name', 'supplier', 'billed', 'quota_type', 'archived',
                    'archive_date', 'contract_id', 'client_id')
    
class ServiceConsumptionAdmin(admin.ModelAdmin):
    list_display = ('service', 'doc', 'consumed')
    
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'archived', 'archive_date', 'one_time', 'county',
                    'fiscal_id', 'registration_id')

admin.site.register(ApartmentGroup, ApartmentGroupAdmin)
admin.site.register(Apartment, ApartmentAdmin)
admin.site.register(ApartmentConsumption, ApartmentConsumptionAdmin)
admin.site.register(CollectingFund, CollectingFundAdmin)
admin.site.register(DisplayDate, DisplayDateAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(ServiceConsumption, ServiceConsumptionAdmin)
admin.site.register(Supplier, SupplierAdmin)
