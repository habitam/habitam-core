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
import tempfile


def __add_ops(billed, service, op_docs):
    print billed, service, op_docs
    for op_doc in op_docs:
        for op in op_doc.operation_set.all():
            tmp = billed[op.dest.name][service.name] 
            billed[op.dest.name][service.name] = tmp + op.amount

def download_display_list(building, begin_ts, end_ts):
    services = building.services()
   
    billed = {}
    for ap in building.apartments():
        billed[ap.account.name] = {}
        for service in services:
            billed[ap.account.name][service.account.name] = 0
        
    for service in services:
        op_docs = service.account.operation_list(begin_ts, end_ts)
        __add_ops(billed, service, op_docs)
    
    temp = tempfile.TemporaryFile()
    temp.write(str(billed))
    return temp
