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
    
Created on Sep 21, 2013

@author: Stefan Guna
'''

from reportlab.lib.units import cm
from reportlab.platypus.tables import Table, TableStyle
import os
import sys

def __habitam_logo():
    current_module = sys.modules[__name__]
    base = os.path.dirname(current_module.__file__)
    return os.path.join(base, 'habitam-logo.jpg')
   
def habitam_footer(canvas):
    canvas.setFontSize(9)
    canvas.setFillColorRGB(.07, .48, .23)
    canvas.drawImage(__habitam_logo(), cm, cm, width=2.3 * cm, preserveAspectRatio=True)
    canvas.drawString(cm, cm, 'www.habitam.ro')
    canvas.linkURL('http://www.habitam.ro', (cm, cm, 3.35 * cm, 2.2 * cm), relative=1)
    
def signatures():
    d = [[u'PREȘEDINTE\n(numele și semnătura)', u'CENZOR\n(numele și semnătura)', u'ADMINISTRATOR\n(numele și semnătura)']]
    table = Table(d, colWidths=[7 * cm, 7 * cm, 7 * cm])
    table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ]))
    return table
