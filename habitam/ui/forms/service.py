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
from habitam.entities.models import ApartmentGroup, Service
from habitam.ui.forms.generic import NewDocPaymentForm
import logging


logger = logging.getLogger(__name__)


class EditServiceForm(forms.ModelForm):
    name = forms.CharField(label='Nume', max_length=100)
    billed = forms.ModelChoiceField(label='Clienți', queryset=ApartmentGroup.objects.all())
    quota_type = forms.ChoiceField(label='Distribuie cota', choices=Service.QUOTA_TYPES)

    class Meta:
        model = Service
        fields = ('name', 'billed', 'quota_type')
        
    def __init__(self, *args, **kwargs):
        building = kwargs['building']
        del kwargs['building']
        super(EditServiceForm, self).__init__(*args, **kwargs)
        self.fields['billed'].queryset = ApartmentGroup.objects.filter(Q(parent=building) | Q(pk=building.id))
   

class NewServicePayment(NewDocPaymentForm):
    service = forms.ModelChoiceField(label='Serviciu', queryset=Service.objects.all())
    
    
    def __init__(self, *args, **kwargs):
        building = kwargs['building']
        del kwargs['building']
        del kwargs['account']
        super(NewServicePayment, self).__init__(*args, **kwargs)
        queryset = Service.objects.filter(
                            Q(billed=building) | Q(billed__parent=building))
        self.fields['service'].queryset = queryset
