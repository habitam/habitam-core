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

Created on Jun 6, 2013

@author: stefan
'''
from django import forms
from django.forms.forms import NON_FIELD_ERRORS
from django.forms.util import ErrorDict
from django.utils.translation import ugettext as _
from habitam.entities.bootstrap_suppliers import remaining_suppliers
from habitam.entities.models import Supplier

class EditSupplierForm(forms.ModelForm):
    address = forms.CharField(label=_('Adresa'), max_length=200, required=False)
    archived = forms.BooleanField(label=_('Arhivat'), required=False)
    bank = forms.CharField(label=_('Banca'), max_length=30, required=False)
    county = forms.CharField(label=_(u'Județ'), max_length=30, required=False)
    fiscal_id = forms.CharField(label=_(u'Nr. înregistrare fiscală'), max_length=30, required=False)
    iban = forms.CharField(label=_('IBAN'), max_length=30, required=False)
    legal_representative = forms.CharField(label=_('Reprezentant legal'), max_length=200, required=False)
    name = forms.CharField(label=_('Nume'))   
    registration_id = forms.CharField(label=_(u'Nr. registrul comerțului'), max_length=30, required=False)

    class Meta:
        model = Supplier 
        fields = ('name', 'address', 'county', 'legal_representative', 'bank',
                  'iban', 'fiscal_id', 'registration_id', 'archived')    
        
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
            slist = self._user.administrator.license.suppliers
            n = self.cleaned_data['name']
            if self.instance.pk == None:
                for ss in slist.all():
                    if ss.name == n:
                        raise forms.ValidationError(_('Numele %s mai exista in lista de furnizori') % (n))
        return self.cleaned_data
    
    def add_form_error(self, error_message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(error_message)


class SelectSuppliersForm(forms.Form):
    suppliers = forms.MultipleChoiceField(label=_(u'Alege unul sau mai mulți furnizori:'), widget=forms.CheckboxSelectMultiple)

    def __init__(self, existing_suppliers, *args, **kwargs):
        super(SelectSuppliersForm, self).__init__(*args, **kwargs)
        self.fields['suppliers'].choices = remaining_suppliers(existing_suppliers)
    
    def add_form_error(self, error_message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(error_message)
