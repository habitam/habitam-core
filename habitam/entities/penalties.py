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
from django.db.models.aggregates import Sum
from django.db.models.query_utils import Q
from habitam.financial.models import Operation
from habitam.settings import PENALTY_START_DAYS, EPS
import logging

logger = logging.getLogger(__name__)


def __debt(ap, begin, end):
    begin_balance = ap.account.balance(begin)
    end_balance = ap.account.balance(end)
    debt = end_balance - begin_balance
    return debt

    
def __debt_interval(building, display_date):
    begin = date(day=building.close_day, month=display_date.month.month,
                 year=display_date.month.year)
    end = begin + relativedelta(months=1)
    return begin, end
    
    
def __display_dates(building, since, until):
    q = building.displaydate_set.filter(Q(timestamp__gt=since) & 
                                    Q(timestamp__lt=until))
    result = q.order_by('month')
    logger.debug('Display dates for %s between %s - %s are %s' % 
                 (building, since, until, map(lambda dd: dd.month, result)))
    return result


def __days_elapsed(building, since, until):
    count_since = since + relativedelta(days=building.payment_due_days)
    count_since = count_since + relativedelta(days=PENALTY_START_DAYS)
    days = (until - count_since).days
    return days

def __monthly_penalties(ap, carry, display_date, when):
    building = ap.building()
    begin, end = __debt_interval(building, display_date)
    debt = __debt(ap, begin, end)
    payments = __payments(ap, end, when)
    balance = debt + payments - carry

    logger.debug('Balance difference for %s between %s -> %s is %d' % 
                 (ap, begin, end, balance))
    if balance >= 0:
        logger.debug('No debts at %s %f' % (end, balance))
        return 0, payments

    days_elapsed = __days_elapsed(building, end, when)    
    if days_elapsed < 0:
        logger.debug('Not enough time (%d) for penalties at %s %f' % 
                     (days_elapsed, when, balance))
        return 0, payments
    
    penalties = days_elapsed * building.daily_penalty * balance * -1 / 100 
    
    logger.debug('Penalties %s -> %s are %f for debts are %f in %d days_elapsed, the monthly debt is %f' % 
                 (begin, end, penalties, balance, days_elapsed, debt))
    
    return penalties, payments

    
def __payments(ap, since, until):
    account = ap.account
    until = until + relativedelta(days=1)
    
    payments = 0
    q_time = Q(Q(doc__date__gt=since.strftime('%Y-%m-%d')) & 
               Q(doc__date__lt=until.strftime('%Y-%m-%d')))
    
    q = Q(Q(amount__gt=0) & Q(doc__src=account) & q_time)
    qs = Operation.objects.filter(q)
    qs = qs.exclude(Q(dest=ap.building().penalties_account))
    ops = qs.aggregate(total_amount=Sum('amount'))
    if ops['total_amount'] != None:
        payments = 0 - ops['total_amount']
    
    logger.debug('Payments from %s %s -> %s are %f' % 
                 (account, since, until, payments))
    
    return payments * -1 


def penalties(ap, when):
    logger.debug('Computing penalties for %s at %s' % (ap, when))
    building = ap.building()
    if building.daily_penalty == None or building.daily_penalty == 0:
        logger.debug('There is no penalty configuration for this building')
        return None
    
    until = when - relativedelta(days=
                (building.payment_due_days + PENALTY_START_DAYS))
   
    no_penalty_since = start = None 
    penalty, carry = 0, 0
    penalties_found = False
    
    for display_date in __display_dates(building, ap.no_penalties_since,
                                        until):
        monthly, carry = __monthly_penalties(ap, carry, display_date, when)
        penalty = penalty + monthly
        
        if monthly > 0:
            penalties_found = True
        if no_penalty_since == None or not penalties_found:
            no_penalty_since = display_date.month
        
    if no_penalty_since != start:
        logger.info('Increment no_penalty_since for %s(pk=%d) from %s to %s' % 
                    (ap, ap.pk, start, no_penalty_since))
        ap.no_penalties_since = no_penalty_since
        ap.save()
    
    penalty = Decimal(penalty).quantize(EPS) * -1
    logger.debug('Penalties for %s at %s are %f' % (ap, when, penalty))    
    if penalty == 0:
        return None
    return penalty

