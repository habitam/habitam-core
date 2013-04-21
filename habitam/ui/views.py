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
from django.http.response import HttpResponseBadRequest, HttpResponse
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

        
class NewPaymentForm(forms.Form):
    amount = forms.DecimalField(label='Suma')
    
    def spinners(self):
        return ['amount']        


class NewDocPaymentForm(NewPaymentForm):
    no = forms.CharField(label='Nume')


class NewServicePayment(NewDocPaymentForm):
    service = forms.ModelChoiceField(label='Serviciu', queryset=Service.objects.all())
    
    
    def __init__(self, *args, **kwargs):
        building = kwargs['building']
        del kwargs['building']
        super(NewServicePayment, self).__init__(*args, **kwargs)
        queryset = Service.objects.filter(
                            Q(billed=building) | Q(billed__parent=building))
        self.fields['service'].queryset = queryset
        
         
class NewFundTransfer(NewDocPaymentForm):
    dest_link = forms.ModelChoiceField(label='Fond',
                            queryset=AccountLink.objects.all())
    
    def __init__(self, *args, **kwargs):
        building = kwargs['building']
        account = kwargs['account']
        del kwargs['building']
        del kwargs['account']
        super(NewFundTransfer, self).__init__(*args, **kwargs)
        queryset = AccountLink.objects.filter(~Q(account=account) & Q(
                            Q(holder=building) | Q(holder__parent=building)))
        self.fields['dest_link'].queryset = queryset


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
    
    data = {'form': form, 'target': 'edit_apartment', 'parent_id': building_id,
            'entity_id': apartment_id, 
            'spinners': EditApartmentForm.spinners(), 'building': building, 
            'title': 'Apartamentul ' + apartment.name}
    return render(request, 'edit_dialog.html', data)          
          

def building_tab(request, building_id, tab):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    return render(request, tab + '.html',
                  {'building': building, 'active_tab': tab})  


def new_fund_transfer(request, account_id):
    src_account = Account.objects.get(pk=account_id)
    account_link = AccountLink.objects.get(account=src_account)
    building = account_link.holder.building()
    
    if request.method == 'POST':
        form = NewFundTransfer(request.POST, account=src_account,
                               building=building)
        if form.is_valid():
            dest_account = form.cleaned_data['dest_link'].account
            del form.cleaned_data['dest_link']
            src_account.new_transfer(dest_account=dest_account,
                                **form.cleaned_data)
            return render(request, 'edit_ok.html')
    else:
        form = NewFundTransfer(account=src_account, building=building)
    
    data = {'form' : form, 'target': 'new_fund_transfer',
            'entity_id': account_id, 'building': building,
            'title': 'Transfer fonduri de la ' + src_account.holder}
    return render(request, 'edit_dialog.html', data)


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


def new_service(request, building_id):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    
    if request.method == 'POST':
        form = EditServiceForm(request.POST, building=building)
        if form.is_valid():
            service = form.save(commit=False)
            service.account = Account.objects.create(holder=service.name)
            service.save() 
            service.set_quota()
            return render(request, 'edit_ok.html')
    else:
        form = EditServiceForm(building=building)
    
    data = {'form': form, 'parent_id': building_id, 'target': 'new_service',
            'building': building, 'title': 'Serviciu nou'}
    return render(request, 'edit_dialog.html', data)
    

def edit_service(request, service_id):
    service = Service.objects.get(pk=service_id)
    orig_billed = service.billed
    orig_qt = service.quota_type
    building = service.billed.building()
   
    if request.method == 'DELETE':
        logger.debug('delete service %d', service_id)
        if service.can_delete():
            service.delete()
            return HttpResponse() 
        else:
            return HttpResponseBadRequest()
    
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
                
            return render(request, 'edit_ok.html')
    else:
        form = EditServiceForm(building=building, instance=service)
    
    data = {'form': form, 'entity_id': service_id, 'target': 'edit_service',
            'building': building, 'title': 'Serviciul ' + service.name}
    
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
   
   
   
def operation_list(request, account_id):
    account = Account.objects.get(pk=account_id)
    
    data = {'account': account, 'docs': account.operation_list(),
            'building': __find_building(account)}
    return render(request, 'operation_list.html', data)


def operation_doc(request, account_id, operationdoc_id):
    OperationDoc.delete_doc(operationdoc_id)
    return redirect('operation_list', account_id=account_id)


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

    