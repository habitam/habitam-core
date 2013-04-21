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
from django.http.response import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from habitam.entities.models import ApartmentGroup, Apartment
from habitam.services.models import Account
from habitam.ui.views import NewPaymentForm


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


def edit_apartment(request, apartment_id):
    apartment = Apartment.objects.get(pk=apartment_id)
    building = apartment.building() 
    orig_parent = apartment.parent
    
    if request.method == 'DELETE':
        if apartment.can_delete():
            apartment.delete()
            return HttpResponse()
        else:
            return HttpResponseBadRequest()
    
    if request.method == 'POST':
        ''' uncool: there's logic in here '''
        form = EditApartmentForm(request.POST, building=building,
                                 instance=apartment)
        if form.is_valid():
            form.save()
            
            if form.cleaned_data['parent'] != orig_parent:
                orig_parent.update_quotas()
                form.cleaned_data['parent'].update_quotas()
                
            return render(request, 'edit_ok.html')
    else:
        form = EditApartmentForm(building=building, instance=apartment)
    
    data = {'form': form, 'target': 'edit_apartment', 'entity_id': apartment_id,
            'building': building, 'title': 'Apartamentul ' + apartment.name}
    return render(request, 'edit_dialog.html', data)


def new_apartment(request, building_id):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    
    if request.method == 'POST':
        ''' uncool: there's logic in here '''
        form = EditApartmentForm(request.POST, building=building)
        if form.is_valid():
            ap = form.save(commit=False)
            ap.account = Account.objects.create(holder=ap.name)
            ap.save()
            ap.parent.update_quotas()
                
            return render(request, 'edit_ok.html')
    else:
        form = EditApartmentForm(building=building)
    
    data = {'form': form, 'target': 'new_apartment', 'parent_id': building_id,
            'building': building, 'title': 'Apartament nou'}
    return render(request, 'edit_dialog.html', data)


def new_payment(request, apartment_id):
    apartment = Apartment.objects.get(pk=apartment_id)
    building = apartment.building()
    
    if request.method == 'POST':
        form = NewPaymentForm(request.POST)
        if form.is_valid():
            apartment.new_payment(**form.cleaned_data)
            return render(request, 'edit_ok.html')
    else:
        form = NewPaymentForm()
    
    data = {'form': form, 'target': 'new_payment', 'parent_id': apartment_id,
            'building': building, 'title': 'Apartamentul ' + apartment.name}
    return render(request, 'edit_dialog.html', data)

          
