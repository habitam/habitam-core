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
from django.db.models.query_utils import Q
from django.http.response import HttpResponseNotFound
from django.shortcuts import render, redirect
from entities.models import ApartmentGroup, Apartment, Service


class NewBuildingForm(forms.Form):
    name = forms.CharField(label='Nume', max_length=100)
    staircases = forms.IntegerField(label='Număr scări', min_value=1, max_value=100)
    apartments = forms.IntegerField(label='Număr apartamente', min_value=1, max_value=1000)
    apartment_offset = forms.IntegerField(label='Primul apartament', min_value=1, max_value=1000)

    @classmethod
    def spinners(cls):
        return ['staircases', 'apartments', 'apartment_offset']


class EditServiceForm(forms.ModelForm):
    name = forms.CharField(label='Nume', max_length=100)
    billed = forms.ModelChoiceField(label='Clienți', queryset=ApartmentGroup.objects.all())
    quota_type = forms.ChoiceField(label='Distribuie cota', choices=Service.QUOTA_TYPES)

    class Meta:
        model = Service
        fields = ('name', 'billed', 'quota_type')
        
    def __init__(self, *args, **kwargs):
        building = kwargs['building']
        del kwargs['building']
        super(EditServiceForm, self).__init__(*args, **kwargs)
        self.fields['billed'].queryset = ApartmentGroup.objects.filter(Q(parent=building) | Q(pk=building.id))
        

class EditApartmentForm(forms.ModelForm):
    name = forms.CharField(label='Nume')
    floor = forms.IntegerField(label='Etaj', required=False, min_value=1, max_value=50)
    inhabitance = forms.IntegerField(label='Locatari', min_value=0, max_value=50)
    area = forms.IntegerField(label='Suprafață', min_value=1, max_value=1000)
    parent = forms.ModelChoiceField(label='Scara', queryset=ApartmentGroup.objects.all())
    rooms = forms.IntegerField(label='Camere', min_value=1, max_value=20)
    
    @classmethod
    def spinners(cls):
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
        
        
def new_building(request):
    if request.method == 'POST':
        form = NewBuildingForm(request.POST)
        if form.is_valid():
            ApartmentGroup.bootstrap_building(**form.cleaned_data)
            return redirect('building_list')
    else:
        form = NewBuildingForm() 
    data = {'form': form, 'spinners': NewBuildingForm.spinners(),
            'target': 'new_building'}
    return render(request, 'edit_entity.html', data)


def building_list(request):
    buildings = ApartmentGroup.objects.filter(type='building')
    return render(request, 'building_list.html', {'buildings': buildings})


def edit_apartment(request, building_id, apartment_id=None):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    apartment = Apartment.objects.get(pk=apartment_id)
    
    if request.method == 'POST':
        form = EditApartmentForm(request.POST, building=building,
                                 instance=apartment)
        if form.is_valid():
            form.save()
            return redirect('apartment_list',
                    building_id=apartment.building().id)
    else:
        form = EditApartmentForm(building=building, instance=apartment)
    data = {'form': form, 'target': 'edit_apartment',
            'parent_id': building_id, 'entity_id': apartment_id,
            'spinners': EditApartmentForm.spinners()}
    return render(request, 'edit_entity.html', data)          
          

def apartment_list(request, building_id):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    return render(request, 'apartment_list.html', {'building': building})  


def edit_service(request, building_id, service_id=None):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    service = None
    if service_id != None:
        service = Service.objects.get(pk=service_id)
    
    if request.method == 'POST':
        form = EditServiceForm(request.POST, building=building,
                              instance=service)
        if form.is_valid():
            service = form.save(commit=False)
            service.save()
            quota_type = form.cleaned_data['quota_type']
            if quota_type == 'None':
                service.set_quota()
            else:
                service.set_quota(quota_type)
            return redirect('service_list',
                    building_id=building_id)
    else:
        if service != None:
            form = EditServiceForm(building=building, instance=service)
        else:
            form = EditServiceForm(building=building)
    
    data = {'form': form, 'parent_id': building_id}
    
    if service != None:
        data['entity_id'] = service_id
        data['target'] = 'edit_service'
    else:
        data['target'] = 'new_service'
    
    return render(request, 'edit_entity.html', data)


def service_list(request, building_id):
    building = ApartmentGroup.objects.get(pk=building_id)
    services = building.services() 
    data = {'building': building, 'services': services}
    return render(request, 'service_list.html', data)
