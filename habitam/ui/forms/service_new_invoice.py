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
from habitam.ui.forms.generic import NewDocPaymentForm, INVOICE_FIELDS
import logging


logger = logging.getLogger(__name__)


def _drop_undeclared_checkboxes(cleaned_data):    
    for k in cleaned_data.keys():
        if not k.startswith('consumption_undeclared_ap_'):
            continue
        del cleaned_data[k]
 
def _process_undeclared(cleaned_data):
    to_drop = [] 
    for k, v in cleaned_data.iteritems():
        if not k.startswith('consumption_undeclared_ap_') or not v:
            continue
        to_drop.append(int(k[len('consumption_undeclared_ap_'):])) 
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


class NewServiceInvoice(NewDocPaymentForm):
    series = INVOICE_FIELDS['series']
    reference = INVOICE_FIELDS['reference']
    fiscal_id = INVOICE_FIELDS['fiscal_id']
    registration_id = INVOICE_FIELDS['registration_id']
    manual_costs = BooleanField(label='Distribuie costurile manual', required=False)
    cmd = forms.CharField(initial='save', widget=forms.HiddenInput())
    
    def __init__(self, *args, **kwargs):
        self.service = kwargs['entity']
 
        super(NewServiceInvoice, self).__init__(*args, **kwargs)
        
        if self.__manual_costs():
            self.fields['amount'] = forms.DecimalField(label='Suma',
                                                    widget=forms.HiddenInput())
        if self.service.quota_type == 'consumption':
            self.fields['consumption'] = forms.DecimalField(label='Cantitate')
                               
        if self.__manual_costs() or self.service.quota_type == 'consumption':
            self.consumption_ids = []
            self.__add_apartments(args)
            
        self.fields['fiscal_id'].initial = self.service.supplier.fiscal_id
        self.fields['registration_id'].initial = self.service.supplier.registration_id
        
    
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
        return 'manual_costs' in self.data or self.service.quota_type == 'no_quota'
    
    def __mark_unrequired(self):
        for k in self.data:
            if not k.startswith('consumption_undeclared_ap_'):
                continue
            ap = k[len('consumption_undeclared_ap_'):]
            self.fields['consumption_ap_' + ap].required = False
                
    def clean_apartments(self, cleaned_data, label):
        all_data = {}
        all_sum = 0
        for k, v in cleaned_data.items():
            if not k.startswith(label):
                continue
            all_data[int(k[len(label):])] = v
            if not v:
                continue
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
            _process_undeclared(cleaned_data)
        if 'manual_costs' in cleaned_data:
            del cleaned_data['manual_costs']
        _drop_undeclared_checkboxes(cleaned_data)
        
        invoice = {}
        for fn in INVOICE_FIELDS:
            invoice[fn] = cleaned_data[fn]
            del cleaned_data[fn]
        cleaned_data['invoice'] = invoice
            
        return cleaned_data    
    
    def spinners(self):
        return super(NewServiceInvoice, self).spinners()
    
    def refresh_ids(self):
        return ['id_manual_costs']
