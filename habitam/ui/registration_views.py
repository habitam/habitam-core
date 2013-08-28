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
    
Created on Aug 3, 2013

@author: Stefan Guna
'''
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from habitam.licensing.trial_license import register_trial
from habitam.settings import TRIAL_LICENSE
from registration.backends.default.views import RegistrationView, ActivationView


@login_required
def trial_request(request):
    data = {}
    data.update(TRIAL_LICENSE)
    if request.method == 'POST':
        try:
            register_trial(request.user)
        except Exception as e:
            data['form_error'] = e
            return render(request, 'registration/trial_request.html', data)
        return render(request, 'edit_ok.html')
    return render(request, 'registration/trial_request.html', data)     
    

class TrialActivationView(ActivationView):
    def activate(self, request, activation_key):
        user = super(TrialActivationView, self).activate(request, activation_key)
        return user


class TrialRegistrationView(RegistrationView):
    def registration_allowed(self, request):
        return not request.user.is_authenticated()
