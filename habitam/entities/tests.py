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
from habitam.entities.models import Apartment, ApartmentGroup, Service, Person
from habitam.services.models import Quota
import logging


logger = logging.getLogger(__name__)

QUOTA_TYPES = {'inhabitance':1., 'area':10., 'rooms':2., 'floor':None}



class EntitiesTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            if EntitiesTestBase.already_setup != None:
                return
        except:
            pass
        EntitiesTestBase.already_setup = True
        
        root = ApartmentGroup.building_create(name='mybuilding')
        root.save()
        left = ApartmentGroup.staircase_create(name='left', parent=root)
        left.save()
        right = ApartmentGroup.staircase_create(name='right', parent=root)
        right.save()
       
        def create_apartment(i, parent):
            logger.info('creating apartment %d', i)
            owner = Person.objects.create(name=str(i))
            ap = Apartment.objects.create(name=str(i), parent=parent, 
                            inhabitance=i, area=i * 10, rooms=i * 2, floor=i,
                            owner=owner)
            ap.save()
            
        for i in range(0, 5):
            create_apartment(i, left)
        for i in range(5, 10):
            create_apartment(i, right)
            
    class Meta:
        abstract = True
        
        
class EntitiesTests(EntitiesTestBase):
        
    def test_get_all_apartments(self):
        building = ApartmentGroup.objects.get(name='mybuilding')
        aps = building.apartments()
        names = []
        for ap in aps:
            names.append(ap.name)
        for i in range(10):
            self.assertIn(str(i), names)

    def test_get_all_groups(self):
        building = ApartmentGroup.objects.get(name='mybuilding')
        left = ApartmentGroup.objects.get(name='left')
        right = ApartmentGroup.objects.get(name='right')
        groups = building.apartment_groups()
        self.assertListEqual([building, left, right], groups) 


class QuotaTests(EntitiesTestBase):
    @classmethod
    def __setup_quota(cls, quota_type):
        building = ApartmentGroup.objects.get(name='mybuilding')
        service = Service.objects.create(name='service' + quota_type,
                                    billed=building, quota_type=quota_type)
        service.set_quota()
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
        service.new_inbound_operation(value, no, timezone.now())
    
    @classmethod
    def __apartment_payment(cls, name, value):
        ap = Apartment.objects.get(name=name)
        ap.new_inbound_operation(value)
    
    @classmethod 
    def setUpClass(cls):
        EntitiesTestBase.setUpClass()
        building = ApartmentGroup.objects.get(name='mybuilding')
        
        service = Service.objects.create(name='service1', billed=building)
        
        apartments = building.apartments()
        for ap in apartments:
            Quota.objects.create(src=service.account, dest=ap.account,
                                 ratio=1. / len(apartments))
        service.save()

        ServiceTests.__setup_invoice('invoice1', 100) 
        ServiceTests.__setup_invoice('invoice2', 10)
        ServiceTests.__apartment_payment('2', 5)
        
    def __assert_ap_balance(self, name, value):
        ap = Apartment.objects.get(name=name)
        self.assertEquals(value, ap.balance())

    def __assert_apgroup_balance(self, name, value):
        apg = ApartmentGroup.objects.get(name=name)
        self.assertEquals(value, apg.balance())
   
    
    def test_apartment1_balance(self):
        self.__assert_ap_balance('1', -11)
        
    def test_apartment2_balance(self):
        self.__assert_ap_balance('2', -6)
        
    def test_leftgroup_Balance(self):
        self.__assert_apgroup_balance('left', 0)
    
    def test_rightgroup_Balance(self):
        self.__assert_apgroup_balance('right', 0)

    def test_mybuilding_Balance(self):
        self.__assert_apgroup_balance('mybuilding', 5)
        
    def test_duplicate_invoice(self):
        with self.assertRaises(NameError):
            self.__setup_invoice('invoice1', 100)
            
    def test_get_all_services(self):
        building = ApartmentGroup.objects.get(name='mybuilding')
        services = []
        for qt, v in QUOTA_TYPES.iteritems():
            if v == None:
                continue
            services.append(Service.objects.get(name=('service' + qt)))
        services.append(Service.objects.get(name='service1'))
        self.assertListEqual(services, building.services())
