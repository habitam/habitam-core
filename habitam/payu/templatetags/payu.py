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
from django import template
from habitam.payu.payu import payform

FIELD_FORMAT = '<input name="%s" value="%s" type="hidden"/>'

register = template.Library()

def __form_fields(order):
    return ''.join(map(lambda (k, v): FIELD_FORMAT % (k, v), order))

@register.simple_tag
def payu_payment_fields(building, user): 
    return __form_fields(payform(building, user))
