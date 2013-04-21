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
    
Created on Apr 12, 2013

@author: Stefan Guna
'''
from django.conf.urls import patterns, url
from habitam.entities.models import Apartment, ApartmentGroup, Service
from habitam.ui import views, service_views, fund_views
from habitam.ui.apartment_views import EditApartmentForm
from habitam.ui.building_views import EditStaircaseForm
from habitam.ui.service_views import EditServiceForm
from habitam.ui.views import NewPaymentForm, NewDocPaymentForm


urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
    
    url(r'^buildings/new$', views.new_building, name='new_building'),
    
    url(r'^buildings/(?P<building_id>\d+)/apartments$', views.building_tab, {'tab': 'apartment_list'}, name='apartment_list'),
    
    url(r'^buildings/(?P<building_id>\d+)/apartments/new$',
        views.new_building_entity,
        {'form_cls': EditApartmentForm, 'target': 'new_apartment',
         'title': 'Apartament nou'},
        name='new_apartment'),
                       
    url(r'^buildings/(?P<building_id>\d+)/staircases/new$',
        views.new_building_entity,
        {'form_cls': EditStaircaseForm, 'target': 'new_staircase',
         'title': 'Scara noua', 'save_kwargs': {'type': 'stair'}},
        name='new_staircase'),

    url(r'^staircases/(?P<entity_id>\d+)/edit$', views.edit_entity,
       {'entity_cls': ApartmentGroup, 'form_cls': EditStaircaseForm,
        'target': 'edit_staircase', 'title': 'Scara'}, name='edit_staircase'),
    
    url(r'^buildings/(?P<building_id>\d+)/services$', views.building_tab, {'tab': 'service_list'}, name='service_list'),
    
    url(r'^buildings/(?P<building_id>\d+)/services/new$',
        views.new_building_entity,
        {'form_cls': EditServiceForm, 'target': 'new_service', 
         'title': 'Serviciu nou'},
        name='new_service'),
    
    url(r'^buildings/(?P<building_id>\d+)/funds$', views.building_tab, {'tab': 'fund_list'}, name='fund_list'),
    
    url(r'^services/(?P<entity_id>\d+)/edit$', views.edit_entity, 
        {'entity_cls': Service, 'form_cls': EditServiceForm,
         'target': 'edit_service', 'title': 'Serviciul'},
        name='edit_service'),
    
    url(r'^services/(?P<entity_id>\d+)/invoices/new$',
        views.new_inbound_operation, 
        {'entity_cls': Service, 'form_cls': NewDocPaymentForm,
         'target': 'new_invoice', 'title': 'Factura pentru'},
        name='new_invoice'),
    
    url(r'^apartments/(?P<entity_id>\d+)/edit$', views.edit_entity,
        {'entity_cls': Apartment, 'form_cls': EditApartmentForm,
         'target': 'edit_apartment', 'title': 'Apartamentul'},
        name='edit_apartment'),
    
    url(r'^apartments/(?P<entity_id>\d+)/payments/new$',
        views.new_inbound_operation,
        {'entity_cls': Apartment, 'form_cls': NewPaymentForm,
         'target': 'new_payment', 'title': 'Incasare de la'},
        name='new_payment'),
    
    url(r'^accounts/(?P<account_id>\d+)/operations$', views.operation_list, name='operation_list'),
    url(r'^accounts/(?P<account_id>\d+)/operations/(?P<operationdoc_id>\d+)$', views.operation_doc, name='operation_doc'),
    url(r'^accounts/(?P<account_id>\d+)/operations/new_service_payment$', service_views.new_service_payment, name='new_service_payment'),
    url(r'^accounts/(?P<account_id>\d+)/operations/new_transfer$', fund_views.new_fund_transfer, name='new_fund_transfer'),
)
