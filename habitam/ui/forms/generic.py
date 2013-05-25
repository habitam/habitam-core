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
from django.forms.extras.widgets import SelectDateWidget


   
class NewPaymentForm(forms.Form):
    amount = forms.DecimalField(label='Suma', help_text="Suma")
    
    def __init__(self, *args, **kwargs):
        if 'entity' in kwargs.keys():
            del kwargs['entity']
        super(NewPaymentForm, self).__init__(*args, **kwargs)
        
    def spinners(self):
        return ['amount']        


class NewDocPaymentForm(NewPaymentForm):
    no = forms.CharField(label='Numar document', help_text="Seria si numarul documentului.")
    issue_date = forms.DateField(label='Data emiterii', widget=SelectDateWidget, help_text="Data emiterii documentului.")
    
