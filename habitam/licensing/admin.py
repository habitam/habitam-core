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
from habitam.payu.setup import set_payu_payments

class AdministratorInline(admin.StackedInline):
    model = Administrator
    can_delete = False
    verbose_name_plural = 'administratori'

class UserAdmin(UserAdmin):
    inlines = (AdministratorInline,)
    
class LicenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'users', 'valid_until', 'apartment_count',
                    'max_apartments', 'months_back', 'payu_merchant_id',
                    'payu_merchant_key')
    fieldsets = (
                    ('License', {
                        'fields': ('valid_until', 'max_apartments', 'months_back')
                    }),
                    ('PAYU', {
                        'fields': ('payu_merchant_id', 'payu_merchant_key')
                    }),
                 )
    
    actions = ['set_payu_payments']
    
    def set_payu_payments(self, request, queryset):
        updated = 0
        for l in queryset:
            try:
                set_payu_payments(l)
            except Exception as e:
                self.message_user(request, 'Operation failed for %s because "%s"' % (str(l), str(e)))
                return
            updated += 1
        self.message_user(request, 'Set PAYU payments for %d licenses' % updated)
            
    set_payu_payments.short_description = 'Set PAYU payments for this license'
    
 
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(License, LicenseAdmin)
