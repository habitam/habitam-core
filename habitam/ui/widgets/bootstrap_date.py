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
    
Created on Jul 24, 2013

@author: Stefan Guna
'''
from django.forms.widgets import DateInput
from django.utils.safestring import mark_safe


'''
Add it to a form as a field declared like the following:
    day = forms.DateField(initial=datetime.date.today,widget=BootstrapDateInput(input_format='yyyy-mm-dd'))
'''   
class BootstrapDateInput(DateInput):
    def __init__(self, input_format, attrs=None, format=None):
        self.input_format = input_format
        super(BootstrapDateInput, self).__init__(attrs, format)
        
    def render(self, name, value, attrs=None):
        value = '' if value == None else value
        output = []
        output.append(u'<div class="input-append">')
        output.append(u'<input class="datepicker datepicker-input" size="16" type="text" name="%s" id="id_%s" value="%s" data-date="%s" data-date-format="%s">' % (name, name, value, value, self.input_format))
        output.append(u'<span class="add-on"><i class="icon-th"></i></span>')
        output.append(u'</div>')
        return mark_safe(u''.join(output)) 