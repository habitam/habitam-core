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

MARGIN = .2 * cm


def __habitam_logo():
    current_module = sys.modules[__name__]
    base = os.path.dirname(current_module.__file__)
    return os.path.join(base, 'habitam-logo.jpg')

   
def habitam_brand(canvas, width, height):
    x, y = width - 3 * cm, height - 1.5 * cm
    canvas.setFontSize(9)
    canvas.setFillColorRGB(.07, .48, .23)
    canvas.drawImage(__habitam_logo(), x, y, width=2.3 * cm, preserveAspectRatio=True)
    canvas.drawString(x, y, 'www.habitam.ro')
    canvas.linkURL('http://www.habitam.ro', (x, y, 3.35 * cm, 2.2 * cm), relative=1)

    
def signatures(font_size=None):
    d = [[u'PREȘEDINTE\n(numele și semnătura)', u'CENZOR\n(numele și semnătura)', u'ADMINISTRATOR\n(numele și semnătura)']]
    table = Table(d, colWidths=[7 * cm, 7 * cm, 7 * cm])
    style = [('ALIGN', (0, 0), (-1, 0), 'CENTER'), ]
    if font_size:
        style.append(('FONTSIZE', (0, 0), (-1, -1), font_size))
    table.setStyle(TableStyle(style))
    return table
