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
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.shortcuts import render, redirect
from habitam.entities.models import ApartmentGroup, Apartment, Service, \
    AccountLink
from habitam.services.models import Account, OperationDoc
import logging


logger = logging.getLogger(__name__)


class NewBuildingForm(forms.Form):
    name = forms.CharField(label='Nume', max_length=100)
    staircases = forms.IntegerField(label='Număr scări', min_value=1, max_value=100)
    apartments = forms.IntegerField(label='Număr apartamente', min_value=1, max_value=1000)
    apartment_offset = forms.IntegerField(label='Primul apartament', min_value=1, max_value=1000)

    def spinners(self):
        return ['staircases', 'apartments', 'apartment_offset']

   
class NewPaymentForm(forms.Form):
    amount = forms.DecimalField(label='Suma')
    
    def spinners(self):
        return ['amount']        


class NewDocPaymentForm(NewPaymentForm):
    no = forms.CharField(label='Nume')

         
def __find_building(account): 
    try:
        service = Service.objects.get(account=account)
        return service.billed.building()
    except Service.DoesNotExist:
        pass
    try:
        apartment = Apartment.objects.get(account=account)
        return apartment.building()
    except Apartment.DoesNotExist:
        pass
    try:
        account_link = AccountLink.objects.get(account=account)
        return account_link.holder.building()
    except AccountLink.DoesNotExist:
        pass
    return None


def home(request):
    return render(request, 'home.html')
         
def new_building(request):
    if request.method == 'POST':
        form = NewBuildingForm(request.POST)
        if form.is_valid():
            building_id = ApartmentGroup.bootstrap_building(**form.cleaned_data)
            url = reverse('apartment_list', args=[building_id])
            data = {'location': url}
            return render(request, 'edit_redirect.html', data)
    else:
        form = NewBuildingForm() 
    data = {'form': form, 'target': 'new_building', 'title': 'Cladire noua'}
    return render(request, 'edit_dialog.html', data)


def building_tab(request, building_id, tab):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    return render(request, tab + '.html',
                  {'building': building, 'active_tab': tab})  

   
def operation_list(request, account_id):
    account = Account.objects.get(pk=account_id)
    
    data = {'account': account, 'docs': account.operation_list(),
            'building': __find_building(account)}
    return render(request, 'operation_list.html', data)


def operation_doc(request, account_id, operationdoc_id):
    OperationDoc.delete_doc(operationdoc_id)
    return redirect('operation_list', account_id=account_id)



