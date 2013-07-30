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
    
Created on Jul 28, 2013

@author: Stefan Guna
'''
from django import forms
from django.core.mail.message import EmailMessage
from django.forms.forms import NON_FIELD_ERRORS
from django.forms.util import ErrorDict
from habitam.settings import CONTACT_EMAIL, SENDER
import logging


logger = logging.getLogger(__name__)


class ContactForm(forms.Form):
    subject = forms.CharField(label='Subiect', max_length=100)
    message = forms.CharField(label='Mesaj', widget=forms.Textarea)
    cc_myself = forms.BooleanField(label='Trimite-mi o copie', required=False)
    
    def __init__(self, user=None, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self._user = user
        
    def add_form_error(self, error_message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(error_message)
    
    def save(self, fail_silently=False):
        cc = [self._user.email] if self.cleaned_data['cc_myself'] else None
        subject = 'CONTACT: ' + self.cleaned_data['subject']
        body = self.cleaned_data['message']
            
        email = EmailMessage(from_email=self._user.email, subject=subject,
                             body=body, to=[CONTACT_EMAIL], cc=cc,
                             headers={'Reply-To': self._user.email,
                                'Sender': SENDER})
        
        email.send(fail_silently=fail_silently)
        logger.info('Send mail to %s from %s' % 
                    (CONTACT_EMAIL, self._user.email))
