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
from django.db.models.query_utils import Q
from django.utils import timezone
from habitam.settings import EPS
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
    date = models.DateTimeField()
    no = models.CharField(max_length=100) # invoice number used for fiscal stuff
    src = models.ForeignKey('Account', related_name='doc_src_set')
    billed = models.ForeignKey('Account', related_name='doc_billed_set')
    type = models.CharField(max_length=10)

    UNIT_TYPES = (
                  ('none', ''),
                  ('kw','KW'),
                  ('mc', 'mc'),
                  ('kwh','KWh')
                  )
       
       
    vat = models.DecimalField(decimal_places=2, max_digits=4, default=24)
    issue_date = models.DateField()
    due_date = models.DateField()
    
    document_id = models.CharField(max_length=100, null=True) # some invoices have special id for electronic payment 
    
    start_service_date = models.DateField(null=True)
    end_service_date = models.DateField(null=True)
    
    quantity = models.DecimalField(decimal_places=2, max_digits=8, null=True)
    unit_type = models.CharField(null=True, max_length=15, choices=UNIT_TYPES)
    
    @classmethod
    def delete_doc(cls, op_id):
        OperationDoc.objects.get(pk=op_id).delete()
    
    def penalties(self):
        penalty_ops = self.operation_set.filter(dest__type='penalties').aggregate(total_amount=Sum('amount'))
        return penalty_ops['total_amount']
  
   
