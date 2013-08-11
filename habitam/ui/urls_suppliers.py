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
    
Created on Aug 11, 2013

@author: Stefan Guna
'''
from django.conf.urls import patterns, url
from habitam.entities.models import Supplier
from habitam.ui import views, supplier_views
from habitam.ui.forms.supplier import EditSupplierForm

urlpatterns = patterns('',
    url(r'^suppliers/new$', views.new_simple_entity,
        {'entity_cls': Supplier, 'form_cls': EditSupplierForm,
         'target': 'new_supplier', 'title': 'Furnizor nou'}, 'new_supplier'),
    
    url(r'^suppliers/select_std_suppliers$',
        supplier_views.select_std_suppliers, name='select_std_suppliers'),
                       
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
