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

class EditSupplierForm(forms.ModelForm):
    name = forms.CharField(label='Nume')
    archived = forms.BooleanField(label='Arhivat', required=False)

    class Meta:
        model = Supplier 
        fields = ('name', 'archived')
        
    def __init__(self, *args, **kwargs):
        super(EditSupplierForm, self).__init__(*args, **kwargs)
        if self.instance.pk == None or not self.instance.is_archivable():
            del self.fields['archived']