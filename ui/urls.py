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
from django.conf.urls import patterns, url
from ui import views


urlpatterns = patterns('',
    url(r'^new_building$', views.new_building, name='new_building'),
    
    url(r'^services/(?P<billed_id>\d+)/new_service$', views.new_service, name='new_service'),
    url(r'^buildings/(?P<building_id>\d+)/apartment_list$', views.apartment_list, name='apartment_list'),

    url(r'^apartments/(?P<building_id>\d+)/(?P<apartment_id>\d+)/edit$', views.edit_apartment, name='edit_apartment'),
)
