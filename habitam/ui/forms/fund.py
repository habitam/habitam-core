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
from habitam.ui.forms.generic import NewDocPaymentForm


class NewFundTransfer(NewDocPaymentForm):
    dest_link = forms.ModelChoiceField(label='Fond',
                            queryset=AccountLink.objects.all())
    
    def __init__(self, *args, **kwargs):
        building = kwargs['building']
        account = kwargs['account']
        del kwargs['building']
        del kwargs['account']
        super(NewFundTransfer, self).__init__(*args, **kwargs)
        queryset = AccountLink.objects.filter(~Q(account=account) & Q(
                            Q(holder=building) | Q(holder__parent=building)))
        self.fields['dest_link'].queryset = queryset
