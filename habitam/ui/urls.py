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
from habitam.entities.models import Apartment, ApartmentGroup, Service, Person
from habitam.ui import views, service_views
from habitam.ui.forms.apartment import EditApartmentForm, EditPersonForm
from habitam.ui.forms.building import EditStaircaseForm, EditBuildingForm
from habitam.ui.forms.fund import NewFundTransfer
from habitam.ui.forms.generic import NewDocPaymentForm, NewPaymentForm
from habitam.ui.forms.service import EditServiceForm, NewServicePayment


urlpatterns = patterns('',
    url(r'^users/login/$', 'django.contrib.auth.views.login',
        {'template_name': 'login.html'}, 'login'),
    url(r'^users/logout/$', 'django.contrib.auth.views.logout',
        {'template_name': 'logout.html'}, 'logout'),
    url(r'^users/reset/$', 'django.contrib.auth.views.password_reset', 
        {'template_name': 'password_reset.html',
         'email_template_name': 'password_reset_email.txt',
         'subject_template_name': 'password_reset_subject.txt'},
        name='password_reset'),
    url(r'^users/reset/done/$', 'django.contrib.auth.views.password_reset_done',
        {'template_name': 'password_reset_done.html'},
        name='password_reset_done'),
    url(r'^users/reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        'django.contrib.auth.views.password_reset_confirm', 
        {'template_name': 'password_reset_confirm.html'},
        name='password_reset_confirm'),
    url(r'^users/reset/complete/$',
        'django.contrib.auth.views.password_reset_complete',
        {'template_name': 'password_reset_complete.html'},
        name='password_reset_complete'),
    
    url(r'^$', views.home, name='home'),
    
    url(r'^buildings/new$', views.new_building, name='new_building'),
    
    url(r'^buildings/(?P<building_id>\d+)/apartments$', views.building_tab, {'tab': 'apartment_list'}, name='apartment_list'),
    
    url(r'^buildings/(?P<building_id>\d+)/apartments/new$',
        views.new_building_entity,
        {'form_cls': EditApartmentForm, 'target': 'new_apartment',
         'title': 'Apartament nou'},
        name='new_apartment'),
                       
    url(r'^buildings/(?P<entity_id>\d+)/edit$', views.edit_simple_entity,
        {'entity_cls': ApartmentGroup, 'form_cls': EditBuildingForm,
         'target': 'edit_building', 'title': ''}, name='edit_building'),

    url(r'^buildings/(?P<building_id>\d+)/staircases/new$',
        views.new_building_entity,
        {'form_cls': EditStaircaseForm, 'target': 'new_staircase',
         'title': 'Scara noua', 'save_kwargs': {'type': 'stair'}},
        name='new_staircase'),

    url(r'^staircases/(?P<entity_id>\d+)/edit$', views.edit_entity,
       {'entity_cls': ApartmentGroup, 'form_cls': EditStaircaseForm,
        'target': 'edit_staircase', 'title': 'Scara'}, name='edit_staircase'),
    
    url(r'^buildings/(?P<building_id>\d+)/accounts/(?P<account_id>\d+)/operations/(?P<month>\d{4}-\d{2})?$',
        views.operation_list, name='operation_list'),
    
    url(r'^buildings/(?P<building_id>\d+)/accounts/(?P<account_id>\d+)/operations/(?P<operationdoc_id>\d+)$',
        views.operation_doc, name='operation_doc'),
    
    url(r'^buildings/(?P<building_id>\d+)/services$', views.building_tab, {'tab': 'service_list'}, name='service_list'),
    
    url(r'^buildings/(?P<building_id>\d+)/services/new$',
        service_views.new_service, name='new_service'),
    
    url(r'^buildings/(?P<building_id>\d+)/funds$', views.building_tab, {'tab': 'fund_list'}, name='fund_list'),
    
    url(r'^services/(?P<entity_id>\d+)/edit$', service_views.edit_service, 
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
    
    url(r'^accounts/(?P<account_id>\d+)/operations/pay_service$',
        views.new_transfer,
        {'form_cls': NewServicePayment, 'form_dest_key': 'service',
         'target': 'new_service_payment', 'title': 'Plateste de la'},
        name='new_service_payment'),
    
    url(r'^accounts/(?P<account_id>\d+)/operations/transfer$',
        views.new_transfer,
        {'form_cls': NewFundTransfer, 'form_dest_key': 'dest_link',
         'target': 'new_fund_transfer', 'title': 'Transfer de la'},
        name='new_fund_transfer'),
                       
    url(r'^owners/(?P<entity_id>\d+)/edit$', views.edit_simple_entity,
        {'entity_cls': Person, 'form_cls': EditPersonForm,
         'target': 'edit_owner', 'title': ''}, name='edit_owner'),
)
