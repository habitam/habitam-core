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
from django.shortcuts import render, redirect
from habitam.entities.models import ApartmentGroup, Apartment, Service, \
    AccountLink
from habitam.services.models import Account
import logging


logger = logging.getLogger(__name__)


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

        
class NewInvoiceForm(forms.Form):
    no = forms.CharField(label='Nume')
    amount = forms.DecimalField(label='Suma')
    
    @classmethod
    def spinners(cls):
        return ['amount']


class NewPaymentForm(forms.Form):
    amount = forms.DecimalField(label='Suma')
    
    @classmethod
    def spinners(cls):
        return ['amount']        


class NewServicePayment(forms.Form):
    no = forms.CharField(label='Nume')
    amount = forms.DecimalField(label='Suma')
    service = forms.ModelChoiceField(label='Serviciu', queryset=Account.objects.all())
    
    @classmethod
    def spinners(cls):
        return ['amount']

    def __init__(self, *args, **kwargs):
        building = kwargs['building']
        del kwargs['building']
        super(NewServicePayment, self).__init__(*args, **kwargs)
        services = Service.objects.filter(
                            Q(billed=building) | Q(billed__parent=building))
        self.fields['service'].queryset = services
        
         
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
    orig_parent = apartment.parent
    
    if request.method == 'POST':
        form = EditApartmentForm(request.POST, building=building,
                                 instance=apartment)
        if form.is_valid():
            form.save()
            
            if form.cleaned_data['parent'] != orig_parent:
                orig_parent.update_quotas()
                form.cleaned_data['parent'].update_quotas()
                
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


def fund_list(request, building_id):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    return render(request, 'fund_list.html', {'building': building})


def new_service_payment(request, account_id):
    account_link = AccountLink.objects.get(account__pk=account_id)
    building = account_link.holder.building()
    
    if request.method == 'POST':
        form = NewServicePayment(request.POST, building=building)
        if form.is_valid():
            service = form.cleaned_data['service']
            service.new_payment(account=account_link.account,
                                **form.cleaned_data)
            return redirect('fund_list', building_id=building.id)
    else:
        form = NewServicePayment(building=building)
    
    data = {'form' : form, 'target': 'new_service_payment',
            'entity_id': account_id}
    return render(request, 'edit_entity.html', data)


def new_service(request, building_id):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    
    if request.method == 'POST':
        form = EditServiceForm(request.POST, building=building)
        if form.is_valid():
            service = form.save(commit=False)
            service.account = Account.objects.create(holder=service.name)
            service.save() 
            service.set_quota()
            return redirect('service_list', building_id=building_id)
    else:
        form = EditServiceForm(building=building)
    
    data = {'form': form, 'parent_id': building_id, 'target': 'new_service'}
    return render(request, 'edit_entity.html', data)
    

def edit_service(request, service_id=None):
    service = Service.objects.get(pk=service_id)
    orig_billed = service.billed
    orig_qt = service.quota_type
    building = service.billed.building()
    
    if request.method == 'POST':
        form = EditServiceForm(request.POST, building=building,
                              instance=service)
        if form.is_valid():
            service = form.save(commit=False)
            service.account.holder = service.name
            service.save()
            
            logger.debug('edit service %s, %s -> %s %s', orig_billed, orig_qt,
                         service.billed, service.quota_type)
            if orig_billed != service.billed:
                service.drop_quota()
            if orig_billed != service.billed or orig_qt != service.quota_type:
                service.set_quota()
                
            return redirect('service_list', building_id=building.id)
    else:
        form = EditServiceForm(building=building, instance=service)
    
    data = {'form': form, 'entity_id': service_id, 'target': 'edit_service'}
    
    return render(request, 'edit_entity.html', data)


def service_list(request, building_id):
    building = ApartmentGroup.objects.get(pk=building_id)
    services = building.services() 
    data = {'building': building, 'services': services}
    return render(request, 'service_list.html', data)


def new_invoice(request, service_id):
    if request.method == 'POST':
        form = NewInvoiceForm(request.POST)
        if form.is_valid():
            service = Service.objects.get(pk=service_id)
            service.new_invoice(**form.cleaned_data)
            return redirect('service_list',
                            building_id=service.billed.building().id)
    else:
        form = NewInvoiceForm()
        
    data = {'form': form, 'target': 'new_invoice', 'parent_id': service_id,
            'spinners': NewInvoiceForm.spinners()}
    return render(request, 'edit_entity.html', data)
    
    
def operation_list(request, account_id):
    account = Account.objects.get(pk=account_id)
    
    data = {'account': account, 'docs': account.operation_list()}
    return render(request, 'operation_list.html', data)


def new_payment(request, apartment_id):
    if request.method == 'POST':
        form = NewPaymentForm(request.POST)
        if form.is_valid():
            apartment = Apartment.objects.get(pk=apartment_id)
            apartment.new_payment(**form.cleaned_data)
            return redirect('apartment_list',
                            building_id=apartment.building().id)
    else:
        form = NewPaymentForm()
    
    data = {'form': form, 'target': 'new_payment', 'parent_id': apartment_id,
            'spinners': NewPaymentForm.spinners()}
    return render(request, 'edit_entity.html', data)

    
