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
    
Created on Apr 21, 2013

@author: Stefan Guna
'''
from django import forms
from django.forms.forms import NON_FIELD_ERRORS
from django.forms.util import ErrorDict
from habitam.ui.widgets.bootstrap_date import BootstrapDateInput
import datetime

INVOICE_FIELDS = [
    'fiscal_id',
    'no',
    'series',
    'reference',
    'registration_id',
]

RECEIPT_FIELDS = [
    'no',
    'description',
    'fiscal_id',
    'registration_id',
    'payer_name',
    'payer_address',
]
   
class NewDocPaymentForm(forms.Form):
    amount = forms.DecimalField(label='Suma')
    date = forms.DateField(label='Data', initial=datetime.date.today,
                        widget=BootstrapDateInput(input_format='yyyy-mm-dd'))
    no = forms.CharField(label='Număr document')
    
    def __init__(self, *args, **kwargs):
        if 'entity' in kwargs.keys():
            del kwargs['entity']
        super(NewDocPaymentForm, self).__init__(*args, **kwargs)
        
    def spinners(self):
        return ['amount'] 

    def add_form_error(self, error_message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(error_message)


class NewInvoice(NewDocPaymentForm):
    invoice_series = forms.CharField(label='Serie factură', max_length=30, required=False)
    invoice_no = forms.CharField(label='Număr factură')
    invoice_reference = forms.CharField(label='Referință factură', max_length=30, required=False)
    invoice_fiscal_id = forms.CharField(label='Nr. înreg. fiscală furnizor', max_length=30, required=False)
    invoice_registration_id = forms.CharField(label='Nr. reg. com. furnizor', max_length=30, required=False)

    def clean(self):
        cleaned_data = super(NewInvoice, self).clean()
        
        invoice = {}
        for fn in INVOICE_FIELDS:
            label = 'invoice_' + fn
            if not label in cleaned_data:
                continue
            invoice[fn] = cleaned_data[label]
            del cleaned_data[label]
        if 'no' in cleaned_data and not 'no' in invoice:
            invoice['no'] = cleaned_data['no']
        cleaned_data['invoice'] = invoice
        return cleaned_data


class NewReceipt(NewDocPaymentForm):
    no = forms.CharField(label='Număr chitanță')
    receipt_description = forms.CharField(label='Descriere chitanță', max_length=200, required=False)
    receipt_fiscal_id = forms.CharField(label='Nr. înreg. fiscală plătitor', max_length=30, required=False)
    receipt_registration_id = forms.CharField(label='Nr. reg. com. plătitor', max_length=30, required=False)
    receipt_payer_name = forms.CharField(label='Plătit de', max_length=200, required=False)
    receipt_payer_address = forms.CharField(label='Adresa plătitor', max_length=200, required=False)
       
    def clean(self):
        cleaned_data = super(NewReceipt, self).clean()    
        if cleaned_data['amount'] <= 0:
            raise forms.ValidationError(u'Te rog să introduci o sumă mai ca zero')   
        
        receipt = {}
        for fn in RECEIPT_FIELDS:
            label = 'receipt_' + fn
            if not label in cleaned_data:
                continue
            receipt[fn] = cleaned_data[label]
            del cleaned_data[label]
        if not 'no' in receipt:
            receipt['no'] = cleaned_data['no']
        cleaned_data['receipt'] = receipt
        return cleaned_data 
    
