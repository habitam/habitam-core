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
    'series',
    'reference',
    'fiscal_id',
    'registration_id',
]

RECEIPT_FIELDS = [
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


class NewReceiptPayment(NewDocPaymentForm):
    description = forms.CharField(label='Descriere chitanță', max_length=200, required=False)
    fiscal_id = forms.CharField(label='Nr. înregistrare fiscală', max_length=30, required=False)
    registration_id = forms.CharField(label='Nr. registrul comerțului', max_length=30, required=False)
    payer_name = forms.CharField(label='Plătit de', max_length=200, required=False)
    payer_address = forms.CharField(label='Adresa', max_length=200, required=False)
       
    def clean(self):
        cleaned_data = super(NewReceiptPayment, self).clean()    
        if cleaned_data['amount'] <= 0:
            raise forms.ValidationError(u'Te rog să introduci o sumă mai ca zero')   
        
        receipt = {}
        for fn in RECEIPT_FIELDS:
            receipt[fn] = cleaned_data[fn]
            del cleaned_data[fn]
        cleaned_data['receipt'] = receipt
        return cleaned_data 
    