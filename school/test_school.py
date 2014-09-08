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
from organisation.models import UMCloud_Package
from organisation.models import User_Organisations
from school.models import School
from allclass.models import Allclass
from uploadeXe.models import Role
from uploadeXe.models import User_Roles
from django import forms


"""
        url(r'^schools/$', 'school.views.school_list', name='school_list'),
        url(r'^schoolstable/$', 'school.views.school_table', name='school_table'),
        url(r'^schoolnew/$', 'school.views.school_create', name='school_new'),
        url(r'^schooledit/(?P<pk>\d+)$', 'school.views.school_update', name='school_edit'),
        url(r'^schooldelete/(?P<pk>\d+)$', 'school.views.school_delete', name='school_delete'),
"""


class SchoolViewTestCase(TestCase):
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


	school1 = School(school_name="TestSchool", school_desc="This is the desc of the TestSchool",organisation_id=1)
	school1.save()
	

    def test_school_create(self):
	"""
	Users can create schools
	school.views.school_create
	"""
	url_name="school_new"
	post_data_create={'school_name':'TestSchoolCreate','school_desc':'Unit Test Creation','organisationid':1}
	
	"""
	Schools cannot be created without logging in 
	school.views.school_create
	"""
        requesturl = reverse(url_name)
        response = self.client.post(requesturl, post_data_create)
	self.assertEqual(response.status_code, 302)

	"""
	Schools can be created with logging in
	allclass.views.allclass_create
	"""
	self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

	requesturl = reverse(url_name)
	response = self.c.post(requesturl, post_data_create)
	self.assertEqual("TestSchoolCreate", School.objects.get(school_name="TestSchoolCreate").school_name)

	"""
        Schools created again with the same name will fail and return an errro in the create page.
        """
        student_list_ids=[3,4]
	post_data_create={'school_name':'TestSchoolCreate','school_desc':'Unit Test Creation','organisationid':1}

        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

        requesturl = reverse(url_name)
        response = self.c.post(requesturl, post_data_create)
        self.assertContains(response, "The School Name already exists")
        self.assertEqual(response.status_code, 200)


    @unittest.expectedFailure
    def test_school_create_failure(self):
	"""
	Incorrectly done model fails for logged in user
	school.views.school_create
	"""
	url_name="school_new"
	post_data_create_incorrect={'school_name':'TestSchool','school_desc':'This is a false test creation that is bound to fail.','organisationid':42}


        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

        requesturl = reverse(url_name)
        response = self.c.post(requesturl, post_data_create_incorrect)
        test_create_user = School.objects.get(school_name="TestSchoolCreateFail")
        self.assertEqual("TestSchoolCreateFail", School.objects.get(school_name="TestSchoolCreateFail").school_name)

    def test_update(self):
        view_name='school_edit'
	post_data_update={'school_name':'TestSchool','school_desc':'This is an update to TestSchool','organisation':1}

        """
        Login required
	school.views.school_edit
        """
	testschoolcreate = School.objects.get(school_name="TestSchool")
	testschoolcreateid = testschoolcreate.id;
	requesturl = reverse(view_name, kwargs={'pk':testschoolcreateid})	
	response = self.client.post(requesturl)
	#ToDO: should check for return ./login/?blah 
        self.assertEqual(response.status_code, 302)

        """
        Logged in user unable to update id that doesnt exist, shoulw raise 404
	school.views.school_edit
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
        school.views.school_edit
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

	testschoolcreate = School.objects.get(school_name='TestSchool')
	testschoolcreateid = testschoolcreate.id;
	
        self.c.get(view_name,kwargs={'pk':testschoolcreateid})
        requesturl = reverse(view_name, kwargs={'pk':testschoolcreateid})
        response = self.c.post(requesturl, post_data_update)

        changedvalue=School.objects.get(school_name='TestSchool').school_desc
        self.assertEqual('This is an update to TestSchool', changedvalue)
        self.assertRedirects(response, '/schoolstable/')


    def test_delete(self):
        view_name='school_delete'
        """
        User logged in should be able to delete user
	school.views.school_delete
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

	testschoolcreate = School.objects.get(school_name='TestSchool')
        testschoolcreateid = testschoolcreate.id;

        requesturl = reverse(view_name, kwargs={'pk':testschoolcreateid})
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

    def test_table(self):
	view_url="/schoolstable/"

	"""
	Schools cannot be seen without logging in
	"""
        self.c = Client();
        response = self.c.get(view_url)
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/schoolstable/')

        """
        Logged in user will be able to see the school table page
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user = authenticate(username='testuser1', password='12345')
        login = self.c.login(username='testuser1', password='12345')

        response = self.c.get(view_url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "TestSchool", status_code=200)

	

    def tearDown(self):
	print("end of School tests")

	
	
	
