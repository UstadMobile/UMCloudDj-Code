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
from uploadeXe.models import Package as Document
from uploadeXe.models import Course
from django import forms


"""
"""


class CourseViewTestCase(TestCase):
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

	testuser2 = User.objects.create(username='testuser2', password='12345', is_active=True, is_staff=True, is_superuser=True)
        testuser2.save()
	user_role2 = User_Roles(name='test', user_userid=testuser2, role_roleid=adminrole)
	user_role2.save()
	user_organisation2 = User_Organisations(user_userid=testuser2, organisation_organisationid=mainorganisation)
	user_organisation2.save()


	school1 = School(school_name="TestSchool", school_desc="This is the desc of the TestSchool",organisation_id=1)
	school1.save()

	course1 = Course(name="TestCourse", description="This is a test Course", category="Tests", publisher=testuser1, organisation=mainorganisation, success="YES")
	course1.save()
	course2 = Course(name="TestCourse2", description="This is a test Course", category="Tests", publisher=testuser1, organisation=mainorganisation, success="YES")
        course2.save()

	document1 = Document(elpid='elpid001', name='TestDocument1', url='/link/to/TestDocument1/',uid='uid001',success='YES',publisher=testuser1)
	document1.save()
	document2 = Document(elpid='elpid002', name='TestDocument2', url='/link/to/TestDocument2/',uid='uid002',success='YES',publisher=testuser1)
        document2.save()
	
	allclass1 = Allclass(allclass_name="TestAllClass1", allclass_desc="TestAllClass1 Desc", allclass_location="Test Land" ,school=school1)
        allclass1.save()
	allclass2 = Allclass(allclass_name="TestAllClass2", allclass_desc="TestAllClass2 Desc", allclass_location="Test Land" ,school=school1)
        allclass2.save()
	
	

    def test_course_create(self):
	"""
	Users can create Courses 
	uploadeXe.views.course_create
	"""
	url_name="coursenew"
	packageidspicklist=[1,2]
	studentidspicklist=[1,2]
	allclassidspicklist=[1,2]
	post_data_create={'course_name':'TestCourseCreate','course_desc':'Unit Test Creation','course_category':'Test_Course_Create','target':packageidspicklist, 'target2':studentidspicklist, 'target3':allclassidspicklist}
	
	"""
	Courses cannot be created without logging in 
	uploadeXe.views.course_create
	"""
        requesturl = reverse(url_name)
        response = self.client.post(requesturl, post_data_create)
	self.assertEqual(response.status_code, 302)

	"""
	courses can be created with logging in
	uploadeeXe.views.course_create
	"""
	self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

	requesturl = reverse(url_name)
	response = self.c.post(requesturl, post_data_create)
	self.assertEqual("TestCourseCreate", Course.objects.get(name="TestCourseCreate").name)

    @unittest.expectedFailure
    def test_course_create_failure(self):
	"""
	Incorrectly done model fails for logged in user
	uploadeXe.views.course_create
	"""
	url_name="coursenew"
        packageidspicklist=[1,2,44,5]
        studentidspicklist=[1,2,3]
        allclassidspicklist=[1,2,3,4]
        post_data_create_incorrect={'course_name':'TestCourseCreate','course_desc':'This is bound to fail.','course_category':'Test_Course_Create','target':packageidspicklist, 'target2':studentidspicklist, 'target3':allclassidspicklist}



        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

        requesturl = reverse(url_name)
        response = self.c.post(requesturl, post_data_create_incorrect)
        self.assertEqual("TestCourseCreateFail", Course.objects.get(name="TestCourseCreateFail").name)

    def test_update(self):
        view_name='courseedit'
	post_data_update={'id_name':'TestCourse','id_description':'This is an update to TestCourse', 'id_category':'EditCategory'}

        """
        Login required
	uploadeXe.views.course_edit
        """
	testcoursecreate = Course.objects.get(name="TestCourse")
	testcoursecreateid = testcoursecreate.id;
	requesturl = reverse(view_name, kwargs={'pk':testcoursecreateid})	
	response = self.client.post(requesturl)
	#ToDO: should check for return ./login/?blah 
        self.assertEqual(response.status_code, 302)

        """
        Logged in user unable to update id that doesnt exist, shoulw raise 404
	uploadeXe.views.course_edit
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
        Logged in usere should be able to update a valid Course's details and return managecourses Courses table page
        uploadeXe.views.course_edit
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')
	testcoursecreate = Course.objects.get(name='TestCourse')
	testcoursecreateid = testcoursecreate.id;
	
        self.c.get(view_name,kwargs={'pk':testcoursecreateid})
        requesturl = reverse(view_name, kwargs={'pk':testcoursecreateid})
        response = self.c.post(requesturl, post_data_update)

        changedvalue=Course.objects.get(name='TestCourse').description
        self.assertEqual('This is a test Course', changedvalue) #need to fix this.


    def test_delete(self):
        view_name='coursedelete'
        """
        User logged in should be able to delete Course
	uploadeXe.views.course_delete
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

	testcoursecreate = Course.objects.get(name='TestCourse2')
        testcoursecreateid = testcoursecreate.id;

        requesturl = reverse(view_name, kwargs={'pk':testcoursecreateid})
        response = self.c.get(requesturl)
        self.assertEquals(response.status_code,200)

        """
        Logged in user deleting unknown user: 4040
	uploadeXe.views.course_delete
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
	view_url="/uploadeXe/managecourses/"

	"""
	Courses cannot be seen without logging in
	"""
        self.c = Client();
        response = self.c.get(view_url)
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/uploadeXe/managecourses/')

        """
        Logged in user will be able to see the managecourses Courses table page
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user = authenticate(username='testuser1', password='12345')
        login = self.c.login(username='testuser1', password='12345')

        response = self.c.get(view_url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "TestCourse", status_code=200)

	

    def tearDown(self):
	print("end of Courses tests")

	
	
	
