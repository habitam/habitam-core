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
from django.views.generic.base import TemplateView
from habitam.entities.models import Apartment, ApartmentGroup, Service, Person, \
    Supplier, CollectingFund
from habitam.financial.models import Account
from habitam.ui import views, billable_views
from habitam.ui.forms.apartment import EditApartmentForm, EditPersonForm, \
    NewApartmentPayment
from habitam.ui.forms.billable_edit_form import EditServiceForm, \
    EditCollectingFundForm
from habitam.ui.forms.building import EditStaircaseForm, EditBuildingForm
from habitam.ui.forms.fund import NewFundTransfer, EditAccountForm
from habitam.ui.forms.service_new_invoice import NewServiceInvoice
from habitam.ui.forms.service_new_payment import NewServicePayment
from habitam.ui.forms.supplier import EditSupplierForm


urlpatterns = patterns('',
    url(r'^users/login/$', 'django.contrib.auth.views.login',
        {'template_name': 'login.html'}, 'login'),
    url(r'^users/logout/$', 'django.contrib.auth.views.logout',
        {'template_name': 'logout.html'}, 'logout'),
    url(r'^users/password/$', 'django.contrib.auth.views.password_change',
        {'template_name': 'password_change.html'}, 'password_change'),
    url(r'^users/password/done$', 'django.contrib.auth.views.password_change_done',
        {'template_name': 'password_change_complete.html'}, 'password_change_done'),
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
    url(r'^users/license_expired/$',
        TemplateView.as_view(template_name='license_expired.html'),
        name='license_expired'),
    
    url(r'^$', views.home, name='home'),
    
    url(r'^buildings/new$', views.new_building, name='new_building'),
                       
    url(r'^buildings$', views.general_list,
        {'license_subtype': 'buildings', 'entity_cls' : ApartmentGroup,
         'title': 'Cladiri disponibile', 'edit_name': 'edit_building',
         'new_name': 'new_building', 'view_name': 'buildings',
         'entity_view_name': 'building_view'},
        name='buildings'),
                       
    url(r'^buildings/(?P<entity_id>\d+)$', views.entity_view,
        {'entity_cls' : ApartmentGroup, 'edit_name': 'edit_building',
         'view_name': 'building_view'},
        name='building_view'),
                       
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
    
    url(r'^buildings/(?P<building_id>\d+)/services$', views.building_tab,
        {'tab': 'service_list'}, name='service_list'),
    
    url(r'^buildings/(?P<building_id>\d+)/all_services$', views.building_tab,
        {'tab': 'service_list', 'show_all': True}, name='all_service_list'),
    
    url(r'^buildings/(?P<building_id>\d+)/services/new$',
        billable_views.new_billable, {'form_class': EditServiceForm},
        name='new_billable_general'),
    
    url(r'^buildings/(?P<building_id>\d+)/funds$', views.building_tab, {'tab': 'fund_list'}, name='fund_list'),

    url(r'^buildings/(?P<building_id>\d+)/funds/new$',
        views.new_building_entity,
        {'form_cls': EditAccountForm, 'target': 'new_fund',
         'title': 'Cont nou', 'commit_directly': True},
        name='new_fund'),
    
    
    url(r'^buildings/(?P<building_id>\d+)/collecting_funds$',
        views.building_tab, {'tab': 'collecting_fund_list'},
        name='collecting_fund_list'),

    url(r'^buildings/(?P<building_id>\d+)/all_collecting_funds$',
        views.building_tab, {'tab': 'collecting_fund_list', 'show_all': True},
        name='all_collecting_fund_list'),

    url(r'^buildings/(?P<building_id>\d+)/collecting_funds/new$',
        billable_views.new_billable, {'form_class': EditCollectingFundForm},
        name='new_billable_collecting'),
                       
    url(r'^collecting_funds/(?P<entity_id>\d+)/edit$',
        billable_views.edit_billable, {'form_class': EditCollectingFundForm},
        name='edit_billable_collecting'),

    url(r'^buildings/(?P<building_id>\d+)/list/(?P<month>\d{4}-\d{2})?$',
        views.download_list, name='download_list'),
    
    url(r'^collecting_funds/(?P<entity_id>\d+)/collection/new$',
        views.new_inbound_operation,
        {'entity_cls': CollectingFund, 'form_cls': NewServiceInvoice,
         'target': 'new_collection', 'title': 'Colectare pentru'},
        name='new_collection'),

    url(r'^services/(?P<entity_id>\d+)/edit$', 
        billable_views.edit_billable, {'form_class': EditServiceForm},
        name='edit_billable_general'),
    
    url(r'^services/(?P<entity_id>\d+)/invoices/new$',
        views.new_inbound_operation,
        {'entity_cls': Service, 'form_cls': NewServiceInvoice,
         'target': 'new_invoice', 'title': 'Factura pentru'},
        name='new_invoice'),
    
    url(r'^apartments/(?P<entity_id>\d+)/edit$', views.edit_entity,
        {'entity_cls': Apartment, 'form_cls': EditApartmentForm,
         'target': 'edit_apartment', 'title': 'Apartamentul'},
        name='edit_apartment'),
    
    url(r'^apartments/(?P<entity_id>\d+)/payments/new$',
        views.new_inbound_operation,
        {'entity_cls': Apartment, 'form_cls': NewApartmentPayment,
         'target': 'new_payment', 'title': 'Incasare de la'},
        name='new_payment'),
    
    url(r'^accounts/(?P<entity_id>\d+)/edit$',
        views.edit_simple_entity,
        {'entity_cls': Account, 'form_cls': EditAccountForm,
         'target': 'edit_fund', 'title': ''},
        name='edit_fund'),
                       
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


    url(r'^suppliers/new$', views.new_simple_entity,
        {'entity_cls': Supplier, 'form_cls': EditSupplierForm,
         'target': 'new_supplier', 'title': 'Furnizor nou'}, 'new_supplier'),
                       
    url(r'^suppliers/(?P<entity_id>\d+)/edit$', views.edit_simple_entity,
        {'entity_cls': Supplier, 'form_cls': EditSupplierForm,
         'target': 'edit_supplier', 'title': 'Editare furnizor'},
        'edit_supplier'),
                       
    url(r'^suppliers$', views.general_list,
        {'license_subtype': 'suppliers', 'entity_cls' : Supplier,
         'title': 'Furnizori disponibili', 'edit_name': 'edit_supplier',
         'new_name' :'new_supplier', 'view_name': 'suppliers',
         'entity_view_name': 'supplier_view', 'alt_view_name': 'all_suppliers'},
        name='suppliers'),

    url(r'^suppliers/all$', views.general_list,
        {'license_subtype': 'suppliers', 'entity_cls' : Supplier,
         'title': 'Furnizori disponibili', 'edit_name': 'edit_supplier',
         'new_name' :'new_supplier', 'view_name': 'all_suppliers',
         'alt_view_name': 'suppliers', 'entity_view_name': 'supplier_view',
         'show_all': True},
        name='all_suppliers'),
                       
    url(r'^suppliers/(?P<entity_id>\d+)$', views.entity_view,
        {'entity_cls' : Supplier, 'edit_name': 'edit_supplier',
         'view_name': 'supplier_view'},
        name='supplier_view'),
)
