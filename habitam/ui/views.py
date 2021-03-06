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
from django.utils.translation import ugettext as _
from habitam.downloads.display_list import download_display_list
from habitam.entities.accessor import entity_for_account, building_for_account
from habitam.entities.bootstrap_building import bootstrap_building, \
    initial_operations_template, load_initial_operations
from habitam.entities.models import ApartmentGroup, Apartment, AccountLink, \
    CollectingFund, Supplier, Service
from habitam.financial.models import Account, OperationDoc
from habitam.licensing.models import License
from habitam.ui.forms.building import NewBuildingForm, UploadInitialOperations
from habitam.ui.forms.service_new_payment import NewOtherServicePayment
from habitam.ui.license_filter import LicenseFilter, building_accessible, \
    entity_accessible
import calendar
import logging


logger = logging.getLogger(__name__)


def __pdf_response(building, month, name, f):
    wrapper = FileWrapper(f)
    response = HttpResponse(wrapper, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=' + name + building.name + '_' + month + '.pdf'
    response['Content-Length'] = f.tell()
    f.seek(0)
    
    return response


def __xlsx_response(building, name, f):
    wrapper = FileWrapper(f)
    response = HttpResponse(wrapper, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=' + name + building.name + '.xlsx'
    response['Content-Length'] = f.tell()
    f.seek(0)
    
    return response


# TODO stef: there's business logic here
def __transfer_data(building, form):
    if type(form) != NewOtherServicePayment:
        return form.cleaned_data
    
    supplier = Supplier.objects.create(name=form.cleaned_data['supplier'],
                                       one_time=True)
    service = Service(name=form.cleaned_data['service'], billed=building,
                      supplier=supplier, one_time=True,)
    service.save(account_type='std', money_type='3rd party')
    del form.cleaned_data['supplier']
    del form.cleaned_data['service']
    form.cleaned_data['dest_account'] = service.account
    return form.cleaned_data
    

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
                l = request.user.administrator.license
                building = bootstrap_building(l, **form.cleaned_data)
                url = reverse('apartment_list', args=[building.id])
                data = {'location': url}
                return render(request, 'edit_redirect.html', data)
            # TODO @iia catch by different exceptions
            except Exception as e:
                data = {'form': form, 'target': 'new_building',
                        'title': u'Clădire nouă'}
                logger.exception('Cannot save new building')  
                form.add_form_error(e)
                return render(request, 'edit_dialog.html', data)
    else:
        form = NewBuildingForm(request.user) 
    data = {'form': form, 'target': 'new_building', 'title': _(u'Clădire nouă')}
    return render(request, 'edit_dialog.html', data)


@login_required
@decorator_from_middleware(LicenseFilter)
def building_tab(request, building_id, tab, show_all=False):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    building_accessible(request, building)
    data = {'building': building, 'active_tab': tab, 'show_all': show_all}
    return render(request, tab + '.html', data)  


@login_required
@decorator_from_middleware(LicenseFilter)
def download_initial_operations_template(request, building_id):
    building = ApartmentGroup.objects.get(pk=building_id)
    building_accessible(request, building, True)
    temp = initial_operations_template(building)
    return __xlsx_response(building, 'solduri_initiale_', temp)


@login_required
@decorator_from_middleware(LicenseFilter)
def download_list(request, building_id, month):
    building = ApartmentGroup.objects.get(pk=building_id)
    building_accessible(request, building, True)
    begin_ts = datetime.strptime(month + '-%02d' % building.close_day,
                                  "%Y-%m-%d").date()
    end_ts = begin_ts + relativedelta(months=1) 
    l = request.user.administrator.license
    l.validate_month(building, begin_ts)
   
    building.mark_display(begin_ts) 

    temp = download_display_list(building, begin_ts, end_ts)
    return __pdf_response(building, month, 'lista', temp)


@login_required
@decorator_from_middleware(LicenseFilter)
def download_report(request, generator, name, building_id, month):
    building = ApartmentGroup.objects.get(pk=building_id)
    building_accessible(request, building, True)
    if month == None:
        day = date.today()
        month = str(day.month)
    else:
        day = datetime.strptime(month + '-01', '%Y-%m-%d').date()
        last = calendar.monthrange(day.year, day.month)[1]
        day = date(year=day.year, month=day.month, day=last)
   
    l = request.user.administrator.license
    l.validate_month(building, day)
    
    temp = generator(building, day)
    return __pdf_response(building, month, name, temp)


@login_required
@decorator_from_middleware(LicenseFilter)
def form_view(request, view_name, form_class, template_name, success_view):
    if request.method == 'POST':
        form = form_class(request.user, request.POST)
        if form.is_valid():
            try:
                form.save()
                return redirect(success_view)
            # TODO @iia catch by different exceptions
            except Exception as e:
                data = {'form': form, 'target': view_name}  
                form.add_form_error(e)
                return render(request, template_name, data)
    else:
        form = form_class(request.user) 

    data = {'form': form, 'target': view_name}
    return render(request, template_name, data)


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
    building_accessible(request, building)
    if month == None:
        today = date.today()
        month = date(day=building.close_day, month=today.month,
                     year=today.year)
    else:
        month = datetime.strptime(month + '-%02d' % building.close_day,
                                  "%Y-%m-%d").date()
    
    l = License.for_building(building)
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
    building = ApartmentGroup.objects.get(pk=building_id)
    building_accessible(request, building, True)
    OperationDoc.delete_doc(operationdoc_id)
    return redirect('operation_list', building_id=building_id,
                    account_id=account_id)


@login_required
@decorator_from_middleware(LicenseFilter)
def edit_entity(request, entity_id, entity_cls, form_cls, target, title='Entity'):
    entity = entity_cls.objects.get(pk=entity_id)
    building = entity.building()
    building_accessible(request, building, True)
    
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
                logger.exception('Cannot save entity')
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
    entity_accessible(request, entity_cls, entity, True)
    
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
                logger.exception('Cannot save entity')
                form.add_form_error(e)

                return render(request, 'edit_dialog.html', data)
    else:
        form = form_cls(instance=entity, user=request.user)
    
    data = {'form': form, 'target': target, 'entity_id': entity_id,
            'title': title + ' ' + entity.name}
    return render(request, 'edit_dialog.html', data)


@login_required
@decorator_from_middleware(LicenseFilter)
def entity_view(request, entity_cls, entity_id, edit_name, view_name,
                template_name='entity_view.html', template_entity='entity',
                extra_data=None):
    entity = entity_cls.objects.get(id=entity_id)
    entity_accessible(request, entity_cls, entity)
    data = {template_entity: entity, 'entity_cls': entity_cls,
            'edit_name': edit_name, 'view_name': view_name}
    if extra_data != None:
        data.update(extra_data)
    return render(request, template_name, data)
       

@login_required
@decorator_from_middleware(LicenseFilter)
def new_building_entity(request, building_id, form_cls, target,
                        title='New Entity', save_kwargs=None,
                        commit_directly=False):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    building_accessible(request, building, True)
    
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
                logger.exception('Cannot save building entity')
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
    building_accessible(request, building, True)
    
    if request.method == 'POST':
        form = form_cls(request.POST, entity=entity)
        if form.is_valid() and ('cmd' not in form.cleaned_data or form.cleaned_data['cmd'] == 'save'):
            try:
                if 'cmd' in form.cleaned_data:
                    del form.cleaned_data['cmd']
                entity.new_inbound_operation(**form.cleaned_data)
            except Exception as e:
                data = {'form': form, 'target': target, 'parent_id': entity_id,
                        'building': building, 'title': title + ' ' + entity.name}
                logger.exception('Cannot save inbound operation')
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
                logger.exception('Cannot save entity')
                form.add_form_error(e)
    else:
        form = form_cls(user=request.user)
    
    data = {'form': form, 'target': target, 'title': title}
    return render(request, 'edit_dialog.html', data)

@login_required
@decorator_from_middleware(LicenseFilter)
def new_transfer(request, account_id, form_cls, target, title):
    src_account = Account.objects.get(pk=account_id)
    try:
        account_link = AccountLink.objects.get(account=src_account)
        building = account_link.holder.building()
    except AccountLink.DoesNotExist:
        collecting_fund = CollectingFund.objects.get(account=src_account)
        building = collecting_fund.building()
    building_accessible(request, building, True)
    
    if request.method == 'POST':
        form = form_cls(request.POST, account=src_account,
                               user=request.user, building=building)
        if form.is_valid():
            try:
                data = __transfer_data(building, form)
                src_account.new_transfer(**data)
                return render(request, 'edit_ok.html')
            # TODO @iia catch by different exceptions
            except Exception as e:
                data = {'form' : form, 'target': target, 'entity_id': account_id,
                        'building': building,
                        'title': title + ' ' + src_account.name}
                logger.exception('Cannot save transfer')
                form.add_form_error(e)
                return render(request, 'edit_dialog.html', data)
    else:
        form = form_cls(account=src_account, user=request.user,
                        building=building)
    
    data = {'form' : form, 'target': target, 'entity_id': account_id,
            'building': building,
            'title': title + ' ' + src_account.name}
    return render(request, 'edit_dialog.html', data)



@login_required
@decorator_from_middleware(LicenseFilter)
def upload_initial_operations(request, building_id):
    building = ApartmentGroup.objects.get(pk=building_id)
    building_accessible(request, building, True)
    
    if request.method == 'POST':
        form = UploadInitialOperations(request.POST, request.FILES, building=building)
        if form.is_valid():
            try:
                load_initial_operations(building, request.FILES['file'])
                return render(request, 'edit_ok.html')
            except Exception as e:
                logger.exception('Cannot upload initial operations')
                form.add_form_error(e)
    else:
        form = UploadInitialOperations(building=building)
    data = {'form': form, 'building': building}
    return render(request, 'upload_initial_operations.html', data)
    
    
    
