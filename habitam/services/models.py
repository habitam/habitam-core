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
from decimal import Decimal
from django.db import models
from django.db.models.aggregates import Sum
from random import choice
import logging


logger = logging.getLogger(__name__)


class Quota(models.Model):
    src = models.ForeignKey('Account', related_name='quota_src')
    dest = models.ForeignKey('Account', related_name='quota_dest')
    ratio = models.DecimalField(decimal_places=5, max_digits=6)

    @staticmethod
    def del_quota(src):
        Quota.objects.filter(src=src).delete() 
        
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
    src = models.ForeignKey('Account', related_name='doc_src_set')
    billed = models.ForeignKey('Account', related_name='doc_billed_set')
    type = models.CharField(max_length=10)
  
   
class Operation(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    doc = models.ForeignKey(OperationDoc)
    dest = models.ForeignKey('Account', related_name='operation_dest_set')


class Account(models.Model):
    holder = models.CharField(max_length=100)
    
    def __assert_doc_not_exists(self, no):
        try:
            OperationDoc.objects.get(no=no, src=self)
            raise NameError('Document already exists')
        except OperationDoc.DoesNotExist:
            pass
    
    def balance(self):
        ops = self.operation_list()
        bsign = lambda y: -1 if y.src == self else 1
        amount = lambda y: y.total_amount if y.total_amount != None else 0
        bsum = lambda x, y: x + bsign(y) * amount(y)
        return reduce(bsum, ops, 0)
                   
    def new_transfer(self, amount, date, no, dest_account):
        self.__assert_doc_not_exists(no)
        
        doc = OperationDoc.objects.create(date=date, no=no, src=self,
                                          type='transfer')
        Operation.objects.create(amount=amount, doc=doc, src=self,
                                 dest=dest_account)
        self.save()
        
    def new_invoice(self, amount, date, no, billed, dest_accounts):
        self.__assert_doc_not_exists(no)
        
        new_invoice = OperationDoc.objects.create(date=date, no=no,
                            billed=billed, src=self, type='invoice')
        
        quotas = Quota.objects.filter(src=self)
        eps = Decimal('0.01')
        sum_fun = lambda x, q: x + Decimal(q.ratio * amount).quantize(eps)
        qsum = reduce(sum_fun, quotas, 0)
        if qsum != amount:
            remainder = qsum - amount
            remainder_quota = choice(quotas)
        
        for q in quotas:
            q_amount = q.ratio * amount
            if remainder_quota != None and remainder_quota == q:
                logger.info('Selecting %s for a remainder of %f', q.dest,
                            remainder)
                q_amount = q_amount - remainder
            
            Operation.objects.create(amount=q_amount, doc=new_invoice,
                                     dest=q.dest)
        
        self.save()
        
    def operation_list(self):
        docs_src = self.doc_src_set.annotate(
                    total_amount=Sum('operation__amount')).order_by('-date')
        docs_dest = OperationDoc.objects.filter(operation__dest=self).annotate(
                    total_amount=Sum('operation__amount')).order_by('-date')
        docs = []
        docs.extend(docs_src)
        docs.extend(docs_dest)
        docs.sort(cmp=lambda x, y: cmp(x.date, y.date), reverse=True)
        return docs

