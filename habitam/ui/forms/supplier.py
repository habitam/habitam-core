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

Created on Jun 6, 2013

@author: stefan
'''
from django import forms
from habitam.entities.models import Supplier
from django.forms.util import ErrorDict
from django.forms.forms import NON_FIELD_ERRORS 

class EditSupplierForm(forms.ModelForm):
    name = forms.CharField(label='Nume')
    archived = forms.BooleanField(label='Arhivat', required=False)

    class Meta:
        model = Supplier 
        fields = ('name', 'archived')
        
    def __init__(self, *args, **kwargs):
        if 'user' in kwargs.keys():
            self._user = kwargs['user']
            del kwargs['user']
        else:
            self._user = None  
        super(EditSupplierForm, self).__init__(*args, **kwargs)
     
        if self.instance.pk == None or not self.instance.is_archivable():
            del self.fields['archived']
            
    def clean(self):
        if self._user is None:
            return self.cleaned_data
        if 'name' in self.cleaned_data:
            slist=self._user.administrator.license.suppliers
            n=self.cleaned_data['name']
            for ss in slist.all():
                if ss.name==n:
                    raise forms.ValidationError('Numele %s mai exista in lista de furnizori'%(n))
        return self.cleaned_data
    
    def add_form_error(self, error_message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(error_message)