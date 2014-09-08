from django.utils import unittest
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.http import HttpRequest
from django.test.client import Client
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse

#Testing..
from django.forms import ModelForm
from organisation.models import Organisation
from organisation.models import UMCloud_Package as Subscription
from organisation.models import User_Organisations
from school.models import School
from allclass.models import Allclass
from uploadeXe.models import Role
from uploadeXe.models import User_Roles
from django import forms


"""
class UMCloud_Package(models.Model):
   package_name = models.CharField(max_length=300)
   package_desc = models.CharField(max_length=2000)
   max_students = models.IntegerField()
   max_publishers = models.IntegerField()
   price_rate_permonth = models.FloatField()

"""

class SubscriptionViewTestCase(TestCase):
    fixtures = ['uploadeXe/fixtures/initial-model-data.json']
    def setUp(self):
	"""
	Have to manually create users and assign relationships for initial testing.
	"""
	testuser1= User.objects.create(username='testuser1', password='12345', is_active=True, is_staff=True, is_superuser=True)
	testuser1.save()
	adminrole=Role.objects.get(pk=1)
	user_role1 = User_Roles(name="test", user_userid=testuser1, role_roleid=adminrole)
	user_role1.save()
	mainorganisation = Organisation.objects.get(pk=1)
	user_organisation1 = User_Organisations(user_userid=testuser1, organisation_organisationid=mainorganisation)
	user_organisation1.save()

	subscription1=Subscription.objects.create(package_name="TestingPackage", package_desc="This is the Unit Test Package", max_students=15, max_publishers=2, price_rate_permonth=0.05)
	subscription1.save()

	

    def test_subscription_create(self):
	"""
	Users can create subscriptions
	organisation.views.umpackage_create
	"""
	url_name="umpackage_new"
	post_data_create={'package_name':'TestingPackage2','package_desc':'Test to create TestingPackage2','max_students':15, 'max_publishers':3,'price_rate_permonth':2}
	
	"""
	Subscriptions cannot be created without logging in 
	organisation.views.umpackage_create
	"""
        requesturl = reverse(url_name)
        response = self.client.post(requesturl, post_data_create)
	self.assertEqual(response.status_code, 302)

	"""
	Subcscription can be created with logging in
	organisation.views.umpackage_create
	"""
	self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

	requesturl = reverse(url_name)
	response = self.c.post(requesturl, post_data_create)
	updatedsubscription=Subscription.objects.get(package_name="TestingPackage2")
	changedvalue=updatedsubscription.package_name
	self.assertEqual("TestingPackage2",changedvalue)

    @unittest.expectedFailure
    def test_school_create_failure(self):
	"""
	Incorrectly done model fails for logged in user
	organisation.views.umpackage_create
	"""
	
	url_name="umpackage_new"
        post_data_create_incorrect={'package_name':'TestingPackage2','package_desc':'Over writing Test to create TestingPackage2','max_students':'this should be a number', 'max_publishers':3,'price_rate_permonth':2}


        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

        requesturl = reverse(url_name)
        response = self.c.post(requesturl, post_data_create_incorrect)
        self.assertEqual("TestingPackage2", Subscription.objects.get(package_name="TestingPackage2").package_name)

    def test_update(self):
        view_name='umpackage_edit'
	post_data_update={'package_name':'TestingPackage','package_desc':'Update to Test to create TestingPackage','max_students':15, 'max_publishers':2,'price_rate_permonth':0.05}

        """
        Login required
	organisation.views.umpackage_edit
        """

	testingpackage = Subscription.objects.get(package_name='TestingPackage')
	testingpackageid = testingpackage.id;

	requesturl = reverse(view_name, kwargs={'pk':testingpackageid})	
	response = self.client.post(requesturl)
	#ToDO: should check for return ./login/?blah 
        self.assertEqual(response.status_code, 302)

        """
        Logged in user unable to update id that doesnt exist, shoulw raise 404
	organisation.views.umpackage_edit
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

        requesturl = reverse(view_name, kwargs={'pk':42})
        response = self.c.post(requesturl)
        self.assertEqual(response.status_code, 404)

        """
        Logged in usere should be able to update a valid school's details and return schooltable
        organisation.views.umpacakge_edit
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

	testingpackage = Subscription.objects.get(package_name='TestingPackage')
        testingpackageid = testingpackage.id;
	
        self.c.get(view_name,kwargs={'pk':testingpackageid})
        requesturl = reverse(view_name, kwargs={'pk':testingpackageid})
        response = self.c.post(requesturl, post_data_update)

	changedvalue=Subscription.objects.get(package_name='TestingPackage').package_desc
        self.assertEqual('Update to Test to create TestingPackage', changedvalue)
        self.assertRedirects(response, '/umpackagestable/')


    def test_delete(self):
        view_name='umpackage_delete'
        """
        User logged in should be able to delete umpackage
	organisation.views.umpackage_delete
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

	testingpackage = Subscription.objects.get(package_name='TestingPackage')
        testingpackageid = testingpackage.id;

        requesturl = reverse(view_name, kwargs={'pk':testingpackageid})
        response = self.c.get(requesturl)
        self.assertEquals(response.status_code,200)

        """
        Logged in user deleting unknown user: 4040
	school.views.school_delete
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

        requesturl = reverse(view_name, kwargs={'pk':42})
        response = self.c.get(requesturl)
        self.assertEqual(response.status_code, 404)



    def tearDown(self):
	print("end of Subscription Tests")

	
	
	
