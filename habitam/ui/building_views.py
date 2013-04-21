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
         
