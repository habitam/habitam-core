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
    
Created on July 6, 2013

@author: Stefan Guna
'''
from decimal import Decimal
from django import forms
from django.db.models.query_utils import Q
from django.forms.fields import DecimalField
from django.forms.forms import NON_FIELD_ERRORS
from django.forms.util import ErrorDict
from habitam.entities.models import ApartmentGroup, Service, Supplier
from habitam.financial.models import Quota
from habitam.ui.forms.fund import MONEY_TYPES
import logging


logger = logging.getLogger(__name__)

class EditServiceForm(forms.ModelForm):
    supplier = forms.ModelChoiceField(label='Furnizor', queryset=Supplier.objects.all())
    name = forms.CharField(label='Nume', max_length=100)
    billed = forms.ModelChoiceField(label='Clienți', queryset=ApartmentGroup.objects.all())
    quota_type = forms.ChoiceField(label='Distribuie costuri', choices=Service.QUOTA_TYPES)
    cmd = forms.CharField(initial='save', widget=forms.HiddenInput())
    archived = forms.BooleanField(label='Arhivat', required=False)

    class Meta:
        model = Service
        fields = ('supplier', 'name', 'billed', 'quota_type', 'archived')
        
    def __init__(self, *args, **kwargs):
        building = kwargs['building']
        self.service_type = kwargs['service_type']
        self.suppliers = kwargs['suppliers']
        del kwargs['building']
        del kwargs['user']
        del kwargs['suppliers']
        del kwargs['service_type']
        
        super(EditServiceForm, self).__init__(*args, **kwargs)
        
        if len(args) > 0:
            self.__init_manual_quotas__(args)
        elif len(kwargs) > 0 and 'instance' in kwargs.keys():
            self.__init_db_quotas__(kwargs['instance'])
        
        self.fields['billed'].queryset = ApartmentGroup.objects.filter(Q(parent=building) | Q(pk=building.id))
       
        if self.suppliers == None or self.instance.pk != None:
            del self.fields['supplier']
        else:
            self.fields['supplier'].queryset = self.suppliers
        
        if self.service_type == 'collecting':
            self.fields['money_type'] = forms.ChoiceField(label='Tip bani',
                                                choices=MONEY_TYPES)
        
        if self.instance.pk == None:
            del self.fields['archived']
        

    def __init_db_quotas__(self, service):
        if service.quota_type != 'manual':
            return
        
        aps = service.billed.apartments()
        for ap in aps:
            q = Quota.objects.get(Q(src=service.account) & Q(dest=ap.account))
            self.fields['quota_ap_' + str(ap.pk)] = DecimalField(
                        label='Cota ' + str(ap), decimal_places=3,
                        max_digits=4, initial=q.ratio)
        
    def __init_manual_quotas__(self, args):
        billed = args[0].get('billed')
        qt = args[0].get('quota_type')
        if qt != 'manual' or billed == '':
            return
        
        aps = ApartmentGroup.objects.get(pk=billed).apartments()
        for ap in aps:
            self.fields['quota_ap_' + str(ap.pk)] = DecimalField(
                        label='Cota ' + str(ap), decimal_places=3, max_digits=4)

    def __validate_manual_quota__(self, cleaned_data):
        s = Decimal(0)
        for k, v in cleaned_data.items():
            if not k.startswith('quota_ap_'):
                continue
            s = s + v
        if s != Decimal(1):
            raise forms.ValidationError('Quotas do not sum to 1')
    
    def clean(self):
        cleaned_data = super(EditServiceForm, self).clean()
        if cleaned_data['quota_type'] == 'manual':
            self.__validate_manual_quota__(cleaned_data)
        if self.instance.pk == None and self.suppliers != None and \
            not 'supplier' in cleaned_data.keys():
            raise forms.ValidationError('No supplier selected')
        return cleaned_data
    
    def manual_quotas(self):
        if self.cleaned_data['quota_type'] != 'manual':
            return None
        ap_quotas = {}
        for k, v in self.cleaned_data.items():
            if not k.startswith('quota_ap_'):
                continue
            ap_quotas[int(k[len('quota_ap_'):])] = v
        return ap_quotas
    
    def refresh_ids(self):
        return ['id_quota_type', 'id_billed']
    
    def add_form_error(self, error_message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(error_message)
    
