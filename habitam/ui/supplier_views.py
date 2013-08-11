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
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import decorator_from_middleware
from habitam.entities.bootstrap_suppliers import create_suppliers
from habitam.entities.models import Supplier
from habitam.ui.forms.supplier import SelectSuppliersForm
from habitam.ui.license_filter import LicenseFilter
import logging

logger = logging.getLogger(__name__)

@login_required
@decorator_from_middleware(LicenseFilter)
def select_std_suppliers(request):
    ul = request.user.administrator.license
    existing_suppliers = ul.available_suppliers()
    
    if request.method == 'POST':
        form = SelectSuppliersForm(existing_suppliers, request.POST)
        if form.is_valid():
            try:
                supplier_keys = form.cleaned_data['suppliers']
                suppliers = create_suppliers(supplier_keys)
                for supplier in suppliers:
                    ul.add_entity(supplier, Supplier)
                return render(request, 'edit_ok.html')
            # TODO @iia catch by different exceptions
            except Exception as e:
                logger.exception('Cannot save selected suppliers')
                form.add_form_error(e)
    else:
        form = SelectSuppliersForm(existing_suppliers)
        
    data = {'form': form, 'target': 'select_std_suppliers', 'title': 'Furnizori predefiniți'}
    return render(request, 'edit_dialog.html', data)
