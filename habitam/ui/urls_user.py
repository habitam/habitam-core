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
from django.conf.urls import patterns, url
from django.views.generic.base import TemplateView
from habitam.settings import TRIAL_LICENSE
from habitam.ui.forms.trial_registration import HabitamRegistrationForm
from habitam.ui.registration_views import TrialRegistrationView, \
    TrialActivationView, trial_request
    
urlpatterns = patterns('',
    url(r'^users/login/$', 'django.contrib.auth.views.login',
        {'template_name': 'login.html'}, 'login'),
    url(r'^users/logout/$', 'django.contrib.auth.views.logout',
        {'template_name': 'logout.html'}, 'logout'),
    url(r'^users/password/$', 'django.contrib.auth.views.password_change',
        {'template_name': 'password_change.html'}, 'password_change'),
    url(r'^users/password/done$', 'django.contrib.auth.views.password_change_done',
        {'template_name': 'password_change_complete.html'}, 'password_change_done'),
    url(r'^users/reset/$', 'django.contrib.auth.views.password_reset',
        {'template_name': 'password_reset.html',
         'email_template_name': 'password_reset_email.txt',
         'subject_template_name': 'password_reset_subject.txt'},
        name='password_reset'),
    url(r'^users/reset/done/$', 'django.contrib.auth.views.password_reset_done',
        {'template_name': 'password_reset_done.html'},
        name='password_reset_done'),
    url(r'^users/reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        'django.contrib.auth.views.password_reset_confirm',
        {'template_name': 'password_reset_confirm.html'},
        name='password_reset_confirm'),
    url(r'^users/reset/complete/$',
        'django.contrib.auth.views.password_reset_complete',
        {'template_name': 'password_reset_complete.html'},
        name='password_reset_complete'),
    url(r'^users/license_expired/$',
        TemplateView.as_view(template_name='license_expired.html'),
        name='license_expired'),
                       
    url(r'^users/register/$', TrialRegistrationView.as_view(
            form_class=HabitamRegistrationForm),
        name='registration'),
    url(r'^users/register/disallowed$', TemplateView.as_view(
            template_name='registration/registration_disallowed.html'),
        name='registration_disallowed'),
    url(r'^users/register/complete$', TemplateView.as_view(
            template_name='registration/registration_success.html'),
        name='registration_complete'),
    
    url(r'^users/activate/do/(?P<activation_key>.+)$$', TrialActivationView.as_view(
            template_name='registration/registration.html'),
        name='registration_activate'),
    url(r'^users/activate/complete$', TemplateView.as_view(
            template_name='registration/registration_activation_complete.html'),
        name='registration_activation_complete'),
                       
    url(r'^users/trial_request$', trial_request, name='trial_request'),
)
