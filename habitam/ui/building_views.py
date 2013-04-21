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
from django.http.response import HttpResponseBadRequest, HttpResponse
from django.shortcuts import render
from habitam.entities.models import ApartmentGroup


class EditStaircaseForm(forms.ModelForm):
    name = forms.CharField(label='Nume')
    
    class Meta:
        model = ApartmentGroup
        fields = ('name',)
        

def edit_staircase(request, apgroup_id):
    ag = ApartmentGroup.objects.get(pk=apgroup_id)
     
    if request.method == 'DELETE':
        if ag.can_delete():
            ag.delete()
            return HttpResponse()
        else:
            return HttpResponseBadRequest()
    if request.method == 'POST':
        form = EditStaircaseForm(request.POST, instance=ag)
        if form.is_valid():
            form.save()
            return render(request, 'edit_ok.html')
    else:
        form = EditStaircaseForm(instance=ag)
        
    data = {'form': form, 'target': 'edit_staircase', 'entity_id': ag.id,
            'title': 'Scara ' + ag.name}
    return render(request, 'edit_dialog.html', data)


def new_staircase(request, building_id):
    if request.method == 'POST':
        form = EditStaircaseForm(request.POST)
        if form.is_valid():
            building = ApartmentGroup.objects.get(pk=building_id)
            ApartmentGroup.create(form.cleaned_data['name'], 'stair',
                                  building)
            return render(request, 'edit_ok.html')
    else:
        form = EditStaircaseForm()
        
    data = {'form': form, 'target': 'new_staircase', 'parent_id': building_id,
            'title': 'Scara noua'}
    return render(request, 'edit_dialog.html', data)
