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
from habitam.entities.bootstrap_suppliers import remaining_suppliers
from habitam.entities.models import Apartment
from habitam.licensing.models import License
from habitam.payu import payu
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
def available_list_months(building):
    l = License.for_building(building)
    return building.available_list_months(l.months_back)        

@register.filter
def class_name(ob):
    return ob.__class__.__name__

@register.simple_tag
def field_class(field):
    css_class = ''
    if field.name.startswith('consumption_undeclared_ap_'):
        css_class = css_class + 'stick-to-next '
    return css_class

@register.assignment_tag
def license_allowed(admin_license, building):
    return admin_license == License.for_building(building)

@register.assignment_tag
def license_for_building(building):
    return License.for_building(building)

@register.assignment_tag
def list_downloaded(building, month):
    return building.list_downloaded(month) 

@register.simple_tag
def op_amount_class(account, doc, service):
    if doc.type == 'collection' and service != None:
        return ''
    amount = doc.total_amount
    if amount == None:
        return 'positive_balance'
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

@register.assignment_tag
def owner_apartments(email):
    return Apartment.by_owner(email)

@register.assignment_tag
def owner_debt(building, email):
    return building.owner_debt(email)

@register.assignment_tag
def pending_payments(building, user):
    return payu.pending_payments(building, user)

@register.filter
def penalty_collect(building):
    return building.payment_due_days + PENALTY_START_DAYS

@register.assignment_tag
def services_without_invoice(building, month):
    return building.services_without_invoice(month)

@register.filter
def remaining_std_suppliers(l):
    try:
        return remaining_suppliers(l.available_suppliers())
    except:
        return None

@register.assignment_tag
def top_entities(q, count):
    return q[:count]

@register.filter
def unique_buildings(apartments):
    buildings = []
    for ap in apartments:
        if not ap.building().pk in map(lambda b: b.pk, buildings):
            buildings.append(ap.building())
    return buildings

@register.assignment_tag
def valid_timestamp(timestamp, user_license):
    if timestamp == None or timestamp == '':
        return True
    return user_license.valid_timestamp(timestamp)
    
