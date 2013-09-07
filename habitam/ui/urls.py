# -*- coding: utf-8 -*-
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
from habitam.downloads import register, balance
from habitam.entities.models import Apartment, ApartmentGroup, Service, Person, \
    CollectingFund
from habitam.financial.models import Account
from habitam.ui import views, billable_views, urls_user, urls_suppliers
from habitam.ui.forms.apartment import EditApartmentForm, EditPersonForm, \
    NewApartmentPayment
from habitam.ui.forms.billable_edit_form import EditServiceForm, \
    EditCollectingFundForm
from habitam.ui.forms.building import EditStaircaseForm, EditBuildingForm, \
    InitialOperations
from habitam.ui.forms.contact import ContactForm
from habitam.ui.forms.fund import NewFundTransfer, EditAccountForm
from habitam.ui.forms.service_new_invoice import NewServiceInvoice, \
    NewBuildingCharge
from habitam.ui.forms.service_new_payment import NewServicePayment, \
    NewOtherServicePayment
from habitam.ui.views import form_view


urlpatterns = patterns('habitam.ui.urls_user',
    url(r'^contact/$', form_view,
        {'view_name':'contact', 'form_class':ContactForm,
         'template_name':'contact.html', 'success_view':'contact_thanks'},
        'contact'),
    url(r'^contact_thanks/$',
        TemplateView.as_view(template_name='contact_thanks.html'),
        name='contact_thanks'),
    
    url(r'^$', views.home, name='home'),
    
    url(r'^buildings/new$', views.new_building, name='new_building'),
                       
    url(r'^buildings$', views.general_list,
        {'license_subtype': 'buildings', 'entity_cls' : ApartmentGroup,
         'title': u'Clădiri disponibile', 'edit_name': 'edit_building',
         'new_name': 'new_building', 'view_name': 'buildings',
         'entity_view_name': 'apartment_list'},
        name='buildings'),
                       
    url(r'^buildings/(?P<entity_id>\d+)$', views.entity_view,
        {'entity_cls' : ApartmentGroup, 'edit_name': 'edit_building',
         'view_name': 'building_view', 'template_name': 'building_about.html',
         'template_entity': 'building',
         'extra_data': {'active_tab': 'building_view'}},
        name='building_view'),
                       
    url(r'^buildings/(?P<building_id>\d+)/apartments$', views.building_tab, {'tab': 'apartment_list'}, name='apartment_list'),
    
    url(r'^buildings/(?P<building_id>\d+)/apartments/new$',
        views.new_building_entity,
        {'form_cls': EditApartmentForm, 'target': 'new_apartment',
         'title': 'Apartament nou'},
        name='new_apartment'),
                       
    url(r'^buildings/(?P<building_id>\d+)/initial_operations_template$',
        views.download_initial_operations_template,
        name='initial_operations_template'),
                       
    url(r'^buildings/(?P<entity_id>\d+)/edit$', views.edit_simple_entity,
        {'entity_cls': ApartmentGroup, 'form_cls': EditBuildingForm,
         'target': 'edit_building', 'title': ''}, name='edit_building'),
                       
    url(r'^buildings/(?P<building_id>\d+)/initial_operations$',
        views.new_building_entity,
        {'form_cls': InitialOperations, 'target': 'initial_operations',
         'title': u'Solduri inițiale', 'commit_directly': True},
        'initial_operations'),

    url(r'^buildings/(?P<building_id>\d+)/staircases/new$',
        views.new_building_entity,
        {'form_cls': EditStaircaseForm, 'target': 'new_staircase',
         'title': u'Scară nouă', 'save_kwargs': {'type': 'stair'}},
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

    url(r'^buildings/(?P<building_id>\d+)/balance/(?P<month>\d{4}-\d{2})?$',
        views.download_report,
        {'name': 'solduri', 'generator': balance.download_balance},
        name='download_balance'),

    url(r'^buildings/(?P<building_id>\d+)/list/(?P<month>\d{4}-\d{2})?$',
        views.download_list, name='download_list'),

    url(r'^buildings/(?P<building_id>\d+)/register/bank/(?P<month>\d{4}-\d{2})?$',
        views.download_report,
        {'name': 'registru_banca_', 'generator': register.download_bank_register},
        name='download_bank_register'),

    url(r'^buildings/(?P<building_id>\d+)/register/cash/(?P<month>\d{4}-\d{2})?$',
        views.download_report,
        {'name': 'registru_casa_', 'generator': register.download_cash_register},
        name='download_cash_register'),

    url(r'^buildings/(?P<building_id>\d+)/upload_initial_operations$',
        views.upload_initial_operations, name='upload_initial_operations'),
                           
    url(r'^collecting_funds/(?P<entity_id>\d+)/collection/new$',
        views.new_inbound_operation,
        {'entity_cls': CollectingFund, 'form_cls': NewBuildingCharge,
         'target': 'new_collection', 'title': 'Colectare pentru'},
        name='new_collection'),

    url(r'^services/(?P<entity_id>\d+)/edit$',
        billable_views.edit_billable, {'form_class': EditServiceForm},
        name='edit_billable_general'),
    
    url(r'^services/(?P<entity_id>\d+)/invoices/new$',
        views.new_inbound_operation,
        {'entity_cls': Service, 'form_cls': NewServiceInvoice,
         'target': 'new_invoice', 'title': u'Factură pentru'},
        name='new_invoice'),
    
    url(r'^apartments/(?P<entity_id>\d+)/edit$', views.edit_entity,
        {'entity_cls': Apartment, 'form_cls': EditApartmentForm,
         'target': 'edit_apartment', 'title': 'Apartamentul'},
        name='edit_apartment'),
    
    url(r'^apartments/(?P<entity_id>\d+)/payments/new$',
        views.new_inbound_operation,
        {'entity_cls': Apartment, 'form_cls': NewApartmentPayment,
         'target': 'new_payment', 'title': u'Încasare de la'},
        name='new_payment'),
    
    url(r'^accounts/(?P<entity_id>\d+)/edit$',
        views.edit_simple_entity,
        {'entity_cls': Account, 'form_cls': EditAccountForm,
         'target': 'edit_fund', 'title': ''},
        name='edit_fund'),
                       
    url(r'^accounts/(?P<account_id>\d+)/operations/pay_service$',
        views.new_transfer,
        {'form_cls': NewServicePayment, 'target': 'new_service_payment',
         'title': u'Plătește de la'},
        name='new_service_payment'),

    url(r'^accounts/(?P<account_id>\d+)/operations/pay_other_service$',
        views.new_transfer,
        {'form_cls': NewOtherServicePayment,
         'target': 'new_other_service_payment',
         'title': u'Plătește terț de la'},
        name='new_other_service_payment'),
    
    url(r'^accounts/(?P<account_id>\d+)/operations/transfer$',
        views.new_transfer,
        {'form_cls': NewFundTransfer, 'target': 'new_fund_transfer',
         'title': 'Transfer de la'},
        name='new_fund_transfer'),
                       
    url(r'^owners/(?P<entity_id>\d+)/edit$', views.edit_simple_entity,
        {'entity_cls': Person, 'form_cls': EditPersonForm,
         'target': 'edit_owner', 'title': ''}, name='edit_owner'),
)


urlpatterns += urls_user.urlpatterns
urlpatterns += urls_suppliers.urlpatterns

