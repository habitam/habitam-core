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
    
Created on Apr 30, 2013

@author: Stefan Guna
'''

from datetime import date
from django.db.models.aggregates import Sum
from django.db.models.query_utils import Q
from habitam.downloads.common import signatures, habitam_brand, MARGIN
from habitam.entities.models import ApartmentConsumption, ServiceConsumption
from habitam.financial.models import Quota
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, cm, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.platypus.flowables import PageBreak, Spacer
from reportlab.platypus.paragraph import Paragraph
import logging
import tempfile

logger = logging.getLogger(__name__)

__HEIGHT__ = A4[0]
__WIDTH__ = A4[1]

__FONT_SIZE__ = 9


def __add_amounts(breakdown, service_info, service, op_docs):
    sname = service.__unicode__()
    si = service_info[sname]
    si['amount'] = 0
    
    for op_doc in op_docs:
        for op in op_doc.operation_set.all():
            tmp = breakdown[op.dest.name][sname]['amount']
            breakdown[op.dest.name][sname]['amount'] = tmp + op.amount
            si['amount'] = si['amount'] + op.amount
            
            
def __add_consumption(breakdown, service_info, service, op_docs):
    sname = service.__unicode__()
    if not service.quota_type == 'consumption':
        return
    si = service_info[sname]
    si['consumed_declared'] = 0
    
    for op_doc in op_docs:
        for ac in ApartmentConsumption.objects.filter(doc=op_doc):
            apname = ac.apartment.__unicode__()
            tmp = breakdown[apname][sname]['consumed'] 
            breakdown[apname][sname]['consumed'] = tmp + ac.consumed
            tmp = si['consumed_declared']
            si['consumed_declared'] = tmp + ac.consumed
        
        q = ServiceConsumption.objects.filter(doc=op_doc, service=service)
        tmp = q.aggregate(Sum('consumed'))
        si['consumed_invoiced'] = tmp['consumed__sum']
        if si['consumed_invoiced'] == None:
            si['consumed_invoiced'] = 0
        si['consumed_loss'] = si['consumed_invoiced'] - si['consumed_declared']
        if si['amount'] == None:
            si['amount'] = 0
        si['price_per_unit'] = si['amount'] / si['consumed_declared']
       
        
def __add_quotas(billed, service):
    if service.quota_type not in ['equally', 'inhabitance', 'area', 'rooms',
                                  'manual']:
        return
    
    sname = service.__unicode__()
    quotas = Quota.objects.filter(src=service.account)
    for quota in quotas:
        billed[quota.dest.name][sname]['quota'] = quota.ratio
        
def __list_format(canvas, doc):
    canvas.saveState()
    building_style = ParagraphStyle(name='building_title',
                                    fontSize=__FONT_SIZE__)
    t = u'%s<br/>Data afișării: %s<br/>Luna: %s' % (doc.habitam_building.name,
                                              doc.habitam_display,
                                              doc.habitam_month)
    p = Paragraph(t, building_style)
    p.wrapOn(canvas, 5 * cm, 2 * cm)
    p.drawOn(canvas, .5 * cm, __HEIGHT__ - 1.7 * cm)
    habitam_brand(canvas, __WIDTH__, __HEIGHT__)
    canvas.restoreState()
            

def download_display_list(building, begin_ts, end_ts):
    services = building.services()
   
    breakdown = {}
    service_info = {}
    balance = {}
    penalties_exclude = Q(dest=building.penalties_account)
    
    for ap in building.apartments():
        apname = ap.__unicode__()
        breakdown[apname] = {}
        balance[apname] = {}
        a = breakdown[apname]
        b = balance[apname]
        b['penalties'] = {}
        b['penalties']['at_begin'] = ap.penalties(begin_ts) 
        b['penalties']['at_end'] = ap.penalties(end_ts)
        
        b['balance'] = {}
        b['balance']['at_begin'] = ap.account.balance(begin_ts, penalties_exclude)
        b['balance']['at_end'] = ap.account.balance(end_ts, penalties_exclude)
        
        for service in services:
            if service.archived:
                continue
            sname = service.__unicode__()
            a[sname] = {}
            a[sname]['amount'] = 0
            if service.quota_type == 'consumption':
                a[sname]['consumed'] = 0
            
 
    for service in services:
        if service.archived:
            continue
        sname = service.__unicode__()
        service_info[sname] = {}
        op_docs = service.account.operation_list(begin_ts, end_ts)
        __add_amounts(breakdown, service_info, service, op_docs)
        __add_consumption(breakdown, service_info, service, op_docs)
        __add_quotas(breakdown, service)
    
    staircase_breakdown = {}
    staircase_balance = {}    
    for sc in building.apartment_groups():
        if sc == building:
            continue
        scname = sc.__unicode__()
        staircase_breakdown[scname] = {}
        staircase_balance[scname] = {}
        for ap in sc.apartments():
            apname = ap.__unicode__()
            staircase_breakdown[scname][apname] = breakdown[apname]
            staircase_balance[scname][apname] = balance[apname]
    
    
    temp = tempfile.NamedTemporaryFile()

    __to_pdf(temp, breakdown, building, begin_ts, end_ts)

    # TODO (Stefan) this file should be persisted and downloaded on subsequent calls
    return temp


def __to_pdf(tempFile, breakdown, building, begin_ts, end_ts):
    doc = SimpleDocTemplate(tempFile, pagesize=landscape(A4), leftMargin=MARGIN,
                            rightMargin=MARGIN, topMargin=MARGIN,
                            bottomMargin=MARGIN,
                            title=u'Lista de întreținere %s' % building.name,
                            author='www.habitam.ro')
    flowables = []
    sc_title_style = ParagraphStyle(name='staircase_title', alignment=TA_CENTER)
                         
    for sc in building.apartment_groups():
        if sc == building:
            continue
        sc_title = Paragraph(u'Lista de întreținere scara %s' % 
                             sc.name, sc_title_style)
        data = __list_data(sc, breakdown, building.services())
    
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
                        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('VALIGN', (0, 0), (0, -1), 'TOP'),
                        ('FONTSIZE', (0, 0), (-1, -1), __FONT_SIZE__),
                        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                        ('BOX', (0, 0), (-1, -1), 0.25, colors.black)
                       ]))

        flowables.extend([Spacer(1, .5 * cm), sc_title,
                          Spacer(1, cm), table,
                          Spacer(1, .5 * cm), signatures(__FONT_SIZE__),
                          PageBreak()])
    
    doc.habitam_building = building
    doc.habitam_month = begin_ts.strftime('%B %Y')
    doc.habitam_display = date.today().strftime('%d %B %Y')
    doc.build(flowables, onFirstPage=__list_format, onLaterPages=__list_format)


def __list_data(ap_group, d_billed, building_services):
    data = [] 
    header = []
    header.append('Apartament')
    header.append('Numele')
    header.append('Nr Pers')
    
    totalRow = []
    totalRow.append('')
    totalRow.append(u'Total Scară')
    totalRow.append('')
    
    totalDict = {}
    
    data.append(header)
    firstTime = True
    for ap in ap_group.apartments():
        apname = ap.__unicode__()
        ownername = ap.owner.name
        inhabitance = ap.inhabitance
        
        row = []
        row.append(apname)
        row.append(ownername)
        row.append(inhabitance)
        total_amount = 0
        
        for service in building_services:
            sname = service.__unicode__()
            if firstTime is True:
                header.append(sname + ' cost')
                totalDict[sname] = 0
            total_amount = total_amount + d_billed[apname][sname]['amount']
            row.append(str(d_billed[apname][sname]['amount']))
            # calculate total cost for a service/staircase
            totalDict[sname] = totalDict[sname] + d_billed[apname][sname]['amount']
            
            if firstTime is True:
                if service.quota_type == 'consumption':
                    header.append(sname + ' consum')
            consValue = '-'
            logger.info('[toData] - ap=%s service=%s cost=%s' % (apname, sname, d_billed[apname][sname]['amount']))
            if service.quota_type == 'consumption':
                consValue = str(d_billed[apname][sname]['consumed'])
                row.append(consValue)
                
        if firstTime is True:
            header.append('Total')
        row.append(total_amount) 
        data.append(row)
        firstTime = False
        
    for service in building_services:
        sname = service.__unicode__()
        totalRow.append(totalDict[sname])
        if service.quota_type == 'consumption':
            totalRow.append('')
    data.append(totalRow)
    
    return data

