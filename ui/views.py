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
from django.http.response import HttpResponse
from django.shortcuts import render
from entities.models import ApartmentGroup


class BlockEditForm(forms.Form):
    name = forms.CharField(label='Nume', max_length=100)
    staircases = forms.IntegerField(label='Număr scări', min_value=1, max_value=100)
    apartments = forms.IntegerField(label='Număr apartamente', min_value=1, max_value=1000)
    apartment_offset = forms.IntegerField(label='Primul apartament', min_value=1, max_value=1000)
    

def __add_new_block(form):
    print form.cleaned_data
    ApartmentGroup.bootstrap_block(**form.cleaned_data)

def new_block(request):
    if request.method == 'POST':
        form = BlockEditForm(request.POST)
        if form.is_valid():
            __add_new_block(form)
            return HttpResponse("will add a new block")
    else:
        form = BlockEditForm() 
    return render(request, 'newblock.html', {'form': form})
