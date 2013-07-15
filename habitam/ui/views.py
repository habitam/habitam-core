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
from django.contrib.auth.decorators import login_required
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.http.response import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.utils.decorators import decorator_from_middleware
from habitam.downloads.display_list import download_display_list
from habitam.entities.accessor import entity_for_account, building_for_account
from habitam.entities.models import ApartmentGroup, Apartment, Service, \
    AccountLink, CollectingFund
from habitam.financial.models import Account, OperationDoc
from habitam.ui.forms.building import NewBuildingForm
from habitam.ui.license_filter import LicenseFilter
import logging


logger = logging.getLogger(__name__)


@login_required
@decorator_from_middleware(LicenseFilter)
def home(request):
    return render(request, 'home.html')


@login_required
@decorator_from_middleware(LicenseFilter)
def new_building(request):
    if request.method == 'POST':
        form = NewBuildingForm(request.user, request.POST)
        if form.is_valid():
            try:
                building_id = ApartmentGroup.bootstrap_building(
                                                                request.user.administrator.license, **form.cleaned_data)
                url = reverse('apartment_list', args=[building_id])
                data = {'location': url}
                return render(request, 'edit_redirect.html', data)
            # TODO @iia catch by different exceptions
            except Exception as e:
                data = {'form': form, 'target': 'new_building', 'title': 'Cladire noua'}  
                form.add_form_error(e)
                return render(request, 'edit_dialog.html', data)
    else:
        form = NewBuildingForm(request.user) 
    data = {'form': form, 'target': 'new_building', 'title': 'Cladire noua'}
    return render(request, 'edit_dialog.html', data)


@login_required
@decorator_from_middleware(LicenseFilter)
def building_tab(request, building_id, tab, show_all=False):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    data = {'building': building, 'active_tab': tab, 'show_all': show_all}
    return render(request, tab + '.html', data)  

