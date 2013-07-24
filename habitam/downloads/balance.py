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
    
Created on Jul 21, 2013

@author: Stefan Guna
'''
import logging


logger = logging.getLogger(__name__)





def __assets(building, day):
    result = {}

    # sold in casa si in banca
    for mt in ['cash', 'bank']:
        is_mt = lambda ac: ac.money_type == mt and ac.type == 'std'
        result[mt] = building.balance_by_type(is_mt, day)
    
    aps = building.apartments()
    ap_pending = 0
    penalties_pending = 0
    for ap in aps:
        ap_pending = ap_pending + ap.balance(day)
        tmp = ap.penalties(day)
        if tmp != None:
            penalties_pending = penalties_pending + ap.penalties(day)
    
    # lista curenta
    result['apartment_pending'] = ap_pending
    # restante ale locatarilor
    result['penalties_pending'] = penalties_pending
    
    # facturi de la furnizori si prestatori care urmeaza a fi repartizate pe liste.
    # everything is automatically distributed to the list
    result['outstanding_invoices'] = 0
    
    return result


def __liabilities(building, day):
    result = {}
    # fond rulment
    # fond de reparatii
    # fond de penalizari
    # fonduri speciale
    # facturi de la terti
    for t in ['rulment', 'repairs', 'penalties', 'special', '3rd party']:
        is_t = lambda ac:ac.type == t
        result[t] = building.balance_by_type(is_t, day)   
    
    return result


def download_balance(building, day):
    data = {'day': day, 'assets': __assets(building, day),
            'liabilities': __liabilities(building, day)}
    logger.debug('Register is %s' % data)
    return None
