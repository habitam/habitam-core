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
    
Created on Aug 3, 2013

@author: Stefan Guna
'''
from datetime import date
from dateutil.relativedelta import relativedelta
from habitam.licensing.models import License, Administrator
from habitam.settings import TRIAL_LICENSE
import logging


logger = logging.getLogger(__name__)


def register_trial(user):
    try:
        if user.administrator:
            raise ValueError('Sunteți deja un administrator!')
    except Administrator.DoesNotExist:
        pass
    trial = {}
    trial.update(TRIAL_LICENSE)
    trial['valid_until'] = date.today()
    trial['valid_until'] += relativedelta(days=TRIAL_LICENSE['days_valid'])
    del trial['days_valid']
    
    l = License.objects.create(**trial)
    admin = Administrator.objects.create(user=user, license=l)
    admin.save()
    logger.info('Created trial license for %s' % user)
    