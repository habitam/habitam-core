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


class EditAccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('name',)
    
    def __init__(self, *args, **kwargs):
        if 'building' in kwargs.keys():
            self._building = kwargs['building']
            del kwargs['building']
            del kwargs['user']
        else:
            self._building = None
        super(EditAccountForm, self).__init__(*args, **kwargs)
        
    def save(self, commit=True):
        instance = super(EditAccountForm, self).save(commit=False)
        if commit:
            instance.save()
            if self._building != None:
                al = AccountLink.objects.create(holder=self._building,
                                                account=instance)
                al.save()
        
        return instance


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
        
        qbilled_direct = Q(service__billed=building)
        qbilled_parent = Q(service__billed__parent=building)
        qcollecting= Q(Q(service__service_type='collecting') & 
                             Q(qbilled_direct | qbilled_parent))
        qnotarchived = Q(~Q(service__archived=True) & qcollecting)
        
        queryset = Account.objects.filter(Q(qbuilding_accounts | qnotarchived))
        queryset = queryset.exclude(pk=account.id)
        self.fields['dest_account'].queryset = queryset
