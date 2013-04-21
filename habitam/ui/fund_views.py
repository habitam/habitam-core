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
from django.shortcuts import render
from habitam.entities.models import AccountLink
from habitam.services.models import Account
from habitam.ui.views import NewDocPaymentForm


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


def new_fund_transfer(request, account_id):
    src_account = Account.objects.get(pk=account_id)
    account_link = AccountLink.objects.get(account=src_account)
    building = account_link.holder.building()
    
    if request.method == 'POST':
        form = NewFundTransfer(request.POST, account=src_account,
                               building=building)
        if form.is_valid():
            dest_account = form.cleaned_data['dest_link'].account
            del form.cleaned_data['dest_link']
            src_account.new_transfer(dest_account=dest_account,
                                **form.cleaned_data)
            return render(request, 'edit_ok.html')
    else:
        form = NewFundTransfer(account=src_account, building=building)
    
    data = {'form' : form, 'target': 'new_fund_transfer',
            'entity_id': account_id, 'building': building,
            'title': 'Transfer fonduri de la ' + src_account.holder}
    return render(request, 'edit_dialog.html', data)
