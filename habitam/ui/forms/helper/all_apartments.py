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
    
Created on Aug 12, 2013

@author: Stefan Guna
'''

def all_apartments_data(label, cleaned_data):
    all_data = {}
    for k, v in cleaned_data.items():
        if not k.startswith(label):
            continue
        all_data[int(k[len(label):])] = v
        if not v:
            continue
        
    for k in all_data.keys():
        del cleaned_data[label + str(k)]
    
    if len(all_data) == 0:
        return None 
    return all_data


def aggregate_apartments(label, cleaned_data):
    all_data = all_apartments_data(label, cleaned_data)
    if all_data == None:
        return None, None
    return sum(all_data.itervalues()), all_data


def drop_skip_checkboxes(label, cleaned_data):    
    for k in cleaned_data.keys():
        if not k.startswith(label):
            continue
        del cleaned_data[k]


def skip_apartments(label, cleaned_data):
    to_skip = [] 
    for k, v in cleaned_data.iteritems():
        if not k.startswith(label) or not v:
            continue
        to_skip.append(int(k[len(label):])) 
    return to_skip