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
    
Created on Aug 31, 2013

@author: Stefan Guna
'''
from django.shortcuts import render
from django.views.generic.base import View
from habitam.entities.models import ApartmentGroup

class SubmitPaymentView(View):
    template_name = 'submit_payment.html'
    
    def post(self, *args, **kwargs):
        building = ApartmentGroup.objects.get(pk=kwargs['building_id'])
        return render(self.request, self.template_name, {'building': building})
