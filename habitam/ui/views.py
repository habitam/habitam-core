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
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.http.response import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from habitam.downloads.display_list import download_display_list
from habitam.entities.models import ApartmentGroup, Apartment, Service, \
    AccountLink
from habitam.financial.models import Account, OperationDoc
from habitam.ui.forms.building import NewBuildingForm
import logging


logger = logging.getLogger(__name__)

         
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


def license_valid(user):
    l = user.administrator.license
    return date.today() < l.valid_until


@login_required
@user_passes_test(license_valid)
def home(request):
    return render(request, 'home.html')


@login_required
@user_passes_test(license_valid)   
def new_building(request):
    if request.method == 'POST':
        form = NewBuildingForm(request.user, request.POST)
        if form.is_valid():
            building_id = ApartmentGroup.bootstrap_building(
                    request.user.administrator.license, **form.cleaned_data)
            url = reverse('apartment_list', args=[building_id])
            data = {'location': url}
            return render(request, 'edit_redirect.html', data)
    else:
        form = NewBuildingForm(request.user) 
    data = {'form': form, 'target': 'new_building', 'title': 'Cladire noua'}
    return render(request, 'edit_dialog.html', data)


@login_required
@user_passes_test(license_valid)
def building_tab(request, building_id, tab):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    return render(request, tab + '.html',
                  {'building': building, 'active_tab': tab})  

