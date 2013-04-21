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
from habitam.ui import views, service_views, apartment_views, fund_views


urlpatterns = patterns('',
    
    url(r'^buildings$', views.building_list, name='building_list'),
    
    url(r'^buildings/new$', views.new_building, name='new_building'),
    url(r'^buildings/(?P<building_id>\d+)/apartments$', views.building_tab, {'tab': 'apartment_list'}, name='apartment_list'),
    url(r'^buildings/(?P<building_id>\d+)/apartments/(?P<apartment_id>\d+)/edit$', apartment_views.edit_apartment, name='edit_apartment'),
    url(r'^buildings/(?P<building_id>\d+)/services$', views.building_tab, {'tab': 'service_list'}, name='service_list'),
    url(r'^buildings/(?P<building_id>\d+)/services/new$', service_views.new_service, name='new_service'),
    url(r'^buildings/(?P<building_id>\d+)/funds$', views.building_tab, {'tab': 'fund_list'}, name='fund_list'),
    
    url(r'^services/(?P<service_id>\d+)/edit$', service_views.edit_service, name='edit_service'),
    url(r'^services/(?P<service_id>\d+)/invoices/new$', service_views.new_invoice, name='new_invoice'),
    
    url(r'^apartments/(?P<apartment_id>\d+)/payments/new$', apartment_views.new_payment, name='new_payment'),
    
    url(r'^accounts/(?P<account_id>\d+)/operations$', views.operation_list, name='operation_list'),
    url(r'^accounts/(?P<account_id>\d+)/operations/(?P<operationdoc_id>\d+)$', views.operation_doc, name='operation_doc'),
    url(r'^accounts/(?P<account_id>\d+)/operations/new_service_payment$', service_views.new_service_payment, name='new_service_payment'),
    url(r'^accounts/(?P<account_id>\d+)/operations/new_transfer$',fund_views.new_fund_transfer, name='new_fund_transfer'),
)
