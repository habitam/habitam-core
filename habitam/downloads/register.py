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
    
Created on Jul 18, 2013

@author: Stefan Guna
'''
from datetime import date
from dateutil.relativedelta import relativedelta
import logging


logger = logging.getLogger(__name__)


def __balance(building, d):
    s = reduce(lambda s, l: s + l.account.balance(d),
                 building.accountlink_set.all(), 0)
    s = reduce(lambda s, cf: s + cf.account.balance(d),
                 building.collecting_funds(), s)
    return s


def __operations(entity, d):
    next_day = d + relativedelta(days=1)
    ops = entity.account.operation_list(d, next_day)
    for op in ops:
        op.total_amount = op.total_amount * -1
    return ops


def __register(building, d, initial_balance):
    ml = map(lambda ap: __operations(ap, d), building.apartments()) + \
         map(lambda svc: __operations(svc, d), building.services())
    ops = []
    for ol in ml:
        if ol:
            ops.extend(ol)
    
    end_balance = reduce(lambda c, op: c + op.total_amount, ops, initial_balance)
    return {'initial_balance': initial_balance,
            'operations': ops,
            'end_balance':end_balance}, end_balance


def download_register(building, day):
    d = date(day.year, day.month, 1)
    logger.debug('Downloading register %s - %s' % (d, day))
    
    day_before = d - relativedelta(days=1)
    initial_balance = __balance(building, day_before)
    data = {}
    while d <= day:
        data[d], initial_balance = __register(building, d, initial_balance)
        d = d + relativedelta(days=1)
    
    logger.debug('Register is %s' % data )
    return None
        
