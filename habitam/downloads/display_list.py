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
from habitam.entities.models import ApartmentConsumption, ServiceConsumption
from habitam.financial.models import Quota
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, cm, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import logging
import tempfile

logger = logging.getLogger(__name__)

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

    to_pdf(temp, to_data(building, breakdown), building)

    # TODO (Stefan) this file should be persisted and downloaded on subsequent calls
    return temp

def to_pdf(tempFile, data, building):
    # response = HttpResponse(mimetype='application/pdf')
    # response['Content-Disposition'] = 'attachment; filename=somefilename.pdf'

    elements = []

    doc = SimpleDocTemplate(tempFile, rightMargin=0.5 * cm, leftMargin=0.5 * cm, topMargin=0.3 * cm, bottomMargin=0, pagesize=landscape(A4))

    table = Table(data)
    table.setStyle(TableStyle([('VALIGN', (0, 0), (0, -1), 'TOP'),
                       ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                       ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                       ]))
    # TODO Ionut: fix image load

    # I = Image('ui/img/habitam-logo-header.jpg')
    # I.drawHeight = 1.25*cm*I.drawHeight / I.drawWidth
    # I.drawWidth = 1.25*cm
    # elements.append(I)
    
    styleSheet = getSampleStyleSheet()
    P0 = Paragraph('''
    <para align=right spaceb=3><b>
    <font color=green>Raport Habitam</font></b>
    </para>''',
    styleSheet["BodyText"])
    P1 = Paragraph('''
    <para align=right spaceb=3><b>
    <font color=black>Bloc ''' + building.name + '''</font></b>
    </para>''',
    styleSheet["BodyText"])
    
    elements.append(P0)
    elements.append(P1)
    elements.append(table)
    doc.build(elements) 
    # return response


def to_data(building, d_billed):
    services = building.services()
    data = [] 
    header = []
    header.append('Ap')
    data.append(header)
    firstTime = True
    for ap in building.apartments():
        apname = ap.__unicode__()
        row = []
        row.append(apname)
        for service in services:
            sname = service.__unicode__()
            if firstTime is True:
                header.append(sname + ' cost')
            row.append(str(d_billed[apname][sname]['amount']))
            if firstTime is True:
                header.append(sname + ' consum')
            consValue = '-'
            logger.info('[toData] - ap=%s service=%s cost=%s' % (apname, sname, d_billed[apname][sname]['amount']))
            if service.quota_type == 'consumption':
                consValue = str(d_billed[apname][sname]['consumed'])
            row.append(consValue)
        data.append(row)
        firstTime = False
    return data
