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
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from habitam.licensing.models import Administrator, License

class AdministratorInline(admin.StackedInline):
    model = Administrator
    can_delete = False
    verbose_name_plural = 'administratori'

class UserAdmin(UserAdmin):
    inlines = (AdministratorInline, )

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(License)