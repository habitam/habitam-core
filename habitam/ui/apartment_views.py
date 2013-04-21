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
from habitam.entities.models import ApartmentGroup, Apartment


class EditApartmentForm(forms.ModelForm):
    name = forms.CharField(label='Nume')
    floor = forms.IntegerField(label='Etaj', required=False, min_value=1, max_value=50)
    inhabitance = forms.IntegerField(label='Locatari', min_value=0, max_value=50)
    area = forms.IntegerField(label='Suprafață', min_value=1, max_value=1000)
    parent = forms.ModelChoiceField(label='Scara', queryset=ApartmentGroup.objects.all())
    rooms = forms.IntegerField(label='Camere', min_value=1, max_value=20)
    
    def spinners(self):
        return ['floor', 'inhabitance', 'area', 'rooms']
     
    class Meta:
        model = Apartment
        fields = ('name', 'parent', 'floor', 'inhabitance', 'area', 'rooms')
    
    def __init__(self, *args, **kwargs):
        building = kwargs['building']
        del kwargs['building']
        super(EditApartmentForm, self).__init__(*args, **kwargs)
        staircases = ApartmentGroup.objects.filter(parent=building)
        self.fields['parent'].queryset = staircases 

