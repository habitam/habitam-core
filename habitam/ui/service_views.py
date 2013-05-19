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
from django.shortcuts import render
from habitam.entities.models import ApartmentGroup
from habitam.ui.forms.service import EditServiceForm
from habitam.ui.views import license_valid


def __save_new_service(request, form):
    entity = form.save(commit=False)
    ap_quotas = form.manual_quotas()
    kwargs = {}
    if ap_quotas != None:
        kwargs['ap_quotas'] = ap_quotas
    print kwargs
    entity.save(**kwargs)
    return render(request, 'edit_ok.html')


@login_required
@user_passes_test(license_valid)
def new_service(request, building_id, save_kwargs=None):
    target = 'new_service'
    title = 'Serviciu nou'
    building = ApartmentGroup.objects.get(pk=building_id).building()
    
    if request.method == 'POST':
        form = EditServiceForm(request.POST, user=request.user, building=building)
        if form.is_valid() and form.cleaned_data['cmd'] == 'save':
            return __save_new_service(request, form)
    else:
        form = EditServiceForm(user=request.user, building=building)
    
    refresh_ids = ['id_quota_type', 'id_billed']
    data = {'form': form, 'target': target, 'parent_id': building_id,
            'building': building, 'title': title, 'refresh_ids': refresh_ids }
    return render(request, 'edit_dialog.html', data)
