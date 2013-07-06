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
from django import forms
from django.forms.fields import DecimalField
from habitam.ui.forms.generic import NewDocPaymentForm
import logging


logger = logging.getLogger(__name__)


class NewServiceInvoice(NewDocPaymentForm):
    manual_costs = forms.BooleanField(label='Distribuie costurile manual', required=False)
   
    def __init__(self, *args, **kwargs):
        self.service = kwargs['entity']
        super(NewServiceInvoice, self).__init__(*args, **kwargs)
       
         
        if self.__manual_costs():
            self.fields['amount'] = forms.DecimalField(label='Suma',
                                                    widget=forms.HiddenInput())
            self.__add_apartments('Suma ', 'sum_ap_')
        
        if self.service.quota_type == 'consumption':
            self.fields['consumption'] = forms.DecimalField(label='Cantitate')
            self.__add_apartments('Cantitate pentru ', 'consumption_ap_')
    
    def __add_apartments(self, label, var_name):
        aps = self.service.billed.apartments()
        for ap in aps:
            self.fields[var_name + str(ap.pk)] = \
                DecimalField(label=label + str(ap))
    
    def __manual_costs(self):
        return 'manual_costs' in self.data or self.service.quota_type == 'no_quota'
                
    def clean_apartments(self, cleaned_data, label):
        all_data = {}
        all_sum = 0
        for k, v in cleaned_data.items():
            if not k.startswith(label):
                continue
            all_data[int(k[len(label):])] = v
            all_sum = all_sum + v
            
        for k in all_data.keys():
            del cleaned_data[label + str(k)]
        
        if all_sum == 0 or len(all_data) == 0:
            return None, None 
        return all_sum, all_data
    
    def clean(self):
        cleaned_data = super(NewServiceInvoice, self).clean()
        if self.__manual_costs():
            cleaned_data['amount'], cleaned_data['ap_sums'] = \
                self.clean_apartments(cleaned_data, 'sum_ap_')
        if self.service.quota_type == 'consumption': 
            dummy, cleaned_data['ap_consumptions'] = \
                self.clean_apartments(cleaned_data, 'consumption_ap_')
        if 'manual_costs' in cleaned_data:
            del cleaned_data['manual_costs']
        return cleaned_data    
    
    def spinners(self):
        return super(NewServiceInvoice, self).spinners()
    
    def refresh_ids(self):
        return ['id_manual_costs']