@login_required
@decorator_from_middleware(LicenseFilter)
def download_list(request, building_id, month):
    building = ApartmentGroup.objects.get(pk=building_id)
    begin_ts = datetime.strptime(month + '-%02d' % building.close_day,
                                  "%Y-%m-%d").date()
    end_ts = begin_ts + relativedelta(months=1) 
    l = request.user.administrator.license
    l.validate_month(building, begin_ts)
   
    building.mark_display(begin_ts) 

    temp = download_display_list(building, begin_ts, end_ts)
    
    wrapper = FileWrapper(temp)
    response = HttpResponse(wrapper, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=lista' + building.name + '_' + month + '.pdf'
    response['Content-Length'] = temp.tell()
    temp.seek(0)
    return response

@login_required
@decorator_from_middleware(LicenseFilter)
def general_list(request, license_subtype, entity_cls, edit_name, new_name,
                 title, view_name, entity_view_name=None, alt_view_name=None,
                 show_all=False):
    l = request.user.administrator.license
    g = getattr(l, 'available_' + license_subtype)
    if alt_view_name == None:
        alt_view_name = view_name
    data = {'entities': g(), 'title': title, 'entity_cls': entity_cls,
            'edit_name': edit_name, 'new_name': new_name, 'show_all': show_all,
            'view_name': view_name, 'alt_view_name': alt_view_name,
            'entity_view_name': entity_view_name}
    return render(request, 'general_list.html', data)
       

@login_required
@decorator_from_middleware(LicenseFilter)
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
    
    apartment = entity_for_account(Apartment, account)
    # TODO(Stefan) there's logic put in the view, this is uncool
    if apartment != None:
        initial_penalties = apartment.penalties(month)
        final_penalties = apartment.penalties(month_end)
        src_exclude = Q(dest=apartment.building().penalties_account)
        
    service = entity_for_account(CollectingFund, account)
    if service != None:
        src_exclude = Q(doc__type='collection')
        
    initial = account.balance(month, src_exclude)
    final = account.balance(month_end, src_exclude)
    
    data = {'account': account, 'docs': ops, 'building': building,
            'initial_balance': initial, 'initial_penalties': initial_penalties,
            'final_balance': final, 'final_penalties': final_penalties,
            'month': month, 'month_end': month_end, 'service': service,
            'building': building_for_account(account)}
    return render(request, 'operation_list.html', data)


@login_required
@decorator_from_middleware(LicenseFilter)
def operation_doc(request, building_id, account_id, operationdoc_id):
    OperationDoc.delete_doc(operationdoc_id)
    return redirect('operation_list', building_id=building_id,
                    account_id=account_id)


@login_required
@decorator_from_middleware(LicenseFilter)
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
            try:
                form.save()
                return render(request, 'edit_ok.html')
            # TODO @iia catch by different exceptions
            except Exception as e:
                data = {'form': form, 'target': target, 'entity_id': entity_id,
                            'building': building, 'title': title + ' ' + entity.name} 
                form.add_form_error(e)

                return render(request, 'edit_dialog.html', data)

    else:
        form = form_cls(user=request.user, building=building, instance=entity)
    
    data = {'form': form, 'target': target, 'entity_id': entity_id,
            'building': building, 'title': title + ' ' + entity.name}
    return render(request, 'edit_dialog.html', data)


@login_required
@decorator_from_middleware(LicenseFilter)
def edit_simple_entity(request, entity_id, entity_cls, form_cls, target, title='Entity'):
    entity = entity_cls.objects.get(pk=entity_id)
    
    if request.method == 'DELETE':
        if entity.can_delete():
            entity.delete()
            return HttpResponse()
        else:
            return HttpResponseBadRequest()
    
    if request.method == 'POST':
        form = form_cls(request.POST, instance=entity, user=request.user)
        if form.is_valid():
            try:
                form.save()
                return render(request, 'edit_ok.html')
            # TODO @iia catch by different exceptions
            except Exception as e:
                data = {'form': form, 'target': target, 'entity_id': entity_id,
                        'title': title + ' ' + entity.name}
                form.add_form_error(e)

                return render(request, 'edit_dialog.html', data)
    else:
        form = form_cls(instance=entity, user=request.user)
    
    data = {'form': form, 'target': target, 'entity_id': entity_id,
            'title': title + ' ' + entity.name}
    return render(request, 'edit_dialog.html', data)


@login_required
@decorator_from_middleware(LicenseFilter)
def entity_view(request, entity_cls, entity_id, edit_name, view_name):
    entity = entity_cls.objects.get(id=entity_id)
    data = {'entity': entity, 'entity_cls': entity_cls, 'edit_name': edit_name,
            'view_name': view_name}
    return render(request, 'entity_view.html', data)
       

@login_required
@decorator_from_middleware(LicenseFilter)
def new_building_entity(request, building_id, form_cls, target,
                        title='New Entity', save_kwargs=None,
                        commit_directly=False):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    
    if request.method == 'POST':
        form = form_cls(request.POST, user=request.user, building=building)
        if form.is_valid():
            try:
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
            # TODO @iia catch by different exceptions
            except Exception as e:
                data = {'form': form, 'target': target, 'parent_id': building_id,
                        'building': building, 'title': title}
                form.add_form_error(e)

                return render(request, 'edit_dialog.html', data)
    else:
        form = form_cls(user=request.user, building=building)
    data = {'form': form, 'target': target, 'parent_id': building_id,
            'building': building, 'title': title}
    return render(request, 'edit_dialog.html', data)


@login_required
@decorator_from_middleware(LicenseFilter)
def new_inbound_operation(request, entity_id, entity_cls, form_cls, target,
                        title):
    entity = entity_cls.objects.get(pk=entity_id)
    building = entity.building()
    
    if request.method == 'POST':
        form = form_cls(request.POST, entity=entity)
        if form.is_valid():
            try:
                entity.new_inbound_operation(**form.cleaned_data)
            except Exception as e:
                data = {'form': form, 'target': target, 'parent_id': entity_id,
                        'building': building, 'title': title + ' ' + entity.name}
                form.add_form_error(e)
                return render(request, 'edit_dialog.html', data)
            return render(request, 'edit_ok.html')
    else:
        form = form_cls(entity=entity, initial=entity.initial_operation())
    
    data = {'form': form, 'target': target, 'parent_id': entity_id,
            'building': building, 'title': title + ' ' + entity.name}
    return render(request, 'edit_dialog.html', data)  

@login_required
@decorator_from_middleware(LicenseFilter)
def new_simple_entity(request, entity_cls, form_cls, target,
                      title='Entitate nouă'):
    if request.method == 'POST':
        form = form_cls(request.POST, user=request.user)
        if form.is_valid():  
            try:
                if entity_cls.use_license():
                    entity = form.save(commit=False)
                    entity.save()
                    ul = request.user.administrator.license
                    ul.add_entity(entity, entity_cls)
                else:
                    form.save()
                return render(request, 'edit_ok.html')
            # TODO @iia catch by different exceptions
            except Exception as e:
                data = {'form': form, 'target': target, 'title': title}
                form.add_form_error(e)
                return render(request, 'edit_dialog.html', data)
    else:
        form = form_cls(user=request.user)
    
    data = {'form': form, 'target': target, 'title': title}
    return render(request, 'edit_dialog.html', data)

@login_required
@decorator_from_middleware(LicenseFilter)
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
            try:
                src_account.new_transfer(**form.cleaned_data)
                return render(request, 'edit_ok.html')
            # TODO @iia catch by different exceptions
            except Exception as e:
                data = {'form' : form, 'target': target, 'entity_id': account_id,
                        'building': building,
                        'title': title + ' ' + src_account.name}
                form.add_form_error(e)
                return render(request, 'edit_dialog.html', data)
    else:
        form = form_cls(account=src_account, user=request.user,
                        building=building)
    
    data = {'form' : form, 'target': target, 'entity_id': account_id,
            'building': building,
            'title': title + ' ' + src_account.name}
    return render(request, 'edit_dialog.html', data)
