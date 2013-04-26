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
from habitam.services.models import Quota, OperationDoc, Operation, Account

class QuotaAdmin(admin.ModelAdmin):
    list_display = ('src', 'dest', 'ratio')

class OperationDocAdmin(admin.ModelAdmin):
    list_display = ('date', 'no', 'src', 'billed', 'type')

class OperationAdmin(admin.ModelAdmin):
    list_display = ('doc', 'dest', 'amount')

class AccountAdmin(admin.ModelAdmin):
    list_display = ('holder',)

admin.site.register(Quota, QuotaAdmin)
admin.site.register(OperationDoc, OperationDocAdmin)
admin.site.register(Operation, OperationAdmin)
admin.site.register(Account, AccountAdmin)
