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
    
Created on July 9, 2013

@author: Stefan Guna
'''
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from habitam.settings import PENALTY_START_DAYS, EPS
import logging

logger = logging.getLogger(__name__)


def __monthly_penalties(ap, cp, dd, day):
    building = ap.building()
    
    begin = date(day=building.close_day, month=dd.month.month,
                 year=dd.month.year)
    end = begin + relativedelta(months=1)
    
    begin_balance = ap.account.balance(begin)
    end_balance = ap.account.balance(end)
    monthly_debt = end_balance - begin_balance
    next_day = day + relativedelta(days=1)
    payments = ap.account.payments(end, next_day,
                                     building.penalties_account)
    balance = monthly_debt + payments - cp

    logger.debug('%s -> %s' % (begin_balance, end_balance))
    if balance >= 0:
        logger.debug('No debts at %s %f' % (end, balance))
        return 0, payments
    
    count_since = end + relativedelta(days=building.payment_due_days)
    count_since = count_since + relativedelta(days=PENALTY_START_DAYS)
    days = (day - count_since).days
    
    if days < 0:
        logger.debug('Not enough time (%d) for penalties at %s %f' % 
                     (days, day, balance))
        return 0, payments
    
    penalties = days * building.daily_penalty * balance * -1 / 100 
    
    logger.debug('Penalties %s -> %s are %f for debts are %f in %d days, the monthly debt is %f' % 
                 (begin, end, penalties, balance, days, monthly_debt))
    
    return penalties, payments

def penalties(ap, day):
    logger.debug('Computing penalties for %s at %s' % (ap, day))
    building = ap.building()
    if building.daily_penalty == None or building.daily_penalty == 0:
        return None
    
    until = day - relativedelta(days=building.payment_due_days)
    until = until - relativedelta(days=PENALTY_START_DAYS)
   
    nps = start = None 
    p, cp = 0, 0
    penalties_found = False
    for dd in building.display_dates(ap.no_penalties_since, until):
        print '++++++', dd.month 
        m, cp = ap.__monthly_penalties(cp, dd, day)
        p = p + m
        
        if m > 0:
            penalties_found = True
        if nps == None or not penalties_found:
            nps = dd.month
        
    if nps != start:
        logger.info('Increment nps for %s(pk=%d) from %s to %s' % 
                    (ap, ap.pk, start, nps))
        ap.no_penalties_since = nps
        ap.save()
    
    logger.debug('Penalties for %s at %s are %f' % (ap, day, p))    
    p = Decimal(p).quantize(EPS) * -1
    if p == 0:
        return None
    return p

