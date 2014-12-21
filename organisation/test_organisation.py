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
from organisation.models import Organisation, Organisation_Code
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

class Organisation(models.Model):
   organisation_name = models.CharField(max_length=300)
   organisation_desc = models.CharField(max_length=1000)
   add_date = models.DateTimeField(default=datetime.datetime.now)
   set_package = models.ForeignKey(UMCloud_Package)


"""

class OrganisationViewTestCase(TestCase):
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

	organisation1 = Organisation.objects.create(organisation_name='TestingOrganisation', organisation_desc='This is the testing organisation', add_date='2014-07-07',set_package=subscription1)
	organisation1.save()

	orgadmin1=User.objects.create(username='orgadmin1', password='12345', is_active=True, is_staff=False, is_superuser=False)
	orgadmin1.save()
	orgadminrole=Role.objects.get(pk=2)
	user_role2=User_Roles(name="test", user_userid=orgadmin1, role_roleid=orgadminrole)
	user_role2.save()
	user_organisation2=User_Organisations(user_userid=orgadmin1, organisation_organisationid=mainorganisation)
	user_organisation2.save()

	testuser3=User.objects.create(username='testuser2', password='12345', is_active=True, is_staff=False, is_superuser=False)
	testuser3.save()
	contentauthor_role=Role.objects.get(pk=3)
	user_role3=User_Roles(name="test", user_userid=testuser3, role_roleid=contentauthor_role)
	user_role3.save()
	user_organisation3=User_Organisations(user_userid=testuser3, organisation_organisationid=mainorganisation)
	user_organisation3.save()	

	
    def test_organosation_table(self):
	"""Just a test for the table
	"""
	self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

	mainorganisation=Organisation.objects.get(pk=1)
        newcode=Organisation_Code(organisation=mainorganisation,code="COW1234")
        newcode.save()


	url_name="organisation_table"
        requesturl = reverse(url_name)
        response = self.c.get(requesturl)
	self.assertEquals(response.status_code, 200)
	

	self.c = Client();
        self.user = User.objects.get(username="orgadmin1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='orgadmin1', password='hello')
        login = self.c.login(username='orgadmin1', password='hello')


        url_name="organisation_table"
        requesturl = reverse(url_name)
        response = self.c.get(requesturl)
        self.assertEquals(response.status_code, 200)

    def test_my_organisation(self):
	self.c = Client();
        self.user = User.objects.get(username="orgadmin1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='orgadmin1', password='hello')
        login = self.c.login(username='orgadmin1', password='hello')

	url_name="my_organisation"
	requesturl = reverse(url_name)
        response = self.c.get(requesturl)
        self.assertEquals(response.status_code, 200)

	self.c = Client();
        self.user = User.objects.get(username="testuser2")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser2', password='hello')
        login = self.c.login(username='testuser2', password='hello')

        url_name="my_organisation"
        requesturl = reverse(url_name)
        response = self.c.get(requesturl)
        self.assertEquals(response.status_code, 200)
	self.assertContains(response, "You do not have permission to see this page.")

    def test_my_organisation_update(self):
	mainorganisation=Organisation.objects.get(pk=1)
        newcode=Organisation_Code(organisation=mainorganisation,code="COW1234")
        newcode.save()

	"""Login Required"""
	url_name="my_organisation_update"
	self.c = Client();
	requesturl=reverse(url_name, kwargs={'pk':1})
	response=self.c.get(requesturl)
	self.assertEqual(response.status_code, 302)

	"""Only org admins can do stuff
	"""
	self.user = User.objects.get(username="testuser2")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser2', password='hello')
        login = self.c.login(username='testuser2', password='hello')

        response = self.c.get(requesturl)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "You do not have permission to see this page.")

	"""Orgadmins can do stuff
	"""
	self.user = User.objects.get(username="orgadmin1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='orgadmin1', password='hello')
        login = self.c.login(username='orgadmin1', password='hello')

	post_data={'id_code':'UpdateCODE123'}
        response = self.c.post(requesturl, post_data)
	self.assertEquals(response.status_code, 200)



    def test_organisation_create(self):
	"""
	Users can create organisations
	organisation.views.organisation_create
	"""
	setpackage = Subscription.objects.get(pk=1)
	url_name="organisation_new"
	post_data_create={'organisation_name':'TestingOrganisation2','organisation_desc':'Test to create TestingOrganisation2','add_date':'2014-07-07', 'umpackageid':1, 'username':'orgadmin04','email':'orgadmino2@orgadmin04.com','password':'12345','passwordagain':'12345','first_name':'Org','last_name':'Admin','address':'Test Street, 1234 Avenue, Modest, Country','phonenumber':'+1234567890','dateofbirth':'02/02/1980','gender':'F'}
	
	"""
	Organisations cannot be created without logging in 
	organisation.views.organisation_create
	"""
        requesturl = reverse(url_name)
        response = self.client.post(requesturl, post_data_create)
	self.assertEqual(response.status_code, 302)

	"""
	Organisation can be created with logging in
	organisation.views.organisation_create
	"""
	self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

	requesturl = reverse(url_name)
	response = self.c.post(requesturl, post_data_create)
	updatedorganisation = Organisation.objects.get(organisation_name="TestingOrganisation2")
	changedvalue=updatedorganisation.organisation_name
	self.assertEqual("TestingOrganisation2",changedvalue)

	post_data_create_existing={'organisation_name':'TestingOrganisation2','organisation_desc':'Test to create TestingOrganisation2','add_date':'2014-07-07', 'umpackageid':1, 'username':'orgadmin04','email':'orgadmino2@orgadmin04.com','password':'12345','passwordagain':'12345','first_name':'Org','last_name':'Admin','address':'Test Street, 1234 Avenue, Modest, Country','phonenumber':'+1234567890','dateofbirth':'02/02/1980','gender':'F'}
	self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

        requesturl = reverse(url_name)
        response = self.c.post(requesturl, post_data_create_existing)
	self.assertContains(response, "Username already exists")

	post_data_create_orgexists={'organisation_name':'TestingOrganisation','organisation_desc':'Test to create TestingOrganisation1','add_date':'2014-07-07', 'umpackageid':1, 'username':'orgadmin06','email':'orgadmin06@orgadmin04.com','password':'12345','passwordagain':'12345','first_name':'Org','last_name':'Admin','address':'Test Street, 1234 Avenue, Modest, Country','phonenumber':'+1234567890','dateofbirth':'02/02/1980','gender':'F'}
	self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

        requesturl = reverse(url_name)
        response = self.c.post(requesturl, post_data_create_orgexists)
        self.assertContains(response, "Organisation already exists")

	post_data_create_notsamepass={'organisation_name':'TestingOrganisation2','organisation_desc':'Test to create TestingOrganisation2','add_date':'2014-07-07', 'umpackageid':1, 'username':'orgadmin04','email':'orgadmino2@orgadmin04.com','password':'123456','passwordagain':'12345','first_name':'Org','last_name':'Admin','address':'Test Street, 1234 Avenue, Modest, Country','phonenumber':'+1234567890','dateofbirth':'02/02/1980','gender':'F'}
	self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

        requesturl = reverse(url_name)
        response = self.c.post(requesturl, post_data_create_notsamepass)
	self.assertContains(response, 'The two passwords you gave do not match')

	"""Need to be staff"""
        self.c = Client();
        self.user = User.objects.get(username="testuser2")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser2', password='hello')
        login = self.c.login(username='testuser2', password='hello')

	requesturl = reverse(url_name)
        response = self.c.post(requesturl, post_data_create_notsamepass)


        self.assertContains(response, "You do not have permission to see this page")




    @unittest.expectedFailure
    def test_school_create_failure(self):
	"""
	Incorrectly done model fails for logged in user
	organisation.views.organisation_create
	"""
	setpackage=Subscription.objects.get(pk=1)
	url_name="organisation_new"
	post_data_create_incorrect={'organisation_name':'','organisation_desc':'Incorrect Test to create TestingOrganisation2','add_date':'2014-07-07', 'umpackageid':setpackage}


        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

        requesturl = reverse(url_name)
        response = self.c.post(requesturl, post_data_create_incorrect)
        self.assertEqual("TestingOrganisation2", Organisation.objects.get(organisation_name="TestingOrganisation2").organisation_name)

    def test_update(self):
        view_name='organisation_edit'
	setpackage=Subscription.objects.get(pk=1)
	post_data_update={'organisation_name':'TestingOrganisation','organisation_desc':'This is an update to Test to create TestingOrganisation','add_date':'2014-07-07', 'set_package':1}

        """
        Login required
	organisation.views.organisation_edit
        """

	testingorganisation = Organisation.objects.get(organisation_name='TestingOrganisation')
	testingorganisationid = testingorganisation.id;

	requesturl = reverse(view_name, kwargs={'pk':testingorganisationid})	
	response = self.client.post(requesturl)
	#ToDO: should check for return ./login/?blah 
        self.assertEqual(response.status_code, 302)

        """
        Logged in user unable to update id that doesnt exist, shoulw raise 404
	organisation.views.organisation_edit
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
        Logged in usere should be able to update a valid organisation's details and return organisationstable
        organisation.views.organisation_edit
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

	testingorganisation = Organisation.objects.get(organisation_name='TestingOrganisation')
	testingorganisationid = testingorganisation.id;
	
        self.c.get(view_name,kwargs={'pk':testingorganisationid})
        requesturl = reverse(view_name, kwargs={'pk':testingorganisationid})
        response = self.c.post(requesturl, post_data_update)

	changedvalue = Organisation.objects.get(organisation_name='TestingOrganisation').organisation_desc
        self.assertEqual('This is an update to Test to create TestingOrganisation', changedvalue)
        self.assertRedirects(response, '/organisationstable/')


	"""Need to be staff"""
	self.c = Client();
        self.user = User.objects.get(username="testuser2")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser2', password='hello')
        login = self.c.login(username='testuser2', password='hello')

        testingorganisation = Organisation.objects.get(organisation_name='TestingOrganisation')
        testingorganisationid = testingorganisation.id;

        self.c.get(view_name,kwargs={'pk':testingorganisationid})
        requesturl = reverse(view_name, kwargs={'pk':testingorganisationid})
        response = self.c.post(requesturl, post_data_update)

	self.assertContains(response, "You do not have permission to see this page")


    def test_delete(self):
        view_name='organisation_delete'
        """
        User logged in should be able to delete Organisation
	organisation.views.organisation_delete
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

	testingorganisation = Organisation.objects.get(organisation_name='TestingOrganisation')
	testingorganisationid = testingorganisation.id

        requesturl = reverse(view_name, kwargs={'pk':testingorganisationid})
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

	"""Need to be staff"""
        self.c = Client();
        self.user = User.objects.get(username="testuser2")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser2', password='hello')
        login = self.c.login(username='testuser2', password='hello')

	requesturl = reverse(view_name, kwargs={'pk':42})
        response = self.c.get(requesturl)

        self.assertContains(response, "You do not have permission to see this page")




    def tearDown(self):
	print("end of Organiation Tests")

	
	
	
