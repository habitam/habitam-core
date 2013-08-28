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

from datetime import date
from django.http.response import Http404
from django.shortcuts import redirect
from habitam.licensing.models import Administrator, License

def _license_valid(user):
    l = user.administrator.license
    return date.today() < l.valid_until


def building_accessible(request, building, enforce_admin=False):
    try:
        l = request.user.administrator.license
        if l.buildings.filter(pk=building.id):
            return
        if enforce_admin:
            raise Http404
    except Administrator.DoesNotExist:
        if enforce_admin:
            raise Http404
    if not building.owned_apartments(request.user.email):
        raise Http404
    

def entity_accessible(request, entity_cls, entity, enforce_admin=False):
    try:
        l = request.user.administrator.license
        qs = getattr(l, entity_cls.LicenseMeta.license_collection)()
        if qs.filter(pk=entity.id):
            return
        if enforce_admin:
            raise Http404
    except Administrator.DoesNotExist:
        if enforce_admin:
            raise Http404
    
    l = getattr(License, entity_cls.LicenseMeta.license_accessor)(entity)
    buildings = l.available_buildings()
    for building in buildings:
        if  building.owned_apartments(request.user.email):
            return
    raise Http404
    

class LicenseFilter(object):
    def process_request(self, request):
        try:
            if _license_valid(request.user):
                return None
        except:
            if request.method == 'GET':
                return None
        return redirect('license_expired')
    