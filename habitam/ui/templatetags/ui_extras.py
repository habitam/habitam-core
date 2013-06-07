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
    
Created on Apr 20, 2013

@author: Stefan Guna
'''
from django import template
from habitam.settings import PENALTY_START_DAYS

register = template.Library()

@register.assignment_tag
def capability(entity_cls, user_license, cn):
    m = getattr(entity_cls, cn)
    return m(user_license)

@register.assignment_tag
def operation_amount(account, doc, service):
    if doc == None or doc.total_amount == None:
        return 0
    if doc.src == account and not doc.type == 'collection':
        return doc.total_amount * -1
    return doc.total_amount

@register.assignment_tag
def operation_other_party(account, doc):
    if doc.src == account:
        return doc.billed.name
    return doc.src.name

@register.assignment_tag
def available_list_months(building, user_license):
    return building.available_list_months(user_license.months_back)        

@register.assignment_tag
def list_downloaded(building, month):
    return building.list_downloaded(month) 

@register.simple_tag
def op_amount_class(account, doc, service):
    if doc.type == 'collection' and service != None:
        return ''
    amount = doc.total_amount
    if doc.src == account:
        amount = amount * -1
    if amount < 0:
        return 'negative_balance'
    return 'positive_balance'

@register.simple_tag
def op_class(doc, service):
    if doc.type == 'collection' and service != None:
        return 'collection'
    return ''

@register.filter
def penalty_collect(building):
    return building.payment_due_days + PENALTY_START_DAYS

@register.assignment_tag
def valid_timestamp(timestamp, user_license):
    if timestamp == None or timestamp == '':
        return True
    return user_license.valid_timestamp(timestamp)
    