@login_required
@user_passes_test(license_valid)   
def download_list(request, building_id, month):
    building = ApartmentGroup.objects.get(pk=building_id)
    begin_ts = datetime.strptime(month + '-%02d' % building.close_day,
                                  "%Y-%m-%d").date()
    end_ts = begin_ts + relativedelta(months=1) 
    l = request.user.administrator.license
    l.validate_month(building, begin_ts)

    temp = download_display_list(building, begin_ts, end_ts)
    
    wrapper = FileWrapper(temp)
    response = HttpResponse(wrapper, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=lista' + building.name + '_' + month + '.txt'
    response['Content-Length'] = temp.tell()
    temp.seek(0)
    return response
   

@login_required
@user_passes_test(license_valid)   
def operation_list(request, building_id, account_id, month=None):
    building = ApartmentGroup.objects.get(pk=building_id)
    if month == None:
        today = date.today()
        month = date(day=building.close_day, month=today.month,
                     year=today.year)
    else:
        month = datetime.strptime(month + '-%02d' % building.close_day,
                                  "%Y-%m-%d").date()
    
    l = request.user.administrator.license
    l.validate_month(building, month)
    month_end = month + relativedelta(months=1) 
    
    account = Account.objects.get(pk=account_id)
    
    ops = account.operation_list(month, month_end)
    initial_penalties, final_penalties = None, None
    src_exclude = None
    
    apartment = Apartment.for_account(account)
    # TODO(Stefan) there's logic put in the view, this is uncool
    if apartment != None:
        initial_penalties = apartment.penalties(month)
        final_penalties = apartment.penalties(month_end)
        src_exclude = Q(dest=apartment.building().penalties_account)
        
    service = Service.for_account(account)
    if service != None and service.service_type == 'collecting':
        src_exclude = Q(doc__type='collection')
        
    initial = account.balance(month, src_exclude)
    final = account.balance(month_end, src_exclude)
    
    data = {'account': account, 'docs': ops, 'building': building,
            'initial_balance': initial, 'initial_penalties': initial_penalties,
            'final_balance': final, 'final_penalties': final_penalties,
            'month': month, 'month_end': month_end, 'service': service,
            'building': __find_building(account)}
    return render(request, 'operation_list.html', data)


@login_required
@user_passes_test(license_valid)
def operation_doc(request, building_id, account_id, operationdoc_id):
    OperationDoc.delete_doc(operationdoc_id)
    return redirect('operation_list', building_id=building_id,
                    account_id=account_id)


@login_required
@user_passes_test(license_valid)
def edit_entity(request, entity_id, entity_cls, form_cls, target, title='Entity'):
    entity = entity_cls.objects.get(pk=entity_id)
    building = entity.building()
    
    if request.method == 'DELETE':
        if entity.can_delete():
            entity.delete()
            return HttpResponse()
        else:
            return HttpResponseBadRequest()
    
    if request.method == 'POST':
        form = form_cls(request.POST, user=request.user, building=building,
                        instance=entity)
        if form.is_valid():
            form.save()
            return render(request, 'edit_ok.html')
    else:
        form = form_cls(user=request.user, building=building, instance=entity)
    
    data = {'form': form, 'target': target, 'entity_id': entity_id,
            'building': building, 'title': title + ' ' + entity.name}
    return render(request, 'edit_dialog.html', data)


@login_required
@user_passes_test(license_valid)
def edit_simple_entity(request, entity_id, entity_cls, form_cls, target, title='Entity'):
    entity = entity_cls.objects.get(pk=entity_id)
    
    if request.method == 'DELETE':
        if entity.can_delete():
            entity.delete()
            return HttpResponse()
        else:
            return HttpResponseBadRequest()
    
    if request.method == 'POST':
        form = form_cls(request.POST, instance=entity)
        if form.is_valid():
            form.save()
            return render(request, 'edit_ok.html')
    else:
        form = form_cls(instance=entity)
    
    data = {'form': form, 'target': target, 'entity_id': entity_id,
            'title': title + ' ' + entity.name}
    return render(request, 'edit_dialog.html', data)


@login_required
@user_passes_test(license_valid)
def new_building_entity(request, building_id, form_cls, target,
                        title='New Entity', save_kwargs=None,
                        commit_directly=False):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    
    if request.method == 'POST':
        form = form_cls(request.POST, user=request.user, building=building)
        if form.is_valid():
            if commit_directly:
                form.save()
            else: 
                entity = form.save(commit=False)
                if save_kwargs != None:
                    save_kwargs['building'] = building
                    entity.save(**save_kwargs)
                else:
                    entity.save()
            return render(request, 'edit_ok.html')
    else:
        form = form_cls(user=request.user, building=building)
    data = {'form': form, 'target': target, 'parent_id': building_id,
            'building': building, 'title': title}
    return render(request, 'edit_dialog.html', data)


@login_required
@user_passes_test(license_valid)
def new_inbound_operation(request, entity_id, entity_cls, form_cls, target,
                        title):
    entity = entity_cls.objects.get(pk=entity_id)
    building = entity.building()
    
    if request.method == 'POST':
        form = form_cls(request.POST, entity=entity)
        if form.is_valid():
            entity.new_inbound_operation(**form.cleaned_data)
            return render(request, 'edit_ok.html')
    else:
        form = form_cls(entity=entity, initial=entity.initial_operation())
    
    data = {'form': form, 'target': target, 'parent_id': entity_id,
            'building': building, 'title': title + ' ' + entity.name}
    return render(request, 'edit_dialog.html', data)  


@login_required
@user_passes_test(license_valid)
def new_transfer(request, account_id, form_cls, form_dest_key, target, title):
    src_account = Account.objects.get(pk=account_id)
    try:
        account_link = AccountLink.objects.get(account=src_account)
        building = account_link.holder.building()
    except AccountLink.DoesNotExist:
        service = Service.objects.get(account=src_account)
        building = service.building()
    
    if request.method == 'POST':
        form = form_cls(request.POST, account=src_account,
                               user=request.user, building=building)
        if form.is_valid():
            src_account.new_transfer(**form.cleaned_data)
            return render(request, 'edit_ok.html')
    else:
        form = form_cls(account=src_account, user=request.user,
                        building=building)
    
    data = {'form' : form, 'target': target, 'entity_id': account_id,
            'building': building,
            'title': title + ' ' + src_account.name}
    return render(request, 'edit_dialog.html', data)
