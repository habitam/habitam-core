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

Created on Apr 9, 2013

@author: Stefan Guna
'''
from decimal import Decimal
from django.utils import unittest, timezone
from entities.models import Apartment, ApartmentGroup, Account, Service
from services.models import Quota
import logging


logger = logging.getLogger(__name__)

QUOTA_TYPES = {'inhabitance':1., 'surface':10., 'rooms':2., 'floor':None}

class EntitiesTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            if EntitiesTestBase.already_setup != None:
                return
        except:
            pass
        EntitiesTestBase.already_setup = True
        
        root = ApartmentGroup.objects.create(name='myblock')
        root.save()
        left = ApartmentGroup.objects.create(parent=root)
        left.save()
        right = ApartmentGroup.objects.create(parent=root)
        right.save()
       
        def create_apartment(i, parent):
            logger.info('creating apartment', i)
            account = Account.objects.create()
            ap = Apartment.objects.create(name=str(i), parent=parent,
                            account=account, inhabitance=i, surface=i * 10,
                            rooms=i * 2, floor=i)
            ap.save()
            
        for i in range(0, 5):
            create_apartment(i, left)
        for i in range(5, 10):
            create_apartment(i, right)
            
    class Meta:
        abstract = True
        
        
class EntitiesTests(EntitiesTestBase):
    def test_new_apartment(self):
        ap = Apartment.objects.get(name='1')
        self.assertEqual(ap.type, 'apart')
        
        
    def test_get_all_apartments(self):
        block = ApartmentGroup.objects.get(name='myblock')
        aps = block.apartments()
        names = []
        for ap in aps:
            names.append(ap.name)
        for i in range(10):
            self.assertIn(str(i), names)


class QuotaTests(EntitiesTestBase):
    @classmethod
    def __setup_quota(cls, quota_type):
        block = ApartmentGroup.objects.get(name='myblock')
        account = Account.objects.create()
        service = Service.objects.create(name='service' + quota_type,
                                    billed=block, account=account)
        service.set_quota(quota_type)
        service.save()
        
    @classmethod
    def setUpClass(cls):
        EntitiesTestBase.setUpClass()
        for qt, v in QUOTA_TYPES.iteritems():
            if not v:
                continue
            QuotaTests.__setup_quota(qt)
            
    def __correct_quota(self, apid, quota_type):
        service = Service.objects.get(name='service' + quota_type)
        total = 9 * 5 * QUOTA_TYPES[quota_type]
        ap = Apartment.objects.get(name=str(apid)) 
        q = Quota.objects.get(src=service.account, dest=ap.account)
        expected = Decimal(apid * QUOTA_TYPES[quota_type]) / Decimal(total)
        expected = expected.quantize(Decimal('0.00001'))
        self.assertEquals(expected, q.ratio)
   
    def test_correct_quota(self):
        for i in range(10):
            for qt, v in QUOTA_TYPES.iteritems():
                if not v:
                    continue
                self.__correct_quota(i, qt) 
        
        
class ServiceTests(EntitiesTestBase):
    @classmethod
    def __setup_invoice(cls, no, value):
        service = Service.objects.get(name='service1')
        service.new_invoice(value, timezone.now(), no)
    
    @classmethod 
    def setUpClass(cls):
        EntitiesTestBase.setUpClass()
        block = ApartmentGroup.objects.get(name='myblock')
        account = Account.objects.create()
        
        service = Service.objects.create(name='service1', billed=block,
                                         account=account)
        
        apartments = block.apartments()
        for ap in apartments:
            Quota.objects.create(src=service.account, dest=ap.account,
                                 ratio=1. / len(apartments))
        service.save()

        ServiceTests.__setup_invoice('invoice1', 100) 
        ServiceTests.__setup_invoice('invoice2', 10)  
    
    def test_apartment_balance(self):
        ap = Apartment.objects.get(name='1')
        self.assertEquals(11, ap.balance())
            
    def test_duplicate_invoice(self):
        with self.assertRaises(NameError):
            self.__setup_invoice('invoice1', 100)
