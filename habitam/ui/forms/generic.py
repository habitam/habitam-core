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


class NewBuildingForm(forms.Form):
    name = forms.CharField(label='Nume', max_length=100)
    staircases = forms.IntegerField(label='Număr scări', min_value=1, max_value=100)
    apartments = forms.IntegerField(label='Număr apartamente', min_value=1, max_value=1000)
    apartment_offset = forms.IntegerField(label='Primul apartament', min_value=1, max_value=1000)

    def __init__(self, user, *args, **kwargs):
        super(NewBuildingForm, self).__init__(*args, **kwargs)
        self.user = user
        
    def clean(self):
        l = self.user.administrator.license
        a = l.max_apartments - l.apartment_count()
        if a < self.cleaned_data['apartments']:
            raise forms.ValidationError('Prea multe apartamente')
        return self.cleaned_data

    def spinners(self):
        return ['staircases', 'apartments', 'apartment_offset']

   
class NewPaymentForm(forms.Form):
    amount = forms.DecimalField(label='Suma')
    
    def spinners(self):
        return ['amount']        


class NewDocPaymentForm(NewPaymentForm):
    no = forms.CharField(label='Nume')
