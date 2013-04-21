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
from django.db.models.query_utils import Q
from django.http.response import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from habitam.entities.models import AccountLink, ApartmentGroup, Service
from habitam.services.models import Account
from habitam.ui.views import NewDocPaymentForm
import logging


logger = logging.getLogger(__name__)


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
   

class NewServicePayment(NewDocPaymentForm):
    service = forms.ModelChoiceField(label='Serviciu', queryset=Service.objects.all())
    
    
    def __init__(self, *args, **kwargs):
        building = kwargs['building']
        del kwargs['building']
        super(NewServicePayment, self).__init__(*args, **kwargs)
        queryset = Service.objects.filter(
                            Q(billed=building) | Q(billed__parent=building))
        self.fields['service'].queryset = queryset


def new_service_payment(request, account_id):
    account_link = AccountLink.objects.get(account__pk=account_id)
    building = account_link.holder.building()
    
    if request.method == 'POST':
        form = NewServicePayment(request.POST, building=building)
        if form.is_valid():
            service = form.cleaned_data['service']
            service.new_payment(account=account_link.account,
                                **form.cleaned_data)
            return render(request, 'edit_ok.html')
    else:
        form = NewServicePayment(building=building)
    
    data = {'form' : form, 'target': 'new_service_payment',
            'entity_id': account_id, 'building': building,
            'title': 'Plata serviciu de la ' + account_link.account.holder }
    return render(request, 'edit_dialog.html', data)



def new_invoice(request, service_id):
    service = Service.objects.get(pk=service_id)
    building = service.billed.building()
    
    if request.method == 'POST':
        form = NewDocPaymentForm(request.POST)
        if form.is_valid():
            service.new_invoice(**form.cleaned_data)
            return render(request, 'edit_ok.html')
    else:
        form = NewDocPaymentForm()
        
    data = {'form': form, 'target': 'new_invoice', 'parent_id': service_id,
            'building': building, 'title': 'Factura noua'}
    return render(request, 'edit_dialog.html', data)
