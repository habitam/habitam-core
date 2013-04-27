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
from habitam.entities.models import ApartmentGroup
from habitam.settings import MAX_ISSUANCE_DAY, MAX_PAYMENT_DUE_DAYS, \
    MAX_PENALTY_PER_DAY


class EditBuildingForm(forms.ModelForm):
    name = forms.CharField(label='Nume')

    class Meta:
        model = ApartmentGroup
        fields = ('name',)

class EditStaircaseForm(forms.ModelForm):
    name = forms.CharField(label='Nume')
    type = forms.CharField(label='Type',
                        widget=forms.HiddenInput())
    parent = forms.ModelChoiceField(label='Cladirea',
                        queryset=ApartmentGroup.objects.all(),
                        widget=forms.HiddenInput())
    
    class Meta:
        model = ApartmentGroup
        fields = ('name',)
        
    def __init__(self, *args, **kwargs):
        building = kwargs['building']
        del kwargs['building']
        del kwargs['user']
        
        print kwargs
        initial = {'parent': building.id,
                   'type': 'stair'}
        if kwargs.has_key('initial'):
            kwargs['initial'].update(initial)
        else:
            kwargs['initial'] = initial
        print kwargs
        super(EditStaircaseForm, self).__init__(*args, **kwargs)
        print self.fields
        
         
class NewBuildingForm(forms.Form):
    apartments = forms.IntegerField(label='Număr apartamente', min_value=1,
                                    max_value=1000)
    apartment_offset = forms.IntegerField(label='Primul apartament',
                                    initial=1, min_value=1, max_value=1000)
    daily_penalty = forms.DecimalField(label='Penalitate (procent zilnic)',
                                    initial=MAX_PENALTY_PER_DAY, min_value=0,
                                    max_value=MAX_PENALTY_PER_DAY)
    issuance_day = forms.IntegerField(label='Data afișare listă',
                                    initial=1, min_value=1,
                                    max_value=MAX_ISSUANCE_DAY)
    payment_due_days = forms.IntegerField(label='Zile de scadență',
                                    initial=MAX_PAYMENT_DUE_DAYS, min_value=1,
                                    max_value=MAX_PAYMENT_DUE_DAYS)
    name = forms.CharField(label='Nume', max_length=100)
    staircases = forms.IntegerField(label='Număr scări', initial=1,
                                    min_value=1, max_value=100)

    def __init__(self, user, *args, **kwargs):
        super(NewBuildingForm, self).__init__(*args, **kwargs)
        self.user = user
        self.fields.keyOrder = ['name', 'staircases', 'apartments',
                                'apartment_offset', 'issuance_day',
                                'payment_due_days', 'daily_penalty']
        
    def clean(self):
        l = self.user.administrator.license
        a = l.max_apartments - l.apartment_count()
        if a < self.cleaned_data['apartments']:
            raise forms.ValidationError('Prea multe apartamente')
        return self.cleaned_data

    def spinners(self):
        return ['staircases', 'apartments', 'apartment_offset', 'issuance_day',
                'payment_due_days', 'daily_penalty']
