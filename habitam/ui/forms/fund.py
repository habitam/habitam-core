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
from habitam.entities.models import AccountLink
from habitam.financial.models import Account
from habitam.ui.forms.generic import NewDocPaymentForm
from django.forms.util import ErrorDict
from django.forms.forms import NON_FIELD_ERRORS 


MONEY_TYPES = (
    ('cash', 'bani lichizi'),
    ('bank', 'bancă')
)
TYPES = (
    ('std', 'standard'),
    ('repairs', 'repairs'),
    ('rulment', 'rulment'),
    ('special', 'special'),
)

class EditAccountForm(forms.ModelForm):
    money_type = forms.ChoiceField(label='Tip bani', choices=MONEY_TYPES)
    type = forms.ChoiceField(label='Tip', choices=TYPES)
    
    class Meta:
        model = Account
        fields = ('name', 'type', 'money_type')
    
    def __init__(self, *args, **kwargs):
        if 'building' in kwargs.keys():
            self._building = kwargs['building']
            del kwargs['building']
        else:
            self._building = None
        del kwargs['user']
        super(EditAccountForm, self).__init__(*args, **kwargs)
        if self.instance.type == 'penalties':
            del self.fields['type']
        
    def save(self, commit=True):
        instance = super(EditAccountForm, self).save(commit=False)
        if commit:
            instance.save()
            if self._building != None:
                al = AccountLink.objects.create(holder=self._building,
                                                account=instance)
                al.save()
        
        return instance
    
    def add_form_error(self, error_message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(error_message)


class NewFundTransfer(NewDocPaymentForm):
    dest_account = forms.ModelChoiceField(label='Fond',
                            queryset=Account.objects.all())
    
    def __init__(self, *args, **kwargs):
        building = kwargs['building']
        account = kwargs['account']
        del kwargs['building']
        del kwargs['account']
        del kwargs['user']
        super(NewFundTransfer, self).__init__(*args, **kwargs)
        
        qdirect = Q(accountlink__holder=building)
        qparent = Q(accountlink__holder__parent=building)
        qbuilding_accounts = Q(qdirect | qparent)
        
        qbilled_direct = Q(collectingfund__billed=building)
        qbilled_parent = Q(collectingfund__billed__parent=building)
        qbilled = Q(qbilled_direct | qbilled_parent)
        qnotarchived = Q(~Q(service__archived=True) & qbilled)
        
        queryset = Account.objects.filter(Q(qbuilding_accounts | qnotarchived))
        queryset = queryset.exclude(pk=account.id)
        self.fields['dest_account'].queryset = queryset
