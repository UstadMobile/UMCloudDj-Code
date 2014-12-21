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
from organisation.models import Organisation, Organisation_Code
from organisation.models import UMCloud_Package
from organisation.models import User_Organisations
from school.models import School
from allclass.models import Allclass
from users.models import UserProfile
from django import forms
from uploadeXe.models import Package as Document
from uploadeXe.models import Course 
from uploadeXe.models import Ustadmobiletest
from users.models import UserProfile
import os 
from django.conf import settings
import json
import simplejson
import uuid
from datetime import datetime, timedelta
from lrs import forms, models, exceptions
import base64
from django.utils.timezone import utc

class ReportsViewTestCase(TestCase):
    fixtures = ['uploadeXe/fixtures/initial-model-data.json']
    def setUp(self):
	"""
	Have to manually create users and assign relationships 
	for initial testing.
	"""

	adminrole=Role.objects.get(pk=1)
	mainorganisation = Organisation.objects.get(pk=1)
	orgadminrole=Role.objects.get(pk=2)
	studentrole=Role.objects.get(role_name="Student")

	#Super Admin
	testuser = User.objects.create(username='testuser1', \
	    password='12345', is_active=True, is_staff=True, \
		is_superuser=True)
	testuser.save()
	user_role = User_Roles(name="test", user_userid=testuser,\
	    role_roleid=adminrole)
	user_role.save()
	user_organisation = User_Organisations(user_userid=testuser,\
            organisation_organisationid=mainorganisation)
        user_organisation.save()

        #Org Admin 1
        orgadmin01=User.objects.create(username='orgadmin01', \
            password='12345', is_active=True, is_superuser=False)
        orgadmin01.save()
        orgadmin01_role = User_Roles(name="test", user_userid=orgadmin01, \
            role_roleid=orgadminrole)
        orgadmin01_role.save()
        orgadmin01_organisation = User_Organisations(user_userid=orgadmin01, \
            organisation_organisationid=mainorganisation)
        orgadmin01_organisation.save()


	#Student 1
	student1 = User.objects.create(username="student1", password="12345", \
	    email='student1@ustadmobile.com')
	student1.save()
	student_rol1=User_Roles(name="test", user_userid=student1, \
	    role_roleid=studentrole)
	student_rol1.save()
	student_organisation1=User_Organisations(user_userid=student1,\
	    organisation_organisationid=mainorganisation)
	student_organisation1.save()

 	#Student 2
        student2 = User.objects.create(username="student2", password="12345")
        student2.save()
        student_rol2=User_Roles(name="test", user_userid=student2, \
            role_roleid=studentrole)
        student_rol2.save()
        student_organisation2=User_Organisations(user_userid=student2,\
            organisation_organisationid=mainorganisation)
        student_organisation2.save()

	#Student 3
        student3 = User.objects.create(username="student3", password="12345")
        student3.save()
        student_rol3=User_Roles(name="test", user_userid=student3, \
            role_roleid=studentrole)
        student_rol3.save()
        student_organisation3=User_Organisations(user_userid=student3,\
            organisation_organisationid=mainorganisation)
        student_organisation3.save()

	#School 1
	school1 = School(school_name="TestSchool", \
	    school_desc="This is the desc of the TestSchool",organisation_id=1)
        school1.save()

	#AllClass 1
        allclass1 = Allclass(allclass_name="TestAllClassTableTest1", \
	    allclass_desc="TestAllClass1 Desc", allclass_location="Test Land",\
		school=school1)
        allclass1.save()

        allclass1.students.add(student1)
	allclass1.students.add(student2)
	allclass1.students.add(student3)
        allclass1.save()

	#Test Block 1
	test_block=Document(name="unittest01", elpid="ThisIsTheUniqueElpID", \
	    url="//this.is.the/linke/to/the/test/01",uid="123UGOFreei01", \
	    success="YES", publisher=orgadmin01, \
	    tincanid='http://www.ustadmobile.com/um-tincan/activities')
        test_block.save()

	#Test Course 1
	test_course = Course(name="TestCourse", category="Testing",\
	    description="This is a course made for testing", \
		publisher=orgadmin01, organisation=mainorganisation,\
		    tincanid='http://www.ustadmobile.com/um-tincan/course')
	test_course.save()
	test_course.students.add(orgadmin01)
	test_course.save()

	test_course.packages.add(test_block)
        test_course.save()

	test_course.allclasses.add(allclass1)
	test_course.save()

	allstatements=models.Statement.objects.all()
	print("All statements:")
	print(allstatements)

	self.username = "student1"
	self.email = "student1@ustadmobile.com"
	self.password = "12345"
	self.auth = "Basic %s" % base64.b64encode("%s:%s" % (self.username, self.password))

	self.username2 = "student2"
	self.email2 = "student2@ustadmobile.com"
	self.password2 = "student2"
	self.auth2 = "Basic %s" % base64.b64encode("%s:%s" % (self.username2, self.password2))

	#self.firstTime = str(datetime.utcnow().replace(tzinfo=utc).isoformat())
	self.guid1 = str(uuid.uuid1())

	print("Sending Statement1:")
	statement1=json.dumps({"actor":{"mbox":"mailto:student1@ustadmobile.com","name":"Student One","objectType":"Agent"},"verb":{"id":"http://adlnet.gov/expapi/verbs/launched","display":{"en-US":"launched"}},"object":{"id":"http://www.ustadmobile.com/um-tincan/activities/ThisIsTheUniqueElpID","objectType":"Activity","definition":{"name":{"en-US":"Course Title"},"description":{"en-US":"Example activity definition"}}},"context":{"contextActivities":{"parent":[{"id":"http://www.ustadmobile.com/um-tincan/course/1"}]}}})
	statement2=json.dumps({"actor":{"mbox":"mailto:student1@ustadmobile.com","name":"Student One","objectType":"Agent"},"object":{"definition":{"description":{"en-US":"Motivational"},"name":{"en-US":"Motivational"},"type":"http://adlnet.gov/expapi/activities/module"},"id":"http://www.ustadmobile.com/um-tincan/activities/ThisIsTheUniqueElpID/Motivational","objectType":"Activity"},"result":{"duration":"PT0H0M2S"},"verb":{"display":{"en-US":"experienced"},"id":"http://adlnet.gov/expapi/verbs/experienced"}})
	
	view_url="/umlrs/statements"
	response = self.client.post(view_url, statement1, content_type="application/json",
	Authorization=self.auth, X_Experience_API_Version="1.0.0")
	self.assertEqual(response.status_code, 200)
	stmt_id = json.loads(response.content)[0]
	print(stmt_id)
	self.existStmt = models.Statement.objects.get(statement_id=stmt_id)
	self.exist_stmt_id = self.existStmt.statement_id

	print("-------------------------------------------------------")

	response = self.client.post(view_url, statement2, content_type="application/json",
        Authorization=self.auth, X_Experience_API_Version="1.0.0")
        self.assertEqual(response.status_code, 200)
        stmt_id = json.loads(response.content)[0]
        print(stmt_id)
        self.existStmt = models.Statement.objects.get(statement_id=stmt_id)
        self.exist_stmt_id = self.existStmt.statement_id

	print("\nAll statements after insert test")
	allstatements=models.Statement.objects.all()
	print(allstatements)
	allstatementinfos = models.StatementInfo.objects.all()
	for esi in allstatementinfos:
	    #print(esi.school)
	    print(str(esi.statement.id) + " " + str(esi.id) + " " + esi.block.name +\
	    " " + esi.course.name + " " + esi.allclass.allclass_name + " " + esi.school.school_name)

    def test_report_pagi_statements_view(self):
        """
        Tests that logged in user and not logged in user to get to the Report statement page
        """

        """
        Not logged in user will redirect to login page
        """
        view_url="/reports/pagi_allstatements/"
        self.c = Client();
        response = self.c.get(view_url)
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/reports/pagi_allstatements/')

    
    def test_report_statements_view(self):
	"""
        Tests that logged in user and not logged in user to get to the Report statement page
        """

        """
        Not logged in user will redirect to login page
        """
        view_url="/reports/allstatements/"
        self.c = Client();
        response = self.c.get(view_url)
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/reports/allstatements/')

        """
        Logged in user will be able to see the upload page
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user = authenticate(username='testuser1', password='12345')
        login = self.c.login(username='testuser1', password='12345')

        response = self.c.get(view_url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "All statements from your organisation", status_code=200)

    def test_report_selection_view(self):
	"""
        Tests that logged in user and not logged in user to get to the Report mcq page
        """

        """
        Not logged in user will redirect to login page
        """
        view_url="/reports/durationreport_selection/"
        self.c = Client();
        response = self.c.get(view_url)
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/reports/durationreport_selection/')

        """
        Logged in user will be able to see the upload page
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user = authenticate(username='testuser1', password='12345')
        login = self.c.login(username='testuser1', password='12345')

        response = self.c.get(view_url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "Select the filters below", status_code=200)
	

    def test_pagi_statements_db_dynatable(self):
        view_name="pagi_allstatements"
        view_url="/reports/pagi_allstatements/"
        self.c = Client();
        self.user = User.objects.get(username="orgadmin01")
        self.user = authenticate(username='orgadmin01', password='12345')
        login = self.c.login(username='orgadmin01', password='12345')

        response = self.c.get(view_url)
        self.assertContains(response, "All statements from your organisation")

    def test_statements_db_dynatable(self):
	view_name="allstatements"
	view_url="/reports/allstatements/"
	self.c = Client();
	self.user = User.objects.get(username="orgadmin01")
	self.user = authenticate(username='orgadmin01', password='12345')
        login = self.c.login(username='orgadmin01', password='12345')
	
	response = self.c.get(view_url)
	self.assertContains(response, "All statements from your organisation")

    def test_durationreport_selection(self):
	view_name="durationreport_selection"
	view_url="/reports/durationreport_selection/"
	self.c = Client();
	self.user = User.objects.get(username="orgadmin01")
        self.user = authenticate(username='orgadmin01', password='12345')
        login = self.c.login(username='orgadmin01', password='12345')

        response = self.c.get(view_url)
	self.assertContains(response, "Select the filters below to generate a report")

    def test_durationreport(self):
	view_url="/reports/durationreport/"
	self.c = Client();
        self.user = User.objects.get(username="orgadmin01")
        self.user = authenticate(username='orgadmin01', password='12345')
        login = self.c.login(username='orgadmin01', password='12345')

	response = self.c.get(view_url)
	self.assertRedirects(response, "/reports/durationreport_selection/")

	post_data={'since_1_alt':'2014-07-01', 'until_1_alt':'2014-10-28', 'model':['ALL'], 'brand':['1']}
	response = self.c.post(view_url, post_data)
	self.assertContains(response, "Duration Report between 01 Jul 2014 and 28 Oct 2014")

    def test_breakdownreport(self):
	#url(r'^reports/breakdown_report/$', 'report_statement.views.test_heather_report', name='heather_report'), #Breakdown report
	view_url="/reports/breakdown_report/"
	self.c = Client();
        self.user = User.objects.get(username="orgadmin01")
        self.user = authenticate(username='orgadmin01', password='12345')
        login = self.c.login(username='orgadmin01', password='12345')

        response = self.c.get(view_url)
	self.assertEquals(response.status_code, 200)
	self.assertContains(response, "breakdowntreetable")

    def test_all_statements_table(self):
	#url(r'^reports/durationreport/getstatements/(?P<userid>[-\w]+)/$', 'report_statement.views.all_statements_table'), #Get statements by userid
	student1=User.objects.get(username="student1")
	view_url="/reports/durationreport/getstatements/"+str(student1.id)+"/"
	self.c = Client();
        self.user = User.objects.get(username="orgadmin01")
        self.user = authenticate(username='orgadmin01', password='12345')
        login = self.c.login(username='orgadmin01', password='12345')

        response = self.c.get(view_url)
	self.assertContains(response, "User statements")

	
    def test_my_statements_db_dynatable(self):
	view_url="/reports/mystmtsdynadb/"
	self.c = Client();
        self.user = User.objects.get(username="orgadmin01")
        self.user = authenticate(username='orgadmin01', password='12345')
        login = self.c.login(username='orgadmin01', password='12345')

        response = self.c.get(view_url)
        self.assertContains(response, "User statements")
    
    def test_response_report_selection(self):
	#url(r'^reports/responsereport_selection/$', 'report_statement.views.response_report_selection', name='response_report_selection')
	view_url="/reports/responsereport_selection/"
	self.c = Client();
        self.user = User.objects.get(username="orgadmin01")
        self.user = authenticate(username='orgadmin01', password='12345')
        login = self.c.login(username='orgadmin01', password='12345')

        response = self.c.get(view_url)
	self.assertContains(response, "Usage Report Mockups")

    def test_guest_response_report_selection(self):
        #url(r'^reports/responsereport_selection/$', 'report_statement.views.response_report_selection', name='response_report_selection')
        view_url="/reports/responsereport_selection/"
        self.c = Client();

        response = self.c.get(view_url)
        self.assertContains(response, "Usage Report Mockups")
	self.assertContains(response, "Hello Guest")


    def test_test_usage_report(self):
	view_url="/reports/usage_report/"
	self.c = Client();
        self.user = User.objects.get(username="orgadmin01")
        self.user = authenticate(username='orgadmin01', password='12345')
        login = self.c.login(username='orgadmin01', password='12345')

        response = self.c.get(view_url)
	self.assertContains(response, "Usage Report")
	self.assertContains(response, "Indicators")

	post_data= {'until_1_alt': ['2014-12-28'], 'coursesjstreefields': ['allcourses|course.small.png,1|course.small.png'], 'searchcourses': [''], 'since_1': [''], 'searchusers': [''], 'radiotype': ['table'], 'usersjstreefields': ['allschools|school.small.png,1|school.small.png'], 'until_1': [''], 'since_1_alt': ['2014-9-27'], 'totalduration': ['on']}
	#ToDo: remove POST data. This isn't a POST request anymore. 
	#Handled by ajax handler.

	response = self.c.post(view_url, post_data)

    def test_usage_report_data_ajax_handler(self):
	print("All Ajax Blocks:")
	print(Document.objects.all())
	view_url="/fetch/usage_report_data/"
	self.c = Client();
        self.user = User.objects.get(username="orgadmin01")
        self.user = authenticate(username='orgadmin01', password='12345')
        login = self.c.login(username='orgadmin01', password='12345')

        post_data= {'until_1_alt': ['2015-12-28'], 'coursesjstreefields': ['allcourses|course.small.png,1|course.small.png'], 'searchcourses': [''], 'since_1': [''], 'searchusers': [''], 'radiotype': ['table'], 'usersjstreefields': ['allschools|school.small.png,1|school.small.png'], 'until_1': [''], 'since_1_alt': ['2014-9-27'], 'totalduration': ['on']}

        response = self.c.post(view_url, post_data)


    def test_show_statements_from_db(self):
	#url(r'^reports/stmtdb/$','report_statement.views.show_statements_from_db'), #SuperAdmin all statements
	view_url="/reports/stmtdb/"
	self.c = Client();
        self.user = User.objects.get(username="orgadmin01")
        self.user = authenticate(username='orgadmin01', password='12345')
        login = self.c.login(username='orgadmin01', password='12345')

        response = self.c.get(view_url)
	self.assertRedirects(response, '/reports/')

	self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user = authenticate(username='testuser1', password='12345')
        login = self.c.login(username='testuser1', password='12345')
        response = self.c.get(view_url)

        self.assertContains(response, "Statements from Databse")

	
	
    def tearDown(self):
	print("end of Reporting tests")
