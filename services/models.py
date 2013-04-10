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

Created on Apr 8, 2013

@author: Stefan Guna
'''
from django.db import models



class Quota(models.Model):
    src = models.ForeignKey('Account', related_name='quota_src')
    dest = models.ForeignKey('Account', related_name='quota_dest')
    ratio = models.DecimalField(decimal_places=5, max_digits=6)
   
    @staticmethod
    def set_quota(src, dest, ratio):
        try:
            q = Quota.objects.get(src=src, dest=dest)
            q.ratio = ratio 
        except Quota.DoesNotExist:
            q = Quota.objects.create(src=src, dest=dest, ratio=ratio)
        q.save()
    
    
class OperationDoc(models.Model):
    date = models.TimeField()
    no = models.CharField(max_length=100)
    src = models.ForeignKey('Account', related_name='doc_src')
    type = models.CharField(max_length=10)
  
   
class Operation(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    doc = models.ForeignKey(OperationDoc)
    src = models.ForeignKey('Account', related_name='src')
    dest = models.ForeignKey('Account', related_name='dest')


class Account(models.Model):
    
    def __assert_doc_not_exists(self, no):
        try:
            OperationDoc.objects.get(no=no, src=self)
            raise NameError('Document already exists')
        except OperationDoc.DoesNotExist:
            pass
        
    def new_transfer(self, amount, date, no, dest_account):
        self.__assert_doc_not_exists(no)
        
        doc = OperationDoc.objects.create(date=date, no=no, src=self,
                                          type='transfer')
        Operation.objects.create(amount=amount, doc=doc, src=self, 
                                 dest=dest_account)
        self.save()
        
        
    def new_invoice(self, amount, date, no, dest_accounts):
        self.__assert_doc_not_exists(no)
        
        new_invoice = OperationDoc.objects.create(date=date, no=no,
                                                  src=self, type='invoice')
        for account in dest_accounts:
            try:
                q = Quota.objects.get(src=self, dest=account) 
            except Quota.DoesNotExist: 
                continue
            ap_amount = q.ratio * amount
            
            Operation.objects.create(amount=ap_amount, doc=new_invoice,
                                     src=self, dest=account)
        
        self.save()


    def balance(self):
        outOps = Operation.objects.filter(dest=self)
        total = 0
        for op in outOps:
            total = total + op.amount
        inOps = Operation.objects.filter(src=self)
        for op in inOps:
            total = total - op.amount
        return total
