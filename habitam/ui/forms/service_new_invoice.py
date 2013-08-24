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
    
Created on July 6, 2013

@author: Stefan Guna
'''
from decimal import Decimal
from django import forms
from django.forms.fields import DecimalField, BooleanField
from habitam.ui.forms.generic import NewDocPaymentForm, NewInvoice
from habitam.ui.forms.helper.all_apartments import skip_apartments, \
    aggregate_apartments, drop_skip_checkboxes
import logging


logger = logging.getLogger(__name__)



 
def _process_undeclared(cleaned_data):
    to_drop = skip_apartments('consumption_undeclared_ap_', cleaned_data)
    if not to_drop or not cleaned_data['ap_consumptions'] or not cleaned_data['consumption']:
        return
    for pk in to_drop:
        if pk in cleaned_data['ap_consumptions']:
            del cleaned_data['ap_consumptions'][pk]
    declared = sum(cleaned_data['ap_consumptions'].values())
    share = (Decimal(cleaned_data['consumption']) - declared) / len(to_drop)
    for pk in to_drop:
        cleaned_data['ap_consumptions'][pk] = share
   
 
def _required(args, ap):
    label = 'consumption_undeclared_ap_' + str(ap.pk)
    return not (args and label in args[0])


class NewBuildingCharge(NewDocPaymentForm):
    cmd = forms.CharField(initial='save', widget=forms.HiddenInput())
    
    def __init__(self, *args, **kwargs):
        self.service = kwargs['entity']
 
        super(NewBuildingCharge, self).__init__(*args, **kwargs)
        
        if self.service.quota_type != 'noquota':
            self.fields['manual_costs'] = BooleanField(
                                    label='Distribuie costurile manual',
                                    required=False)
        
        if self.__manual_costs():
            self.fields['amount'] = forms.DecimalField(label='Suma',
                                                    widget=forms.HiddenInput())
        if self.service.quota_type == 'consumption':
            self.fields['consumption'] = forms.DecimalField(label='Cantitate')
                               
        if self.__manual_costs() or self.service.quota_type == 'consumption':
            self.consumption_ids = []
            self.__add_apartments(args)
        
    
    def __add_apartments(self, args):
        aps = self.service.billed.apartments()
        for ap in aps:
            if self.__manual_costs():
                self.fields['sum_ap_' + str(ap.pk)] = \
                    DecimalField(label='Suma ' + str(ap))
            if self.service.quota_type == 'consumption':
                self.fields['consumption_undeclared_ap_' + str(ap.pk)] = \
                    BooleanField(label='Consum nedeclarat',
                                 required=False)
                self.fields['consumption_ap_' + str(ap.pk)] = \
                    DecimalField(label='Consum ' + str(ap),
                                 required=_required(args, ap))
                
                self.consumption_ids.append(ap.pk)
 
    
    def __manual_costs(self):
        return 'manual_costs' in self.data or self.service.quota_type == 'noquota'
    
    def __mark_unrequired(self):
        for k in self.data:
            if not k.startswith('consumption_undeclared_ap_'):
                continue
            ap = k[len('consumption_undeclared_ap_'):]
            self.fields['consumption_ap_' + ap].required = False
    
    def clean(self):
        cleaned_data = super(NewBuildingCharge, self).clean()
        if self.__manual_costs():
            cleaned_data['amount'], cleaned_data['ap_sums'] = \
                aggregate_apartments('sum_ap_', cleaned_data)
        if self.service.quota_type == 'consumption': 
            dummy, cleaned_data['ap_consumptions'] = \
                aggregate_apartments('consumption_ap_', cleaned_data)
            _process_undeclared(cleaned_data)
        if 'manual_costs' in cleaned_data:
            del cleaned_data['manual_costs']
        drop_skip_checkboxes('consumption_undeclared_ap_', cleaned_data)
            
        return cleaned_data    
    
    def spinners(self):
        return super(NewBuildingCharge, self).spinners()
    
    def refresh_ids(self):
        return ['id_manual_costs']


class NewServiceInvoice(NewInvoice, NewBuildingCharge):
    def __init__(self, *args, **kwargs):
        super(NewServiceInvoice, self).__init__(*args, **kwargs)   
        self.fields['no'].label = 'Număr factură'     
        del self.fields['invoice_no']
        self.fields['invoice_fiscal_id'].initial = self.service.supplier.fiscal_id
        self.fields['invoice_registration_id'].initial = self.service.supplier.registration_id
        
