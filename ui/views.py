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


class NewServiceForm(forms.ModelForm):
    QUOTA_TYPES = (
        (None, 'în mod egal'),
        ('inhabitance', 'după număr persoane'),
        ('area', 'după suprafață'),
        ('rooms', 'după număr camere')
    )
    name = forms.CharField(label='Nume', max_length=100)
    quota_type = forms.ChoiceField(label='Distribuie cota', choices=QUOTA_TYPES)

    class Meta:
        model = Service
        fields = ('name', 'quota_type')
        

class EditApartmentForm(forms.ModelForm):
    name = forms.CharField(label='Nume')
    floor = forms.IntegerField(label='Etaj', required=False, min_value=1, max_value=50)
    inhabitance = forms.IntegerField(label='Locatari', min_value=0, max_value=50)
    area = forms.IntegerField(label='Suprafață', min_value=1, max_value=1000)
    parent = forms.ModelChoiceField(queryset=ApartmentGroup.objects.all())
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
    building = ApartmentGroup.objects.get(pk=building_id)
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
    try:
        building = ApartmentGroup.objects.get(pk=building_id)
    except ApartmentGroup.DoesNotExist:
        return HttpResponseNotFound('Nu am găsit blocul')
    if building.type != 'building':
        return HttpResponseNotFound('Nu am găsit blocul')
    return render(request, 'apartment_list.html', {'building': building})  


def new_service(request, billed_id):
    if request.method == 'POST':
        billed = ApartmentGroup.objects.get(pk=billed_id)
        form = NewServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.billed = billed
            service.save()
            quota_type = form.cleaned_data['quota_type']
            if quota_type == 'None':
                service.set_quota()
            else:
                service.set_quota(quota_type)
            return redirect('apartment_list',
                    building_id=billed.building().id)
    else:
        form = NewServiceForm()
    data = {'form': form, 'target': 'new_service',
            'parent_id': billed_id}
    return render(request, 'edit_entity.html', data)


def service_list(request, billed_id):
    billed = ApartmentGroup.objects.get(pk=billed_id)
    services = Service.objects.filter(billed=billed)
    print billed, services
    data = {'billed': billed, 'services': services}
    return render(request, 'service_list.html', data)