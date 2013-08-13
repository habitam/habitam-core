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
from django.forms.forms import NON_FIELD_ERRORS
from django.forms.util import ErrorDict
from habitam.entities.bootstrap_building import initial_operations
from habitam.entities.models import ApartmentGroup, BuildingDetails
from habitam.settings import MAX_CLOSE_DAY, MAX_PAYMENT_DUE_DAYS, \
    MAX_PENALTY_PER_DAY
from habitam.ui.forms.helper.all_apartments import skip_apartments, \
    drop_skip_checkboxes, all_apartments_data
from habitam.ui.widgets.bootstrap_date import BootstrapDateInput
import datetime


class EditBuildingForm(forms.ModelForm):
    address = forms.CharField(label='Adresă', required=False)
    fiscal_id = forms.CharField(label='CIF', max_length=30, required=False)
    name = forms.CharField(label='Nume')
    notes = forms.CharField(label='Observații', widget=forms.Textarea,
                            required=False)
    registration_id = forms.CharField(label='Nr.Reg.Comerțului',
                            max_length=200, required=False)

    class Meta:
        model = ApartmentGroup
        fields = ('name', 'address', 'fiscal_id', 'registration_id', 'notes')
        extra_fields = ('address', 'notes', 'fiscal_id', 'registration_id')
        
    def __init__(self, *args, **kwargs):
        if 'user' in kwargs.keys():
            del kwargs['user']
        super(EditBuildingForm, self).__init__(*args, **kwargs)
        try:
            bd = self.instance.buildingdetails
            for ef in EditBuildingForm.Meta.extra_fields:
                self.fields[ef].initial = getattr(bd, ef)
        except BuildingDetails.DoesNotExist:
            pass
    
    def add_form_error(self, error_message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(error_message)
        
    def save(self):
        b = super(EditBuildingForm, self).save()
        try:
            bd = b.buildingdetails
        except BuildingDetails.DoesNotExist:
            bd = BuildingDetails.objects.create(apartment_group=b)
        for ef in EditBuildingForm.Meta.extra_fields:
            setattr(bd, ef, self.cleaned_data[ef])
        bd.save()
        return b


class EditStaircaseForm(forms.ModelForm):
    name = forms.CharField(label='Nume')
    type = forms.CharField(label='Type',
                        widget=forms.HiddenInput())
    parent = forms.ModelChoiceField(label='Cladirea',
                        queryset=ApartmentGroup.objects.all(),
                        widget=forms.HiddenInput())
    
    class Meta:
        model = ApartmentGroup
        fields = ('name',)
        
    def __init__(self, *args, **kwargs):
        building = kwargs['building']
        del kwargs['building']
        del kwargs['user']
        
        print kwargs
        initial = {'parent': building.id,
                   'type': 'stair'}
        if kwargs.has_key('initial'):
            kwargs['initial'].update(initial)
        else:
            kwargs['initial'] = initial
        print kwargs
        super(EditStaircaseForm, self).__init__(*args, **kwargs)
        print self.fields
        
    
    def add_form_error(self, error_message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(error_message)
        

class InitialOperations(forms.Form):
    def __init__(self, *args, **kwargs):
        self.building = kwargs['building']
        del kwargs['user']
        del kwargs['building']
        
        super(InitialOperations, self).__init__(*args, **kwargs)
        for ap in self.building.apartments():
            f = forms.BooleanField(label='Fără sold inițial pentru ' + str(ap), \
                                    required=False)
            self.fields['undeclared_ap_' + str(ap.pk)] = f
            f = forms.DecimalField(label='Suma ' + str(ap), required=False)
            self.fields['sum_ap_' + str(ap.pk)] = f
            f = forms.DateField(label='Data', initial=datetime.date.today,
                        widget=BootstrapDateInput(input_format='yyyy-mm-dd'))
            self.fields['date_ap_' + str(ap.pk)] = f

    def add_form_error(self, error_message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(error_message)
            
    def clean(self):
        cleaned_data = super(InitialOperations, self).clean()
        to_skip = skip_apartments('undeclared_ap_', cleaned_data)
        sums = all_apartments_data('sum_ap_', cleaned_data)
        dates = all_apartments_data('date_ap_', cleaned_data)
        for k in to_skip:
            del(sums[k])
            del(dates[k])
       
        msg = u'Introduceți o valoare'
        for k, v in sums.iteritems():
            if not v:
                self._errors['sum_ap_' + str(k)] = self.error_class([msg])
        if not sums:
            raise forms.ValidationError(u'Nu a fost introdusă nici o valoare')
        drop_skip_checkboxes('undeclared_ap_', cleaned_data)
        
        cleaned_data['sums'] = sums
        cleaned_data['dates'] = dates
        return cleaned_data
    
    def save(self):
        initial_operations(self.building, **self.cleaned_data)
         
         
class NewBuildingForm(forms.Form):
    apartments = forms.IntegerField(label='Număr apartamente', initial=1, min_value=1,
                                    max_value=1000)
    apartment_offset = forms.IntegerField(label='Primul apartament',
                                    initial=1, min_value=1, max_value=1000)
    close_day = forms.IntegerField(label='Data închidere listă',
                                    initial=1, min_value=1,
                                    max_value=MAX_CLOSE_DAY)
    daily_penalty = forms.DecimalField(label='Penalitate (procent zilnic)',
                                    initial=MAX_PENALTY_PER_DAY, min_value=0,
                                    max_value=MAX_PENALTY_PER_DAY)
    payment_due_days = forms.IntegerField(label='Zile de scadență',
                                    initial=MAX_PAYMENT_DUE_DAYS, min_value=1,
                                    max_value=MAX_PAYMENT_DUE_DAYS)
    name = forms.CharField(label='Nume', max_length=100)
    staircases = forms.IntegerField(label='Număr scări', initial=1,
                                    min_value=1, max_value=100)

    def __init__(self, user, *args, **kwargs):
        super(NewBuildingForm, self).__init__(*args, **kwargs)
        self.user = user
        self.fields.keyOrder = ['name', 'staircases', 'apartments',
                                'apartment_offset', 'close_day',
                                'payment_due_days', 'daily_penalty']
        
    def clean(self):
        if 'apartments' in self.cleaned_data:
            l = self.user.administrator.license
            a = l.max_apartments - l.apartment_count()
            if a < self.cleaned_data['apartments']:
                raise forms.ValidationError('Prea multe apartamente')
        return self.cleaned_data

    def spinners(self):
        return ['staircases', 'apartments', 'apartment_offset', 'close_day',
                'payment_due_days', 'daily_penalty']

    
    def add_form_error(self, error_message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(error_message)
        
        
class UploadInitialOperations(forms.Form):
    file  = forms.FileField()
    
    def __init__(self, *args, **kwargs):
        self.building = kwargs['building']
        del kwargs['building']
        
        super(UploadInitialOperations, self).__init__(*args, **kwargs)

    def add_form_error(self, error_message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(error_message)