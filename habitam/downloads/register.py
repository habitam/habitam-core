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
from habitam.downloads.common import MARGIN, habitam_brand
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.platypus.flowables import Spacer
import logging
import tempfile


__HEIGHT__ = A4[1]
__WIDTH__ = A4[0]
__FONT_SIZE__ = 9

logger = logging.getLogger(__name__)


def __balance(building, d, money_type):
    funds = building.accountlink_set.filter(account__money_type=money_type)
    s = reduce(lambda s, l: s + l.account.balance(d), funds, 0)
    collecting_funds = building.collecting_funds().filter(account__money_type=money_type)
    s = reduce(lambda s, cf: s + cf.account.balance(d), collecting_funds, s)
    return s


def __document_number(op_doc):
    if op_doc.receipt:
        return op_doc.receipt.no
    if op_doc.invoice:
        return op_doc.invoice.series + '/' + op_doc.invoice.no
    return ''

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


def __register_format(canvas, doc):
    canvas.saveState()
    building_style = ParagraphStyle(name='building_title')
    t = doc.habitam_building.name
    p = Paragraph(t, building_style)
    p.wrapOn(canvas, 5 * cm, 2 * cm)
    p.drawOn(canvas, .5 * cm, __HEIGHT__ - 1 * cm)
    habitam_brand(canvas, __WIDTH__, __HEIGHT__)
    canvas.restoreState()


def to_data(building, d_list, day):
    d = date(day.year, day.month, 1)
    
    data = [] 
    header = []
    header.append('Nr. Crt.')
    header.append(u'Nr. Act')
    header.append(u'Nr.\nAnexa')
    header.append(u'Explicatii')
    header.append(u'Incasari')
    header.append(u'Plati')
    header.append('Simbol\ncont')
    data.append(header)
    
    details_style = ParagraphStyle(name='details',
                                   fontSize=__FONT_SIZE__)
    day_item_style = ParagraphStyle(name='day_item',
                                    fontSize=__FONT_SIZE__,
                                    alignment=TA_RIGHT)
        
    while d <= day:

        if d_list[d]['operations'] is not None and len(d_list[d]['operations']) > 0:

            initial_balance = d_list[d]['initial_balance'];
            end_balance = d_list[d]['end_balance'];
            
            first_row = []
            first_row.append('')
            first_row.append('')
            first_row.append('')
            first_row.append(Paragraph(u'Sold inițial la %s' % d, day_item_style))
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
                row.append(__document_number(op_doc))
                row.append('')
                row.append(Paragraph(op_doc.description, details_style))
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
            sum_row.append(Paragraph('RULAJ ZI', day_item_style))
            sum_row.append(inbound)
            sum_row.append(outbound)
            sum_row.append('')
            data.append(sum_row) 
                     
            last_row = []
            last_row.append('')
            last_row.append('')
            last_row.append('')
            last_row.append(Paragraph('SOLD FINAL', day_item_style))
            last_row.append(end_balance)
            last_row.append('')
            last_row.append('')
            data.append(last_row)
                                    
        d = d + relativedelta(days=1)   
    return data
        
def __to_pdf(tempFile, data, building, title):
    
   
    doc = SimpleDocTemplate(tempFile, pagesize=A4, leftMargin=MARGIN,
                            rightMargin=MARGIN, topMargin=MARGIN,
                            bottomMargin=MARGIN,
                            title=title,
                            author='www.habitam.ro')    
    
    register_title_style = ParagraphStyle(name='register_title', alignment=TA_CENTER)
    register_title = Paragraph(title, register_title_style)
    
    table = Table(data, colWidths=[1.3 * cm, 3 * cm, 1.2 * cm, 7.5 * cm, 2 * cm, 2 * cm, 1.7 * cm])
    table.setStyle(TableStyle([
                        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), __FONT_SIZE__),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                        ('BOX', (0, 0), (-1, -1), 0.25, colors.black)
                        ]))

    flowables = [Spacer(1, 1.5 * cm), register_title, Spacer(1, cm), table]
    
    doc.habitam_building = building  
    doc.build(flowables, onFirstPage=__register_format, onLaterPages=__register_format)


def download_bank_register(building, day):
    return __download_register(building, day, 'bank', u'Registru de bancă') 

def download_cash_register(building, day):
    return __download_register(building, day, 'cash', u'Registru de casă')   




