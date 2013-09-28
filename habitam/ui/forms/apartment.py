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
    
Created on Apr 21, 2013

@author: Stefan Guna
'''
from django import forms
from django.db.models.query_utils import Q
from django.forms.forms import NON_FIELD_ERRORS
from django.forms.util import ErrorDict
from django.utils.translation import ugettext as _
from habitam.entities.models import ApartmentGroup, Apartment, Person
from habitam.financial.models import Account
from habitam.ui.forms.generic import NewReceipt


class EditApartmentForm(forms.ModelForm):
    name = forms.CharField(label=_('Nume'))
    floor = forms.IntegerField(label=_('Etaj'), required=False, min_value=1, max_value=50)
    inhabitance = forms.IntegerField(label=_('Locatari'), min_value=0, max_value=50)
    area = forms.IntegerField(label=_(u'Suprafață'), min_value=1, max_value=1000)
    parent = forms.ModelChoiceField(label=_('Scara'), queryset=ApartmentGroup.objects.all())
    rooms = forms.IntegerField(label=_('Camere'), min_value=1, max_value=20)
    
    def spinners(self):
        return ['floor', 'inhabitance', 'area', 'rooms']
     
    class Meta:
        model = Apartment
        fields = ('name', 'parent', 'floor', 'inhabitance', 'area', 'rooms')
    
    def __init__(self, *args, **kwargs):
        building = kwargs['building']
        user = kwargs['user']
        del kwargs['building']
        del kwargs['user']
        super(EditApartmentForm, self).__init__(*args, **kwargs)
        staircases = ApartmentGroup.objects.filter(parent=building)
        self.fields['parent'].queryset = staircases
        self.user = user
        
    
    def clean(self):
        l = self.user.administrator.license
        a = l.max_apartments - l.apartment_count()
        if self.instance.id == None and a < 1:
            raise forms.ValidationError(_('Prea multe apartamente'))
        return self.cleaned_data
    
    def add_form_error(self, error_message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(error_message)

class EditPersonForm(forms.ModelForm):
    class Meta:
        model = Person 
        
    def __init__(self, *args, **kwargs):
        if 'user' in kwargs.keys():
            del kwargs['user']
        super(EditPersonForm, self).__init__(*args, **kwargs)
   
    def add_form_error(self, error_message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(error_message)

class NewApartmentPayment(NewReceipt):
    dest_account = forms.ModelChoiceField(label=_('Cont'),
                            queryset=Account.objects.all())
    
    def __init__(self, *args, **kwargs):        
        ap = kwargs['entity']
        building = ap.building()
        super(NewApartmentPayment, self).__init__(*args, **kwargs)
        
        qdirect = Q(accountlink__holder=building)
        qparent = Q(accountlink__holder__parent=building)
        q = Account.objects.filter(qdirect | qparent).exclude(type='penalties')
        
        self.fields['dest_account'].queryset = q
        
        self.fields['receipt_payer_name'].initial = ap.owner.name
        try:
            self.fields['receipt_payer_address'].initial = building.buildingdetails.address
        except:
            pass
        self.fields['description'].initial = _(u'Plată întreținere apartament ') + ap.name
        
