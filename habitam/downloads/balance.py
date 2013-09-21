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
    
Created on Jul 21, 2013

@author: Stefan Guna
'''
from habitam.downloads.common import habitam_brand, signatures, MARGIN
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus.doctemplate import SimpleDocTemplate
from reportlab.platypus.flowables import Spacer
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.tables import Table, TableStyle
import logging
import tempfile


logger = logging.getLogger(__name__)

__HEIGHT__ = A4[0]
__WIDTH__ = A4[1]

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
    result['apartment_pending'] = ap_pending * -1
    # restante ale locatarilor
    result['penalties_pending'] = penalties_pending * -1
    
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


def __balance_format(canvas, doc):
    canvas.saveState()
    canvas.setFontSize(16)
    t = u'Situația soldurilor elementelor de activ și pasiv pentru %s la %s'
    canvas.drawCentredString(__WIDTH__ / 2.0, __HEIGHT__ - 100,
                             t % (doc.habitam_data['building'].name, doc.habitam_data['day']))
    habitam_brand(canvas, __WIDTH__, __HEIGHT__)
    canvas.restoreState()

def __format_data(data):
    styles = getSampleStyleSheet()
    
    assets = data['assets']
    liabilities = data['liabilities']
    
    d = [['NR.\nCRT.', 'ELEMENTE DE ACTIV', 'VALORI\n(LEI)', 'ELEMENTE DE PASIV', 'VALORI\n(LEI)'],
         ['1.', Paragraph(u'Sold în casă', styles['Normal']), assets['cash'], Paragraph('Sold fond de rulment', styles['Normal']), liabilities['rulment']],
         ['2.', Paragraph(u'Sold conturi la bănci', styles['Normal']), assets['bank'], Paragraph(u'Sold fond de reparații', styles['Normal']), liabilities['repairs']],
         ['3.', Paragraph(u'Sume neachitate de proprietarii din asociație pentru lista de plată curentă', styles['Normal']), assets['apartment_pending'], Paragraph('Sold fond sume speciale', styles['Normal']), liabilities['special']],
         ['4.', Paragraph(u'Restanțe existente la data întocmirii acestei situații', styles['Normal']), assets['penalties_pending'], Paragraph('Soldul altor fonduri legal stabilite', styles['Normal']), '0'],
         ['5.', Paragraph(u'Debitori, alții decât mebrii asociației', styles['Normal']), '0', Paragraph('Furnizori pentru facturi neachitate', styles['Normal']), '0'],
         ['6.', Paragraph(u'Acte de plată pe luna în curs, nerepartizate proprietarilor', styles['Normal']), assets['outstanding_invoices'], Paragraph(u'Creditori diverși', styles['Normal']), liabilities['3rd party']],
         ['7.', Paragraph(u'Acte de plăți pentru cheltuielile aferente fondurilor de reparații, speciale, de penalizări care nu au fost încă scăzute din fondurile respective', styles['Normal']), '0', '', ''],
         ['', Paragraph(u'TOTAL PARTEA I', styles['Normal']), sum(assets.values()), Paragraph(u'TOTAL PARTEA II', styles['Normal']), sum(liabilities.values())]
        ]
    
    table = Table(d, colWidths=[1.3 * cm, 7 * cm, 4 * cm, 7 * cm, 4 * cm])
    table.setStyle(TableStyle([
                        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (0, -1), 'MIDDLE'),
                        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                        ('VALIGN', (2, 0), (2, -1), 'MIDDLE'),
                        ('ALIGN', (4, 0), (4, -1), 'CENTER'),
                        ('VALIGN', (4, 0), (4, -1), 'MIDDLE'),
                        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                        ('BOX', (0, 0), (-1, -1), 0.25, colors.black)
                        ]))
    return table

def __to_pdf(temp, data):
    doc = SimpleDocTemplate(temp, pagesize=landscape(A4), leftMargin=MARGIN,
                            rightMargin=MARGIN, topMargin=MARGIN,
                            bottomMargin=MARGIN,
                            title=u'Situația activ/pasiv pentru %s' % data['building'].name,
                            author='www.habitam.ro')
     
    flowables = [Spacer(1, 6 * cm), __format_data(data), Spacer(1, cm), signatures()]
    doc.habitam_data = data    
    doc.build(flowables, onFirstPage=__balance_format, onLaterPages=__balance_format)


def download_balance(building, day):
    data = {'building': building, 'day': day,
            'assets': __assets(building, day),
            'liabilities': __liabilities(building, day)}
    logger.debug('Balance is %s' % data)
    
    temp = tempfile.NamedTemporaryFile()
    __to_pdf(temp, data)
    return temp  
