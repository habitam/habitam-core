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

Created on May 19, 2013

@author: Stefan Guna
'''
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils.decorators import decorator_from_middleware
from habitam.entities.models import ApartmentGroup
from habitam.ui.license_filter import LicenseFilter, building_accessible


def __save_service(request, form):
    billable = form.save(commit=False)
    ap_quotas = form.manual_quotas()
    kwargs = {}
    if ap_quotas != None:
        kwargs['ap_quotas'] = ap_quotas
    kwargs['money_type'] = form.cleaned_data['money_type']
    kwargs['account_type'] = form.cleaned_data['account_type']
    billable.save(**kwargs)
    return render(request, 'edit_ok.html')


@login_required
@decorator_from_middleware(LicenseFilter)
def edit_billable(request, entity_id, form_class):
    entity = form_class.Meta.model.objects.get(pk=entity_id)
    building = entity.building()
    user_license = request.user.administrator.license 
    
    if request.method == 'DELETE':
        if entity.can_delete():
            entity.delete()
            return HttpResponse()
        else:
            return HttpResponseBadRequest()
    
    if request.method == 'POST':
        form = form_class(request.POST, user=request.user,
                        building=building, instance=entity,
                        user_license=user_license)
        if form.is_valid() and form.cleaned_data['cmd'] == 'save':
            return __save_service(request, form)
    else:
        form = form_class(user=request.user, building=building,
                               instance=entity, user_license=user_license)
    

    data = {'form': form, 'target': 'edit_billable_' + form_class.target(),
            'entity_id': entity_id, 'building': building,
            'title': form_class.title() + ' ' + entity.name}
    return render(request, 'edit_dialog.html', data)


@login_required
@decorator_from_middleware(LicenseFilter)
def new_billable(request, building_id, form_class, save_kwargs=None):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    building_accessible(request, building, True)
    user_license = request.user.administrator.license 
    
    if request.method == 'POST':
        form = form_class(request.POST, user=request.user,
                               building=building, user_license=user_license)
        if form.is_valid() and form.cleaned_data['cmd'] == 'save':
            return __save_service(request, form)
    else:
        form = form_class(user=request.user, building=building,
                            user_license=user_license)
    
    data = {'form': form, 'target': 'new_billable_' + form_class.target(),
            'parent_id': building_id, 'building': building,
            'title': form_class.new_title()}
    return render(request, 'edit_dialog.html', data)
