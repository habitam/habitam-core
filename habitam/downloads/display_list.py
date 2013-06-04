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
    
Created on Apr 30, 2013

@author: Stefan Guna
'''
from django.db.models.aggregates import Sum
from habitam.entities.models import ApartmentConsumption, ServiceConsumption
from habitam.financial.models import Quota
import tempfile


def __add_amounts(billed, service_info, service, op_docs):
    sname = service.__unicode__()
    si = service_info[sname]
    si['amount'] = 0
    
    for op_doc in op_docs:
        for op in op_doc.operation_set.all():
            tmp = billed[op.dest.name][sname]['amount']
            billed[op.dest.name][sname]['amount'] = tmp + op.amount
            si['amount'] = si['amount'] + op.amount
            
            
def __add_consumption(billed, service_info, service, op_docs):
    sname = service.__unicode__()
    if not service.quota_type == 'consumption':
        return
    si = service_info[sname]
    si['consumed_declared'] = 0
    
    for op_doc in op_docs:
        for ac in ApartmentConsumption.objects.filter(doc=op_doc):
            apname = ac.apartment.__unicode__()
            tmp = billed[apname][sname]['consumed'] 
            billed[apname][sname]['consumed'] = tmp + ac.consumed
            tmp = si['consumed_declared']
            si['consumed_declared'] = tmp + ac.consumed
        
        q = ServiceConsumption.objects.filter(doc=op_doc, service=service)
        tmp = q.aggregate(Sum('consumed'))
        si['consumed_invoiced'] = tmp['consumed__sum']
        si['consumed_loss'] = si['consumed_invoiced'] - si['consumed_declared']
        si['price_per_unit'] = si['amount'] / si['consumed_declared']
       
        
def __add_quotas(billed, service):
    if service.quota_type not in ['equally', 'inhabitance', 'area', 'rooms',
                                  'manual']:
        return
    
    sname = service.__unicode__()
    quotas = Quota.objects.filter(src=service.account)
    for quota in quotas:
        billed[quota.dest.name][sname]['quota'] = quota.ratio

def download_display_list(building, begin_ts, end_ts):
    services = building.services()
   
    billed = {}
    service_info = {}
    for ap in building.apartments():
        apname = ap.__unicode__()
        billed[apname] = {}
        for service in services:
            sname = service.__unicode__()
            billed[apname][sname] = {}
            billed[apname][sname]['amount'] = 0
            if service.quota_type == 'consumption':
                billed[apname][sname]['consumed'] = 0
        
    for service in services:
        sname = service.__unicode__()
        service_info[sname] = {}
        op_docs = service.account.operation_list(begin_ts, end_ts)
        __add_amounts(billed, service_info, service, op_docs)
        __add_consumption(billed, service_info, service, op_docs)
        __add_quotas(billed, service)
    
    temp = tempfile.TemporaryFile()
    temp.write(str(service_info))
    temp.write(str(billed))
    # TODO (Ionut) generate PDF
    # TODO (Stefan) this file should be persisted and downloaded on subsequent calls
    return temp