class Operation(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    loss = models.DecimalField(max_digits=10, decimal_places=2, blank=True,
                               null=True)
    doc = models.ForeignKey(OperationDoc)
    dest = models.ForeignKey('Account', related_name='operation_dest_set')


class Account(models.Model):
    TYPES = (
        ('apart', 'apartment'),
        ('std', 'standard'),
        ('penalties', 'penalties')
    )
    name = models.CharField(max_length=100)
    type = models.CharField(default='std', max_length=10, choices=TYPES) 
    
    def __assert_doc_not_exists(self, no):
        try:
            OperationDoc.objects.get(no=no, src=self)
            raise NameError('Document already exists')
        except OperationDoc.DoesNotExist:
            pass
        
    def __unicode__(self):
        if self.type == 'penalties':
            return self.name + ' (penalitati)'
        return self.name
    
    def __source_amount(self, query, month):
        q_time = None
        if month != None:
            q_time = Q(doc__date__lt=month.strftime('%Y-%m-%d'))
            
        if q_time != None:
            q = Q(Q(doc__src=self) & q_time)
        else:
            q = Q(doc__src=self)
        q = Q(q & query)
        qs = Operation.objects.filter(q)
        ops = qs.aggregate(total_amount=Sum('amount'))
        if ops['total_amount'] != None:
            return ops['total_amount']
        return 0
    
    def balance(self, month=None, src_exclude=None):
        q_time = None
        if month != None:
            q_time = Q(doc__date__lt=month.strftime('%Y-%m-%d'))
            
        balance = 0
        
        if q_time != None:
            q = Q(Q(doc__src=self) & q_time)
        else:
            q = Q(doc__src=self)
        qs = Operation.objects.filter(q)
        if src_exclude != None:
            qs = qs.exclude(src_exclude)
        ops = qs.aggregate(total_amount=Sum('amount'))
        if ops['total_amount'] != None:
            balance = balance - ops['total_amount']
        
        if q_time != None:
            q = Q(Q(dest=self) & q_time)
        else:
            q = Q(dest=self)
        ops = Operation.objects.filter(q).aggregate(total_amount=Sum('amount'))
        if ops['total_amount'] != None:
            balance = balance + ops['total_amount']
        
        if self.type == 'apart' and balance != 0:
            return balance * -1
        return balance 
    
    def can_delete(self):
        if self.type == 'penalties':
            return False
        if OperationDoc.objects.filter(Q(src=self) | Q(billed=self)).count() > 0:
            return False
        if Operation.objects.filter(dest=self).count() > 0:
            return False
        return True

    def charged(self, month=None):
        query = Q(Q(doc__type='invoice') | Q(doc__type='collection'))
        return self.__source_amount(query, month)
     
    def has_quotas(self):
        return Quota.objects.filter(Q(dest=self) | Q(src=self)).count() > 0
    
    def new_transfer(self, amount, no, dest_account, date=timezone.now()):
        self.__assert_doc_not_exists(no)
        
        doc = OperationDoc.objects.create(date=date, no=no, src=self,
                                          type='transfer', billed=dest_account)
        Operation.objects.create(amount=amount, doc=doc, dest=dest_account)
        self.save()
        
    def new_multi_transfer(self, no, billed, ops, date=timezone.now(),
                           transfer_type='transfer'):
        self.__assert_doc_not_exists(no)
        doc = OperationDoc.objects.create(date=date, no=no, src=self,
                                          type=transfer_type, billed=billed)
        for op in ops:
            loss = None
            if len(op) == 3:
                loss = op[2]
            Operation.objects.create(amount=op[1], doc=doc, dest=op[0],
                                     loss=loss)
        self.save()
        
    def new_charge(self, amount, date, no, billed, dest_accounts,
                    charge_type, vat, issue_date, due_date, document_id, start_service_date, end_service_date, quantity, unit_type):
        self.__assert_doc_not_exists(no)
        
        new_charge = OperationDoc.objects.create(date=date, no=no,
                            billed=billed, src=self, type=charge_type, vat=vat, issue_date=issue_date, due_date=due_date, document_id=document_id, start_service_date=start_service_date, end_service_date=end_service_date, quantity=quantity, unit_type=unit_type)
        
        quotas = Quota.objects.filter(src=self)
        sum_fun = lambda x, q: x + Decimal(q.ratio * amount).quantize(EPS)
        qsum = reduce(sum_fun, quotas, 0)
        remainder_quota = None
        if qsum != amount:
            remainder = qsum - amount
            remainder_quota = choice(quotas)
        
        for q in quotas:
            q_amount = q.ratio * amount
            if remainder_quota != None and remainder_quota == q:
                logger.info('Selecting %s for a remainder of %f', q.dest,
                            remainder)
                q_amount = q_amount - remainder
            
            Operation.objects.create(amount=q_amount, doc=new_charge,
                                     dest=q.dest)
        
        self.save()
        
    def operation_list(self, month, month_end):
        result = []
        
        q_time = Q(Q(date__gte=month.strftime('%Y-%m-%d')) & 
                   Q(date__lt=month_end.strftime('%Y-%m-%d')))
        q_accnt_link = Q(Q(src=self) | Q(operation__dest=self))
        q = Q(q_time & q_accnt_link)
        qs = OperationDoc.objects.filter(q)
        docs = qs.annotate(total_amount=Sum('operation__amount')).order_by(
                                                                    'date')
        if self.type == 'apart':
            for d in docs:
                if d.penalties() != None:
                    d.total_amount = d.total_amount - d.penalties()
                d.total_amount = d.total_amount * -1
            
        result.extend(docs)
        
        return result
    
    def payments(self, since, until, exclude=None):
        payments = 0
        q_time = Q(Q(doc__date__gt=since.strftime('%Y-%m-%d')) & 
                   Q(doc__date__lt=until.strftime('%Y-%m-%d')))
        
        q = Q(Q(amount__gt=0) & Q(doc__src=self) & q_time)
        qs = Operation.objects.filter(q)
        if exclude != None:
            qs = qs.exclude(Q(dest=exclude))
        ops = qs.aggregate(total_amount=Sum('amount'))
        if ops['total_amount'] != None:
            payments = 0 - ops['total_amount']
        
        logger.debug('Payments from %s %s -> %s excluding %s are %f' % 
                     (self, since, until, exclude, payments))
        
        if self.type == 'apart':
            return payments * -1
        return payments 
    
    def received(self, month=None):
        q_time = None
        if month != None:
            q_time = Q(doc__date__lt=month.strftime('%Y-%m-%d'))
            
        if q_time != None:
            q = Q(Q(dest=self) & q_time)
        else:
            q = Q(dest=self)
        ops = Operation.objects.filter(q).aggregate(total_amount=Sum('amount'))
        if ops['total_amount'] != None:
            return ops['total_amount']
        return 0
     
    def transferred(self, month=None):
        query = Q(doc__type='transfer')
        return self.__source_amount(query, month)
     