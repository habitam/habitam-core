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
from django.forms.util import ErrorDict
from django.forms.forms import NON_FIELD_ERRORS 
   
class NewPaymentForm(forms.Form):
    amount = forms.DecimalField(label='Suma')
    
    def __init__(self, *args, **kwargs):
        if 'entity' in kwargs.keys():
            del kwargs['entity']
        super(NewPaymentForm, self).__init__(*args, **kwargs)
        
    def spinners(self):
        return ['amount']        

    def add_form_error(self, error_message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(error_message)

class NewDocPaymentForm(NewPaymentForm):
    no = forms.CharField(label='Nume')
