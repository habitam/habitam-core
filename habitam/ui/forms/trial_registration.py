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
from captcha.fields import CaptchaField
from django import forms
from django.utils.translation import ugettext as _
from registration.forms import RegistrationFormUniqueEmail


class HabitamRegistrationForm(RegistrationFormUniqueEmail):
    captcha = CaptchaField(label=_(u'Rescrieți textul'))
    
    def __init__(self, *args, **kwargs):
        super(HabitamRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget = forms.HiddenInput()
        self.fields['username'].required = False
        self.fields['password1'].label = _('Parola')
        self.fields['password2'].label = _('Parola (din nou)')
        
    def clean(self):
        cleaned_data = super(HabitamRegistrationForm, self).clean()
        if 'email' in cleaned_data.keys():
            cleaned_data['username'] = cleaned_data['email']
        return cleaned_data

