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
    
Created on Jul 15, 2013

@author: Stefan Guna
'''
from django.db import models
from habitam.financial.models import Account
import logging

logger = logging.getLogger(__name__)

    
class Entity(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True 


class SingleAccountEntity(Entity):   
    account = models.ForeignKey(Account)
    
    def __init__(self, account_type, money_type, *args, **kwargs):
        if 'name' in kwargs.keys():
            account = Account.objects.create(name=kwargs['name'],
                                             type=account_type,
                                             money_type=money_type)
            kwargs.setdefault('account', account)
        super(SingleAccountEntity, self).__init__(*args, **kwargs)

    def balance(self, month):
        return self.account.balance(month)

    class Meta:
        abstract = True
        
    def save(self, account_type, money_type, **kwargs):
        try:
            self.account.name = self.__unicode__()
            self.account.type = account_type
            self.account.money_type = money_type
            self.account.save()
        except Account.DoesNotExist:
            self.account = Account.objects.create(name=self.__unicode__(),
                                                  type=account_type,
                                                  money_type=money_type)
        
        self.account.name = self.name
        self.account.type = account_type
        self.account.money_type = money_type        
        super(SingleAccountEntity, self).save(**kwargs)

