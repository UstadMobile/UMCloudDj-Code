from django.utils import unittest
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.http import HttpRequest
from django.test.client import Client
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse

from uploadeXe.models import Role, Course, Package as Document
from uploadeXe.models import User_Roles
from allclass.models import Allclass
from school.models import School
from django.forms import ModelForm
from organisation.models import Organisation
from organisation.models import UMCloud_Package
from organisation.models import User_Organisations
from users.models import UserProfile
from django import forms



class UserViewTestCase(TestCase):
    fixtures = ['uploadeXe/fixtures/initial-model-data.json']
    def setUp(self):
	"""
	Have to manually create users and assign relationships for initial testing.
	"""
	testuser = User.objects.create(username='testuser', password='12345', is_active=True, is_staff=True, is_superuser=True)
	adminrole=Role.objects.get(pk=2)
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
	
	school1 = School(school_name="TestSchool", school_desc="This is the desc of the TestSchool",organisation_id=1)
        school1.save()

        allclass1 = Allclass(allclass_name="TestAllClassTableTest1", allclass_desc="TestAllClass1 Desc", allclass_location="Test Land" ,school=school1)
        allclass1.save()

        allclass2 = Allclass(allclass_name="TestAllClassTableTest2", allclass_desc="TestAllClass1 Desc", allclass_location="Test Land")
        allclass2.save()

	course1 = Course(name="TestCourse", description="This is a test Course", category="Tests", publisher=testuser, organisation=mainorganisation, success="YES")
        course1.save()
        course2 = Course(name="TestCourse2", description="This is a test Course", category="Tests", publisher=testuser, organisation=mainorganisation, success="YES")
        course2.save()

        document1 = Document(elpid='elpid001', name='TestDocument1', url='/link/to/TestDocument1/',uid='uid001',success='YES',publisher=testuser)
        document1.save()
        document2 = Document(elpid='elpid002', name='TestDocument2', url='/link/to/TestDocument2/',uid='uid002',success='YES',publisher=testuser)
        document2.save()
	
	course1.packages.add(document1)
	course1.packages.add(document2)
	course1.students.add(testuser)
	course1.save()




	""" 
	Ideally we should create first, and then delete but that doesnt work since it removes all users after every test.
	"""

    def test_create(self):
        view_name='user_new'
        """
        Users cannot be created without logging in
	UMCloudDj.views.user_create
        """
	allclassids=[1]
        post_data={'username':'test_create','email':'test_create@ustadmobile.com','password':'123456','passwordagain':'123456','first_name':'test','last_name':'create','role':6,'organisation':1, 'dateofbirth':'02/02/1989','address':'123, ABC Street, DEFG Avenue, IJKLMN, OPQRSTUV', 'gender':'F','phonenumber':'+1234567890','target':allclassids }
        response = self.client.post('/usernew/', post_data)
        self.assertEqual(response.status_code, 302)
        #302 is redirected to login page.

        """
        GUser can be created if logged in
	UMCloudDj.views.user_create
        """
	"""
	Also tests if user_table table returns success redirect
	UMCloudDj.views.user_table
	"""
        self.c = Client();
        self.user = User.objects.get(username="testuser")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser', password='hello')
        login = self.c.login(username='testuser', password='hello')
        requesturl = reverse(view_name)
        response = self.c.post(requesturl, post_data)
        test_create_user = User.objects.get(username="test_create")
        self.assertEqual('test_create',User.objects.get(username='test_create').username)
        self.assertRedirects(response, '/userstable/')

	post_data={'username':'test_create_totable','email':'test_create@ustadmobile.com','password':'123456','passwordagain':'123456','first_name':'test','last_name':'create','role':6,'organisation':1, 'dateofbirth':'02/02/1989','address':'123, ABC Street, DEFG Avenue, IJKLMN, OPQRSTUV', 'gender':'F','phonenumber':'+1234567890','target':allclassids , 'submittotable':'true'}
	response = self.c.post(requesturl, post_data)
        test_create_user = User.objects.get(username="test_create_totable")
        self.assertEqual('test_create_totable',User.objects.get(username='test_create_totable').username)
        self.assertRedirects(response, '/userstable/'+str(test_create_user.id))

	

	post_data={'username':'test_create_tonew','email':'test_create@ustadmobile.com','password':'123456','passwordagain':'123456','first_name':'test','last_name':'create','role':6,'organisation':1, 'dateofbirth':'02/02/1989','address':'123, ABC Street, DEFG Avenue, IJKLMN, OPQRSTUV', 'gender':'F','phonenumber':'+1234567890','target':allclassids , 'submittonew':'true'}
	response = self.c.post(requesturl, post_data)
        test_create_user = User.objects.get(username="test_create_tonew")
        self.assertEqual('test_create_tonew',User.objects.get(username='test_create_tonew').username)
        self.assertContains(response, 'The user test_create_tonew has been created.')

	post_data={'username':'test_create_password_fail','email':'test_create@ustadmobile.com','password':'123456','passwordagain':'12345','first_name':'test','last_name':'create','role':6,'organisation':1, 'dateofbirth':'02/02/1989','address':'123, ABC Street, DEFG Avenue, IJKLMN, OPQRSTUV', 'gender':'F','phonenumber':'+1234567890','target':allclassids , 'submittonew':'true'}
        response = self.c.post(requesturl, post_data)
        self.assertContains(response, 'The two passwords you gave do not match. Please try again.')

	post_data={'username':'test_create_tonew','email':'test_create@ustadmobile.com','password':'123456','passwordagain':'123456','first_name':'test','last_name':'create','role':6,'organisation':1, 'dateofbirth':'02/02/1989','address':'123, ABC Street, DEFG Avenue, IJKLMN, OPQRSTUV', 'gender':'F','phonenumber':'+1234567890','target':allclassids , 'submittonew':'true'}
        response = self.c.post(requesturl, post_data)
        self.assertContains(response, 'That username already exists. Please enter a valid user name')

	post_data={'username':'11111111111111111111111111111111111111111111111111111111111', 'email':'blah@blah.com','password':'123456','passwordagain':'123456','first_name':'test','last_name':'create','role':62,'organisation':1, 'dateofbirth':'02/02/1989','address':'123, ABC Street, DEFG Avenue, IJKLMN, OPQRSTUV', 'gender':'','phonenumber':'+1234567890','target':allclassids , 'submittonew':'true'}
        response = self.c.post(requesturl, post_data)
        self.assertContains(response, 'Could not create user. Make sure you specified all fields')


	response = self.c.get(requesturl)
	self.assertContains(response, "Create a New User")

	requesturl=reverse('user_table', kwargs={'created':42})
	response = self.c.get(requesturl)
	
	

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
	post_data_incorrect={'username':'test_create','email':'test_create@ustadmobile.com','password':'123456','passwordagain':'123456','first_name':'test','last_name':'create','role':1,'organisation':1}
        requesturl = reverse(view_name)
        response = self.c.post(requesturl, post_data_incorrect)
	self.assertEqual(response.status_code, 200)

    def test_update(self):
	view_name='user_edit'
	post_data_changes={'username':'testuser2','email':'testuser2@ustadmobile.com','password':'changedpassword','passwordagain':'changedpassword','first_name':'TestChanged','last_name':'User2Changed','role':1,'organisation':1}

	
	"""
	Login required
	UMCloudDj.views.user_update
	"""
	testuser = User.objects.get(username='testuser')
	testuserid = testuser.id;
	requesturl = reverse(view_name, kwargs={'pk':testuserid})
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
	testuser2 = User.objects.get(username='testuser2')
	testuser2id = testuser2.id;
	self.c.get(view_name,kwargs={'pk':testuser2id})
	requesturl = reverse(view_name, kwargs={'pk':testuser2id})
	response = self.c.post(requesturl, post_data_changes)
	changedvalue=User.objects.get(username='testuser2').first_name
	self.assertEqual('TestChanged', changedvalue)
	self.assertRedirects(response, '/userstable/')
	
	post_data_changes={'username':'testuser2','email':'testuser2@ustadmobile.com','password':'','first_name':'TestChangedNP','last_name':'User2Changed','role':1,'organisation':1}
	self.c = Client();
	self.user = User.objects.get(username="testuser")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser', password='hello')
        login = self.c.login(username='testuser', password='hello')
	testuser2 = User.objects.get(username='testuser2')
        testuser2id = testuser2.id;
        self.c.get(view_name,kwargs={'pk':testuser2id})
        requesturl = reverse(view_name, kwargs={'pk':testuser2id})
        response = self.c.post(requesturl, post_data_changes)
        changedvalue=User.objects.get(username='testuser2').first_name
	self.assertEqual('TestChangedNP', changedvalue)
	self.assertRedirects(response, '/userstable/')
	
	
    def test_delete(self):
	view_name='user_delete'
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

	testuser2 = User.objects.get(username="testuser2")
        testuser2id = testuser2.id;

        requesturl = reverse(view_name, kwargs={'pk':testuser2id})
        response = self.c.get(requesturl)
        self.assertEquals(response.status_code,200)
	self.assertContains(response, 'you want to delete')

	response = self.c.post(requesturl)
	self.assertRedirects(response, '/userstable/')

	view_name="user_delete"
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

    
    def test_getassignedcourses_json(self):
	view_name="getassignedcourses_json"
	"""External API, POST parameters, username, password"""
	post_data={'username':'testuser', 'password':'12345'}
	self.c = Client()
	requesturl = reverse(view_name)
	response = self.c.post(requesturl, post_data)
	self.assertContains(response, '"id": "http://www.ustadmobile.com/um-tincan/course/1", "title": "TestCourse"}]')

    def test_get_course_blocks(self):
	view_name="get_course_blocks"
	"""External API, POST parameters, username, passwordi, courseid"""
	post_data={'username':'testuser', 'password':'12345', "courseid":1}
        self.c = Client()
        requesturl = reverse(view_name)
        response = self.c.post(requesturl, post_data)
        self.assertContains(response, '{"id": "http://www.ustadmobile.com/um-tincan/course/1", "blocks": [{"id": "/elpid001", "title": "TestDocument1"}, {"id": "/elpid002", "title": "TestDocument2"}], "description": "This is a test Course", "title": "TestCourse"}')

	post_data={'username':'testuser','password':'12345','courseid':42}
	self.c=Client()
	response = self.c.post(requesturl, post_data)
	self.assertEquals(response.status_code, 500)

	"""Only works with POST requests
	"""
	response=self.c.get(requesturl)
	self.assertEquals(response.status_code, 500)

    def test_invite_to_course(self):
	view_name="invite_to_course"
	"""External API, POST parameters: username, password, blockid, emailids, mode"""
	post_data={'username':'testuser', 'password':'12345', 'blockid':'elpid001', 'emailids':'["varuna.singh@gmail.com", "varuna@ustadmobile.com"]', 'mode':'individual'}
	self.c=Client()
	requesturl = reverse(view_name)
	response=self.c.post(requesturl, post_data)
	self.assertEqual(response.status_code, 200)

    def tearDown(self):
	print("end of User_Delete test")
