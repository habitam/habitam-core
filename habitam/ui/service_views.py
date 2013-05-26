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
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http.response import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from habitam.entities.models import ApartmentGroup, Service
from habitam.ui.forms.service import EditServiceForm
from habitam.ui.views import license_valid


def __save_service(request, form, service_type=None):
    service = form.save(commit=False)
    ap_quotas = form.manual_quotas()
    kwargs = {}
    if ap_quotas != None:
        kwargs['ap_quotas'] = ap_quotas
    if service_type != None:
        service.service_type = service_type
    service.save(**kwargs)
    return render(request, 'edit_ok.html')


@login_required
@user_passes_test(license_valid)
def edit_service(request, entity_id):
    service = Service.objects.get(pk=entity_id)
    building = service.building()
    
    if request.method == 'DELETE':
        if service.can_delete():
            service.delete()
            return HttpResponse()
        else:
            return HttpResponseBadRequest()
    
    if request.method == 'POST':
        form = EditServiceForm(request.POST, user=request.user,
                        building=building, instance=service)
        if form.is_valid() and form.cleaned_data['cmd'] == 'save':
            return __save_service(request, form)
    else:
        form = EditServiceForm(user=request.user, building=building,
                               instance=service)
    
    refresh_ids = ['id_quota_type', 'id_billed']
    if service.service_type == 'general':
        title = 'Serviciu '
    else:
        title = 'Fond '
    data = {'form': form, 'target': 'edit_service', 'entity_id': entity_id,
            'building': building, 'title': title + service.name,
            'refresh_ids': refresh_ids}
    return render(request, 'edit_dialog.html', data)


@login_required
@user_passes_test(license_valid)
def new_service(request, building_id, service_type, save_kwargs=None):
    building = ApartmentGroup.objects.get(pk=building_id).building()
    
    if request.method == 'POST':
        form = EditServiceForm(request.POST, user=request.user, building=building)
        if form.is_valid() and form.cleaned_data['cmd'] == 'save':
            return __save_service(request, form, service_type)
    else:
        form = EditServiceForm(user=request.user, building=building)
    
    refresh_ids = ['id_quota_type', 'id_billed']
    if service_type == 'general':
        title = 'Serviciu nou'
    else:
        title = 'Fond nou'
    data = {'form': form, 'target': 'new_service_' + service_type,
            'parent_id': building_id, 'building': building,
            'title': title, 'refresh_ids': refresh_ids }
    return render(request, 'edit_dialog.html', data)
