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
from habitam.entities.models import ApartmentGroup, Apartment, Person, Service

class ApartmentGroupAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'type', 'parent')
    
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'parent', 'owner')
    
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'billed', 'quota_type')
    

admin.site.register(ApartmentGroup, ApartmentGroupAdmin)
admin.site.register(Apartment, ApartmentAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Service, ServiceAdmin)
