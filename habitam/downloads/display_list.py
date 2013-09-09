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
from django.db.models.aggregates import Sum
from django.db.models.query_utils import Q
from django.conf import settings
from habitam.entities.models import ApartmentConsumption, ServiceConsumption
from habitam.financial.models import Quota
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, cm, landscape
from reportlab.platypus.flowables import PageBreak
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, KeepInFrame
from reportlab.lib.styles import getSampleStyleSheet
import logging
import tempfile

logger = logging.getLogger(__name__)

MARGIN_SIZE = 0.2 * cm
PAGE_SIZE = A4


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

    to_pdf(temp, breakdown, building, begin_ts, end_ts)

    # TODO (Stefan) this file should be persisted and downloaded on subsequent calls
    return temp


def to_pdf(tempFile, breakdown, building, begin_ts, end_ts):

    elements = []
   
    doc = SimpleDocTemplate(tempFile, rightMargin=MARGIN_SIZE, leftMargin=MARGIN_SIZE, topMargin=MARGIN_SIZE, bottomMargin=0, pagesize=landscape(PAGE_SIZE))
        
    for sc in building.apartment_groups():
        if sc == building:
            continue
        data = to_data(sc, breakdown, building.services())
    
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([('VALIGN', (0, 0), (0, -1), 'TOP'),
                       ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                       ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                       ]))
        
        # TODO Ionut: fix image load. I don't like it
        header_logo_path=settings.BASE_DIR+'/habitam/ui/static/ui/img/habitam-logo-header.jpg'
        I = Image(header_logo_path)
        I.hAlign ='LEFT'
        styleSheet = getSampleStyleSheet()
        P0 = Paragraph('''
            <para align=right spaceb=3><b>
            <font color=green>Raport Habitam '''+begin_ts.strftime('%d/%m/%Y')+'''-'''+end_ts.strftime('%d/%m/%Y')+'''</font></b>
            </para>''',
            styleSheet["BodyText"])
        P1 = Paragraph('''
            <para align=right spaceb=3><b>
            <font color=black>Asociatia proprietari ''' + building.name + ''' Scara ''' + sc.name + ''' </font></b>
            </para>''',
            styleSheet["BodyText"])
        
        headerTableData=[(I, P0),('http://www.habitam.ro',P1)]  
        headerTable=Table(headerTableData, colWidths=(landscape(PAGE_SIZE)[0]-2*MARGIN_SIZE)/2)
        
        P2 = Paragraph ('''
            <para align=left spaceb=3><b>
            <font color=black> Presedinte </font></b></para>''', styleSheet["BodyText"])
        
        P3 = Paragraph ('''
            <para align=center spaceb=3><b>
            <font color=black> Cenzor </font></b></para>''', styleSheet["BodyText"])
     
        P4 = Paragraph ('''
            <para align=right spaceb=3><b>
            <font color=black> Contabil </font></b></para>''', styleSheet["BodyText"])  
        footerTableData=[('Presedinte', 'Cenzor', 'Contabil'), ('...........','...........','...........')]
        footerTable=Table(footerTableData, colWidths=(landscape(PAGE_SIZE)[0]-2*MARGIN_SIZE)/3)
         
        main_frame = KeepInFrame(maxWidth=landscape(PAGE_SIZE)[0] - 2 * MARGIN_SIZE, maxHeight=landscape(PAGE_SIZE)[1] - 2 * MARGIN_SIZE, content=[headerTable, table, footerTable], mode='shrink', name='main_frame')

        elements.append(main_frame)
        elements.append(PageBreak())
    
    
    doc.build(elements) 
    # return response


def to_data(ap_group, d_billed, building_services):
    data = [] 
    header = []
    header.append('Ap')
    header.append('Numele')
    header.append('Nr Pers')
    
    totalRow = []
    totalRow.append('')
    totalRow.append('Total Scara')
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
        total_amount=0
        
        for service in building_services:
            sname = service.__unicode__()
            if firstTime is True:
                header.append(sname + ' cost')
                totalDict[sname]=0
            total_amount=total_amount+d_billed[apname][sname]['amount']
            row.append(str(d_billed[apname][sname]['amount']))
            #calculate total cost for a service/staircase
            totalDict[sname]=totalDict[sname]+d_billed[apname][sname]['amount']
            
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

