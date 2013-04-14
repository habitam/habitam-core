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
    
Created on Apr 12, 2013

@author: Stefan Guna
'''
from django import forms
from django.http.response import HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from entities.models import ApartmentGroup, Apartment


class BlockEditForm(forms.Form):
    name = forms.CharField(label='Nume', max_length=100)
    staircases = forms.IntegerField(label='Număr scări', min_value=1, max_value=100)
    apartments = forms.IntegerField(label='Număr apartamente', min_value=1, max_value=1000)
    apartment_offset = forms.IntegerField(label='Primul apartament', min_value=1, max_value=1000)

    @classmethod
    def spinners(cls):
        return ['staircases', 'apartments', 'apartment_offset']


class ApartmentEditForm(forms.ModelForm):
    name = forms.CharField(label='Nume')
    floor = forms.IntegerField(label='Etaj', required=False, min_value=1, max_value=50)
    inhabitance = forms.IntegerField(label='Locatari', min_value=0, max_value=50)
    area = forms.IntegerField(label='Suprafață', min_value=1, max_value=1000)
    rooms = forms.IntegerField(label='Camere', min_value=1, max_value=20)
   
    @classmethod
    def spinners(cls):
        return ['floor', 'inhabitance', 'area', 'rooms']
     
    class Meta:
        model = Apartment
        fields = ('name', 'floor', 'inhabitance', 'area', 'rooms')
        
        
def new_building(request):
    if request.method == 'POST':
        form = BlockEditForm(request.POST)
        if form.is_valid():
            ApartmentGroup.bootstrap_building(**form.cleaned_data)
            return HttpResponse("will add a new building")
    else:
        form = BlockEditForm() 
    data = {'form': form, 'spinners': BlockEditForm.spinners(),
            'target': 'new_building'}
    return render(request, 'edit_entity.html', data)


def edit_apartment(request, apartment_id=None):
    apartment = Apartment.objects.get(pk=apartment_id)
    if request.method == 'POST':
        form = ApartmentEditForm(request.POST, instance=apartment)
        if form.is_valid():
            form.save()
            return render(request, 'apartment_list.html', 
                          {'building': apartment.building}) 
    else:
        form = ApartmentEditForm(instance=apartment)
    data = {'form': form, 'target': 'edit_apartment',
            'entity_id': apartment_id,
            'spinners': ApartmentEditForm.spinners()}
    return render(request, 'edit_entity.html', data)
            

def apartment_list(request, building_id):
    try:
        building = ApartmentGroup.objects.get(pk=building_id)
    except ApartmentGroup.DoesNotExist:
        return HttpResponseNotFound('Nu am găsit blocul')
    if building.type != 'building':
        return HttpResponseNotFound('Nu am găsit blocul')
    return render(request, 'apartment_list.html', {'building': building})
