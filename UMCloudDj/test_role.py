from django.utils import unittest
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.http import HttpRequest
from django.test.client import Client
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse

from uploadeXe.models import Role
from uploadeXe.models import User_Roles
from django.forms import ModelForm
from organisation.models import Organisation
from organisation.models import UMCloud_Package
from organisation.models import User_Organisations
from users.models import UserProfile
from django import forms



class RoleViewTestCase(TestCase):
    fixtures = ['uploadeXe/fixtures/initial-model-data.json']
    def setUp(self):
	"""
	Have to manually create a random role for initial testing.
	"""
	testrole = Role.objects.create(role_name="Tester", role_desc="This is a test for roles")
	
	"""
	Creating user directly so that we have a user to authenticate against views
	"""
	testuser = User.objects.create(username='testuser', password='12345', is_active=True, is_staff=True, is_superuser=True)
        adminrole=Role.objects.get(pk=1)
        user_role = User_Roles(name="test", user_userid=testuser, role_roleid=adminrole)
        user_role.save()
        testuser2 = User.objects.create(username="testuser2", password="54321", is_active=True, is_staff=True, is_superuser=True)
        user_role2 = User_Roles(name="test", user_userid=testuser2, role_roleid=adminrole)
        user_role2.save()
        mainorganisation = Organisation.objects.get(pk=1)
        user_organisation = User_Organisations(user_userid=testuser, organisation_organisationid=mainorganisation)
        user_organisation.save()
        user_organisation2 = User_Organisations(user_userid=testuser2, organisation_organisationid=mainorganisation)
        user_organisation2.save()


    def test_create(self):
        view_name='role_new'
        """
        Users cannot be created without logging in
	UMCloudDj.views.role_create
        """

	response = self.client.post('/rolenew/')
	self.assertEqual(response.status_code, 302)
	#self.assertContains(response, "http://testserver/login/?next=/rolenew/")

	post_data={'role_name':'test_create','role_desc':'This is created by the test procedure'}
        response = self.client.post('/rolenew/', post_data)
        self.assertEqual(response.status_code, 302)
        #302 is redirected to login page.

        """
        User can be created if logged in
	UMCloudDj.views.role_create
        """
	"""
	Also tests if user_table table returns success redirect
	UMCloudDj.views.role_table
	"""
        self.c = Client();
        self.user = User.objects.get(username="testuser")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser', password='hello')
        login = self.c.login(username='testuser', password='hello')

        requesturl = reverse(view_name)

	"""
	Just checking a new form when no post data is given
	"""
	response = self.c.post(requesturl)
	self.assertContains(response, "id_role_name")
	
        response = self.c.post(requesturl, post_data)
        test_create_role = Role.objects.get(role_name="Tester")
        self.assertEqual('Tester',Role.objects.get(role_name='Tester').role_name)
        self.assertRedirects(response, '/rolestable/')

    @unittest.expectedFailure
    def test_create_faiilure(self):
	"""
	Incorrectly done model fails for logged in user
	UMCloudDj.views.user_create
	"""
	self.c = Client();
        self.user = User.objects.get(username="testuser")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser', password='hello')
        login = self.c.login(username='testuser', password='hello')

	post_data_incorrect={'role_name':'Tester','role_desc':'This is a false test creation that is bound to fail'}
        requesturl = reverse(view_name)
        response = self.c.post(requesturl, post_data_incorrect)
	self.assertEqual(response.status_code, 200)

    def test_update(self):
	view_name='role_edit'
	post_data_changes={'role_name':'Tester','role_desc':'This is an update to Tester'}
	
	"""
	Login required
	UMCloudDj.views.role_update
	"""
	testerrole = Role.objects.get(role_name="Tester")
	testerroleid = testerrole.id;
	requesturl = reverse(view_name, kwargs={'pk':testerroleid})
	response = self.client.post(requesturl)
	self.assertEqual(response.status_code, 302)
	#ToDo should return /login/?blah Check that

	"""
	Logged in user unable to update id that doesnt exist, shoulw raise 404
	UMCloudDj.views.user_delete
	"""
	self.c = Client();
        self.user = User.objects.get(username="testuser")
        self.user.set_password('hello') 
        self.user.save()
        self.user = authenticate(username='testuser', password='hello') 
        login = self.c.login(username='testuser', password='hello') 

	requesturl = reverse(view_name, kwargs={'pk':42})
	response = self.c.post(requesturl)
	self.assertEqual(response.status_code, 404)
	
	"""
	Logged in usere should be able to update a valid user's details and return usertable
	UMCloudDj.views.user_update
	"""
	self.c = Client();
        self.user = User.objects.get(username="testuser")
        self.user.set_password('hello') 
        self.user.save()
        self.user = authenticate(username='testuser', password='hello') 
        login = self.c.login(username='testuser', password='hello') 
	
	"""
        Just checking a new form when no post data is given
        """
	requesturl = reverse(view_name, kwargs={'pk':testerroleid})
        response = self.c.post(requesturl)
        self.assertContains(response, "id_role_name")

	testerrole = Role.objects.get(role_name='Tester')
	testerroleid = testerrole.id;
	self.c.get(view_name,kwargs={'pk':testerroleid})
	requesturl = reverse(view_name, kwargs={'pk':testerroleid})
	response = self.c.post(requesturl, post_data_changes)
	changedvalue=Role.objects.get(role_name='Tester').role_desc
	self.assertEqual('This is an update to Tester', changedvalue)
	self.assertRedirects(response, '/rolestable/')
	

    def test_delete(self):
	view_name='role_delete'
	"""
	User logged in should be able to delete user
	UMCloudDj.views.user_delete
        """
	self.c = Client();
	self.user = User.objects.get(username="testuser")
        self.user.set_password('hello') 
        self.user.save()
        self.user = authenticate(username='testuser', password='hello') 
        login = self.c.login(username='testuser', password='hello') 

	testerrole = Role.objects.get(role_name='Tester')
	testerroleid = testerrole.id;

        requesturl = reverse(view_name, kwargs={'pk':testerroleid})
        response = self.c.get(requesturl)
        self.assertEquals(response.status_code,200)


	"""
	Logged in user deleting unknown user: 4040
	UMCloudDj.views.user_delete
	"""
	self.c = Client();
        self.user = User.objects.get(username="testuser")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser', password='hello')
        login = self.c.login(username='testuser', password='hello')

	requesturl = reverse(view_name, kwargs={'pk':42})
	response = self.c.get(requesturl)
	self.assertEqual(response.status_code, 404)




    def tearDown(self):
	print("end of Role CRUD test")
