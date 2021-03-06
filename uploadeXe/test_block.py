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
    url(r'^list/$', 'list', name='list'),
    url(r'^manage/$', 'manage', name='manage'),
    url(r'^new/$', 'new', name='new'),
    url(r'^edit/(?P<pk>\d+)$', 'edit', name='edit'),
    url(r'^delete/(?P<pk>\d+)$', 'delete', name='delete'),

"""

class DocumentForm(ModelForm): 
    class Meta: 
        model = Document 
        fields = ('name', )

class BlockViewTestCase(TestCase):
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
	
	
    def test_new(self):
	"""
	Users can view block upload form
	uploadeXe.views.new
	"""
	view_url="/uploadeXe/new/"

	"""
        Not logged in user will redirect to login page
        """
        self.c = Client();
        response = self.c.get(view_url)
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/uploadeXe/new/')

        """
        Logged in user will be able to see the new block creation page
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user = authenticate(username='testuser1', password='12345')
        login = self.c.login(username='testuser1', password='12345')

        response = self.c.get(view_url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "Choose your file", status_code=200)

    def test_list_create_bad_files(self):
	"""
        Users can create Blocks
        uploadeXe.views.list
        """
        view_url="/uploadeXe/list/"
	"""
        Logged in users can upload and create
        """
        #try:
        print("Logging in user..")
        if True:
                self.c = Client();
                self.user = User.objects.get(username="testuser1")
                self.user.set_password('hello')
                self.user.save()
                self.user = authenticate(username='testuser1', password='hello')
                login = self.c.login(username='testuser1', password='hello')

                myfiles=[]
                print("Logged in, now opening file..")
                with open('/opt/UMCloudDj/test-invalid.elp',"r") as myfile:
                        myfiles.append(myfile)
                        print(myfiles)
                        courselist=[1,2]
                        requesturl = reverse("list")
                        print(requesturl)
                        post_data={'target':[1],'target2':courselist,'exefile': myfiles}
                        response = self.c.post(requesturl, post_data)
                        print("-------------------------------------------")
                        self.assertEquals(response.status_code, 200)
                        self.assertContains(response, "Failed to upload block. Something is wrong with the file. Please contact us")
		myfiles2=[]
		with open('/opt/UMCloudDj/test-noid.epub',"r") as myfile2:		
			print("Starting..")
                        myfiles2.append(myfile2)
                        print(myfiles2)
                        courselist=[1,2]
                        requesturl = reverse("list")
                        print(requesturl)
                        post_data={'target':[1],'target2':courselist,'exefile': myfiles2}
                        response = self.c.post(requesturl, post_data)
                        print("-------------------------------------------")
                        self.assertEquals(response.status_code, 200)
                        self.assertContains(response, "Upload Failed. A valid title and ID was not found")
		myfiles3=[]
                with open('/opt/UMCloudDj/test-nocontainer.epub',"r") as myfile3:
                        print("Starting..")
                        myfiles3.append(myfile3)
                        print(myfiles3)
                        courselist=[1,2]
                        requesturl = reverse("list")
                        print(requesturl)
                        post_data={'target':[1],'target2':courselist,'exefile': myfiles3}
                        response = self.c.post(requesturl, post_data)
                        print("-------------------------------------------")
                        self.assertEquals(response.status_code, 200)
                        self.assertContains(response, "Failed to upload block. Not a valid epub (no container xml)")

		myfiles4=[]
                with open('/opt/UMCloudDj/test-nopackage.epub',"r") as myfile4:
                        print("Starting..")
                        myfiles4.append(myfile4)
                        print(myfiles4)
                        courselist=[1,2]
                        requesturl = reverse("list")
                        print(requesturl)
                        post_data={'target':[1],'target2':courselist,'exefile': myfiles4}
                        response = self.c.post(requesturl, post_data)
                        print("-------------------------------------------")
                        self.assertEquals(response.status_code, 200)
                        self.assertContains(response, "Failed to upload block. No package file as per container xml")
		myfiles5=[]
                with open('/opt/UMCloudDj/test.zip',"r") as myfile5:
                        print("Starting..")
                        myfiles5.append(myfile5)
                        print(myfiles5)
                        courselist=[1,2]
                        requesturl = reverse("list")
                        print(requesturl)
                        post_data={'target':[1],'target2':courselist,'exefile': myfiles5}
                        response = self.c.post(requesturl, post_data)
                        print("-------------------------------------------")
                        self.assertEquals(response.status_code, 200)
                        self.assertContains(response, "Unable to determine the file type. File is not a .epub or .elp file")
			response=self.c.get(requesturl, post_data)
			self.assertEquals(response.status_code, 200)

		




    def test_list_create(self):
	"""
	Users can create Blocks
	uploadeXe.views.list
	"""
	view_url="/uploadeXe/list/"
	"""
	Users NOT logged in cannot upload
	"""
        #try:

	print("Starting test_list_create..")
	if True:

                with open('/opt/UMCloudDj/test.elp',"r") as myfile:
			courselist=[1,2]
			studentlist=[1]
                        post_data={'target':studentlist, 'target2':courselist,'exefile': myfile}
                        response = self.client.post(view_url, post_data)
			self.assertEquals(response.status_code, 302)
        		self.assertRedirects(response, '/login/?next=/uploadeXe/list/')
		print("Test file found!")

        #except:
	else:
                print("TEST ELP FILE NOT INCLUDED")

	"""
	Logged in users can upload and create
	"""
	#try:
	print("Logging in user..")
	if True:
		self.c = Client();
        	self.user = User.objects.get(username="testuser1")
        	self.user.set_password('hello')
        	self.user.save()
        	self.user = authenticate(username='testuser1', password='hello')
        	login = self.c.login(username='testuser1', password='hello')

		myfiles=[]
		print("Logged in, now opening file..")
                with open('/opt/UMCloudDj/test.elp',"r") as myfile:
			myfiles.append(myfile)
			print(myfiles)
			courselist=[1,2]
			requesturl = reverse("list")
			print(requesturl)
                        post_data={'target':[1],'target2':courselist,'exefile': myfiles}
                        response = self.c.post(requesturl, post_data)
			print("-------------------------------------------")
                        self.assertEquals(response.status_code, 200)
			self.assertContains(response, " has been uploaded.")
			#Because gt1.elp is an old elp without elp lom id, we 
			# fix the successn code manually. 
			#ToDo: Update gt1.elp from new eXe
			print(Document.objects.all())
			self.assertEquals("YES", Document.objects.get(name="zombocom01").success)
			self.assertContains(response, "has been uploaded.")

		#Select and upload the same file again for update
		myfiles=[]
                print("Logged in, now opening file..")
                with open('/opt/UMCloudDj/test.elp',"r") as myfile:
                        myfiles.append(myfile)
                        print(myfiles)
                        courselist=[1,2]
                        requesturl = reverse("list")
                        print(requesturl)
                        post_data={'target':[1],'target2':courselist,'exefile': myfiles}
                        response = self.c.post(requesturl, post_data)
                        print("-------------------------------------------")
                        self.assertEquals(response.status_code, 200)
			self.assertContains(response, "has been uploaded.")
                        #Because gt1.elp is an old elp without elp lom id, we 
                        # fix the successn code manually. 
                        #ToDo: Update gt1.elp from new eXe

                        #self.assertEquals("YES", Document.objects.get(name='zombocom01').success)
			

			

        #except:
	else:
                print("TEST ELP FILE NOT INCLUDED")





    @unittest.expectedFailure
    def test_list_create_failure(self):
	"""
	Incorrectly done model fails for logged in user
	uploadeXe.views.list
	"""
	view_url = "/uploadeXe/list/"
	#try:
	if True:
		self.c = Client();
        	self.user = User.objects.get(username="testuser1")
        	self.user.set_password('hello')
        	self.user.save()
        	self.user = authenticate(username='testuser1', password='hello')
        	login = self.c.login(username='testuser1', password='hello')

                with open('/opt/UMCloudDj/test.elp',"r") as myfile:
                        post_data={'exefile': myfile}
                        response = self.client.post(view_url, post_data)		
			self.assertEqual("YES", Document.objects.get(name="zombocom01").success)
			
			
        #except:
	else:
                print("TEST ELP FILE NOT INCLUDED")


    def test_update(self):
        view_name='edit'
	testuser1=User.objects.get(username='testuser1')
	#b1 = Document(elpid='blockid001', name='TestDocumentEdit', url='/link/to/TestDocumentEdit/',uid='uidb001',success='YES',publisher=testuser1)
	#post_data_update = DocumentForm({'name':'TestDocumentEdit'}, instance=b1)
	post_data_update = {'name':'TestDocumentEdit', "target": [1, 2], "target2": [1]}

        """
        Login required
	uploadeXe.views.edit
        """
	testblockcreate = Document.objects.get(name="TestDocument1")
	testblockcreateid = testblockcreate.id;
	requesturl = reverse(view_name, kwargs={'pk':testblockcreateid})	
	response = self.client.post(requesturl)
        self.assertEqual(response.status_code, 302)
	#self.assertRedirects(response, '/login/?next=/uploadeXe/edit/pk=')

        """
        Logged in user unable to update id that doesnt exist, should raise 404
	uploadeXe.views.edit
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
        Logged in usere should be able to update a valid Block's details and return manage Block table page
        uploadeXe.views.edit
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

	testblockcreate = Document.objects.get(name='TestDocument1')
	testblockcreateid = testblockcreate.id;
	
        self.c.get(view_name,kwargs={'pk':testblockcreateid})
        requesturl = reverse(view_name, kwargs={'pk':testblockcreateid})
        response = self.c.post(requesturl, post_data_update)

        changedvalue=Document.objects.get(name='TestDocumentEdit').name
        self.assertEqual('TestDocumentEdit', changedvalue) #Need to fix this

    def test_delete_block_not_the_publisher(self):
	view_name='delete'
	"""
        User logged in should be able to delete Block
        uploadeXe.views.delete
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser2")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser2', password='hello')
        login = self.c.login(username='testuser2', password='hello')

        testblockcreate = Document.objects.get(name='TestDocument2')
        testblockcreateid = testblockcreate.id;

        requesturl = reverse(view_name, kwargs={'pk':testblockcreateid})
        print(Document.objects.all())
        response=self.c.post(requesturl)
        print(Document.objects.all())
        self.assertEquals('TestDocument2', testblockcreate.name)
	self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, '/uploadeXe/manage/')



    @unittest.expectedFailure
    def test_delete_block(self):
	"""
        User logged in should be able to delete Block
        uploadeXe.views.delete
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

        testblockcreate = Document.objects.get(name='TestDocument2')
        testblockcreateid = testblockcreate.id;

        requesturl = reverse(view_name, kwargs={'pk':testblockcreateid})
        print(Document.objects.all())
        response=self.c.post(requesturl)
        print(Document.objects.all())
	self.assertEquals('TestDocument2', testblockcreate.name)

	

    def test_delete(self):
        view_name='delete'

	"""
	User not loggd in show NOT be able to delete Block
	"""
	testblockcreate = Document.objects.get(name='TestDocument2')
        testblockcreateid = testblockcreate.id;

	self.c = Client();
        requesturl = reverse(view_name, kwargs={'pk':testblockcreateid})
        response = self.c.get(requesturl)
        self.assertEquals(response.status_code,302)
	testblockcreateidstring=str(testblockcreateid)
	self.assertRedirects(response, '/login/?next=/uploadeXe/delete/'+testblockcreateidstring)



        """
        User logged in should be able to delete Block
	uploadeXe.views.delete
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user.set_password('hello')
        self.user.save()
        self.user = authenticate(username='testuser1', password='hello')
        login = self.c.login(username='testuser1', password='hello')

	testblockcreate = Document.objects.get(name='TestDocument2')
        testblockcreateid = testblockcreate.id;

        requesturl = reverse(view_name, kwargs={'pk':testblockcreateid})
        response = self.c.get(requesturl)
        self.assertEquals(response.status_code,200)

	print(Document.objects.all())
	response=self.c.post(requesturl)
  	print(response.status_code)
	print(Document.objects.all())
	self.assertEquals(response.status_code, 302)
	self.assertRedirects(response, '/uploadeXe/manage/')

        """
        Logged in user deleting unknown user: 404
	uploadeXe.views.delete
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

    def test_manage(self):
	view_url="/uploadeXe/manage/"

	"""
	Blocks cannot be seen without logging in
	uploadeXe.views.manage
	"""
        self.c = Client();
        response = self.c.get(view_url)
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/uploadeXe/manage/')

        """
        Logged in user will be able to see the manage Blocks table page
        """
        self.c = Client();
        self.user = User.objects.get(username="testuser1")
        self.user = authenticate(username='testuser1', password='12345')
        login = self.c.login(username='testuser1', password='12345')

        response = self.c.get(view_url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "TestDocument1", status_code=200)

	

    def tearDown(self):
	print("end of Block tests")

	
	
	
