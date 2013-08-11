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
    
Created on Aug 11, 2013

@author: Stefan Guna
'''
from habitam.entities.models import Supplier

PREDEFINED_SUPPLIERS = {
    'RADET' : {
        'name': u'R.A. de Distribuție a Energiei Termice',
        'address': 'Str. Cavafii Vechi, nr. 15, sector 3',
        'fiscal_id': 'RO361218',
        'registration_id': 'J40/195/1991',
        'bank': 'BCR Filiala Sector 3',
        'county': 'Bucuresti',
        'iban': 'RO55RNCB0074006423030092',
        'legal_representative': None
    }, 'Apa Nova' : {
        'name': u'Apa Nova București S.A.',
        'address': 'Str. Aristide Demetriade, nr. 2, sector 2',
        'fiscal_id': 'RO12276949',
        'registration_id': 'J40/9006/1999',
        'bank': None,
        'county': 'Bucuresti',
        'iban': None,
        'legal_representative': None
    }, 'GDF SUEZ' : {
        'name': u'GDF SUEZ Energy România S.A.',
        'address': 'str. Cavafii Vechi, nr. 15, sector 3',
        'fiscal_id': 'RO13093222',
        'registration_id': 'J40/5447/09.06.2000',
        'bank': 'BRD SMCC',
        'county': 'Bucuresti',
        'iban': 'RO08BRDE450SV06719094500',
        'legal_representative': None
    }, 'Enel Muntenia' : {
        'name': u'Enel Distribuție Muntenia S.A.',
        'address': 'Bl. Ion Mihalache, nr. 41-43',
        'fiscal_id': 'RO14507322',
        'registration_id': 'J40/1859/2002',
        'bank': None,
        'county': 'Bucuresti',
        'iban': None,
        'legal_representative': None
    },
}


def remaining_suppliers(existing_suppliers):
    existing_names = map(lambda s: s.name, existing_suppliers)
    result = []
    for k, v in PREDEFINED_SUPPLIERS.iteritems():
        if not v['name'] in existing_names:
            result.append((k, v['name']))
    return result 


def create_suppliers(supplier_keys):
    result = []
    for sk in supplier_keys:
        supplier = Supplier.objects.create(**PREDEFINED_SUPPLIERS[sk])
        supplier.save()
        result.append(supplier)
    return result
