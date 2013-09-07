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
    
Created on Jul 18, 2013

@author: Stefan Guna
'''
from datetime import date
from dateutil.relativedelta import relativedelta
from django.conf import settings
from os import path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, cm, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, \
    Paragraph, KeepInFrame
from reportlab.platypus.flowables import PageBreak
import logging
import tempfile


pdfmetrics.registerFont(TTFont('Helvetica', path.join(settings.BASE_DIR, 'fonts', 'Arial.ttf')))
MARGIN_SIZE = 0.2 * cm
PAGE_SIZE = A4


logger = logging.getLogger(__name__)


def __balance(building, d, money_type):
    funds = building.accountlink_set.filter(account__money_type=money_type)
    s = reduce(lambda s, l: s + l.account.balance(d), funds, 0)
    collecting_funds = building.collecting_funds().filter(account__money_type=money_type)
    s = reduce(lambda s, cf: s + cf.account.balance(d), collecting_funds, s)
    return s


def __download_register(building, day, money_type, title):
    d = date(day.year, day.month, 1)
    
    day_before = d - relativedelta(days=1)
    initial_balance = __balance(building, day_before, money_type)
    d_elem = {'day': day}
    while d <= day:
        d_elem[d], initial_balance = __register(building, d, initial_balance,
                                                money_type)
        d = d + relativedelta(days=1)
    
    logger.debug('Register is %s' % d_elem)
    
    temp = tempfile.NamedTemporaryFile()

    __to_pdf(temp, to_data(building, d_elem, day), building, title)

    return temp  


def __operations(entity, d, money_type, source_only, dest_only):
    next_day = d + relativedelta(days=1)
    ops = entity.account.operation_list(d, next_day, source_only, dest_only,
                                        money_type)
    for op in ops:
        op.total_amount = op.total_amount * -1
        p = op.penalties()
        op.total_amount = op.total_amount + p if p != None else op.total_amount
    return ops


def __register(building, d, initial_balance, money_type):
    ml = map(lambda ap: __operations(ap, d, money_type, True, False), building.apartments()) + \
         map(lambda svc: __operations(svc, d, money_type, False, True), building.services())
    ops = []
    for ol in ml:
        if ol:
            ops.extend(ol)
    
    end_balance = reduce(lambda c, op: c + op.total_amount, ops, initial_balance)
    return {'initial_balance': initial_balance,
            'operations': ops,
            'end_balance':end_balance}, end_balance

def to_data(building, d_list, day):
    d = date(day.year, day.month, 1)
    data = [] 
    header = []
    header.append('Nr. Crt.')
    header.append(u'Nr. Act')
    header.append(u'Nr. Anexă')
    header.append(u'Explicații')
    header.append(u'Încasări')
    header.append(u'Plăți')
    header.append('Simbol cont')
    data.append(header)
    while d <= day:

        if d_list[d]['operations'] is not None and len(d_list[d]['operations']) > 0:

            initial_balance = d_list[d]['initial_balance'];
            end_balance = d_list[d]['end_balance'];
            
            first_row = []
            first_row.append('')
            first_row.append('')
            first_row.append('')
            first_row.append(u'Sold inițial la %s' % d)
            first_row.append(initial_balance)
            first_row.append('')
            first_row.append('')      
            data.append(first_row)
            
            increment = 1
            inbound = 0
            outbound = 0
            for op_doc in d_list[d]['operations']:
                amount = op_doc.total_amount
                row = []
                row.append(increment)
                row.append(op_doc.no)
                row.append(op_doc.date)
                row.append(op_doc.register_details())
                if amount >= 0:
                    row.append(amount)
                    row.append('')
                    inbound += amount
                    
                else:
                    row.append('')
                    row.append(amount * -1)
                    outbound += amount * -1
                increment += 1
                
                data.append(row)
            
            sum_row = []
            sum_row.append('')
            sum_row.append('')
            sum_row.append('')
            sum_row.append('RULAJ ZI')
            sum_row.append(inbound)
            sum_row.append(outbound)
            sum_row.append('')
            data.append(sum_row) 
                     
            last_row = []
            last_row.append('')
            last_row.append('')
            last_row.append('')
            last_row.append('SOLD FINAL')
            last_row.append(end_balance)
            last_row.append('')
            last_row.append('')
            data.append(last_row)
                                    
        d = d + relativedelta(days=1)   
    return data
        
def __to_pdf(tempFile, data, building, title):
    elements = []
   
    doc = SimpleDocTemplate(tempFile, rightMargin=MARGIN_SIZE,
                            leftMargin=MARGIN_SIZE, topMargin=MARGIN_SIZE,
                            bottomMargin=MARGIN_SIZE, pagesize=PAGE_SIZE,
                            encoding='utf8')
        

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([('VALIGN', (0, 0), (0, -1), 'TOP'),
                   ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                   ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                   ]))
    
    # TODO Ionut: fix image load. I don't like it
    header_logo_path = settings.BASE_DIR + '/habitam/ui/static/ui/img/habitam-logo-header.jpg'
    I = Image(header_logo_path)
    I.hAlign = 'LEFT'
    styleSheet = getSampleStyleSheet()
    P0 = Paragraph(u'<para align=right spaceb=3><b>%s</b></para>' % title,
        styleSheet["BodyText"])
    P1 = Paragraph((u'<para align=right spaceb=3>' + 
        u'Asociația de proprietari <b>%s</b>' + 
        u'</para>') % building.name,
        styleSheet["BodyText"])
    
    headerTableData = [(I, P0), ('www.habitam.ro', P1)]  
    headerTable = Table(headerTableData, colWidths=(portrait(PAGE_SIZE)[0] - 2 * MARGIN_SIZE) / 2)
    
    main_frame = KeepInFrame(maxWidth=portrait(PAGE_SIZE)[0] - 2 * MARGIN_SIZE, maxHeight=portrait(PAGE_SIZE)[1] - 2 * MARGIN_SIZE, content=[headerTable, table], mode='shrink', name='main_frame')

    elements.append(main_frame)
    elements.append(PageBreak())
      
    doc.build(elements) 


def download_bank_register(building, day):
    return __download_register(building, day, 'bank', 'Registru banca') 

def download_cash_register(building, day):
    return __download_register(building, day, 'cash', 'Registru casa')   




