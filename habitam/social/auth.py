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
    
Created on Sep 7, 2013

@author: Stefan Guna
'''
from django.core.mail import send_mail
from django.template.context import Context
from django.template.loader import get_template
from habitam.settings import DEFAULT_FROM_EMAIL

PROVIDERS = {
    'google-oauth2': 'Google',
}


def notify(backend, user, new_association, is_new, **kwargs):
    if not new_association:
        return None
    
    c = Context({'email': user.email, 'provider': PROVIDERS[backend.name]})
    if is_new:
        template = 'notify_new_account.txt'
    else:
        template = 'notify_association.txt'
    text_body = get_template(template).render(c)

    send_mail(u'Contul dumneavostră Habitam', text_body, DEFAULT_FROM_EMAIL,
              [user.email])
    return None
    
    
    