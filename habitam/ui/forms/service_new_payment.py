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
from django import forms
from django.db.models.query_utils import Q
from habitam.financial.models import Account
from habitam.ui.forms.generic import NewReceipt, NewInvoice
import logging


logger = logging.getLogger(__name__)


class BasicServicePayment(NewReceipt):
    def __init__(self, *args, **kwargs):
        super(BasicServicePayment, self).__init__(*args, **kwargs)
        
        building = self.building        
        self.fields['receipt_payer_name'].initial = building.name
        try:
            self.fields['receipt_payer_address'].initial = building.buildingdetails.address
            self.fields['receipt_fiscal_id'].initial = building.buildingdetails.fiscal_id
            self.fields['receipt_registration_id'].initial = building.buildingdetails.registration_id
        except:
            pass
        self.fields['receipt_description'].initial = u'Plată serviciu'
        

class NewOtherServicePayment(BasicServicePayment, NewInvoice):
    supplier = forms.CharField(label='Furnizor')
    service = forms.CharField(label='Serviciu', max_length=100)
    
    def __init__(self, *args, **kwargs):
        self.building = kwargs['building']
        del kwargs['building']
        del kwargs['account']
        del kwargs['user']
        super(NewOtherServicePayment, self).__init__(*args, **kwargs)
        self.fields['no'].label = 'Număr chitanță'
        
        
class NewServicePayment(BasicServicePayment):
    dest_account = forms.ModelChoiceField(label='Serviciu',
                            queryset=Account.objects.all())
    
    def __init__(self, *args, **kwargs):
        self.building = kwargs['building']
        del kwargs['building']
        del kwargs['account']
        del kwargs['user']
        super(NewServicePayment, self).__init__(*args, **kwargs)
     
        qbilled_direct = Q(service__billed=self.building)
        qbilled_parent = Q(service__billed__parent=self.building)
        qgeneric_service = Q(Q(qbilled_direct | qbilled_parent))
        qnotarchived = Q(~Q(service__archived=True) & qgeneric_service)
        qnotonetime = Q(~Q(service__one_time=True) & qnotarchived)
        
        queryset = Account.objects.filter(qnotonetime)
        self.fields['dest_account'].queryset = queryset
