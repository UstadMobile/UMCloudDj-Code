from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, redirect, get_object_or_404 
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib import auth
from django.template import RequestContext
from uploadeXe.models import Package as Document
from uploadeXe.models import Course
from uploadeXe.models import Ustadmobiletest
from uploadeXe.models import Invitation
from uploadeXe.models import Country_Organisation

from uploadeXe.models import Role
from uploadeXe.models import User_Roles
from django.forms import ModelForm
from organisation.models import Organisation
from organisation.models import UMCloud_Package
from organisation.models import User_Organisations
from organisation.models import Organisation_Code
from users.models import UserProfile
from allclass.models import Allclass
from school.models import School
from django import forms
from uploadeXe.views import ustadmobile_export
from uploadeXe.views import handle_block_upload
#from uploadeXe.views import grunt_course

from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
import datetime
import time
import os
import urllib
import urllib2, base64, json
import glob #For file ^VS 130420141454
from uploadeXe.models import Ustadmobiletest
import simplejson
from django.conf import settings
from django.db.models import Q
import random
import commands #Added for getting current location 24092014
from xml.dom import minidom
from lxml import etree
import xml.etree.ElementTree as ET
import hashlib
import zipfile
from django.core.mail import send_mail
import socket
import logging
from django.utils.datastructures import MultiValueDictKeyError
from random import randrange

#For django-resumable uploads
from django.views.generic import View
from resumable.views import ResumableUploadView
from resumable.files import ResumableFile
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
import requests
import uuid

from opds.views import login_basic_auth
import re
from django.http import HttpResponseBadRequest
import random
import string
import phonenumbers

logger = logging.getLogger(__name__)
###################################
# Role CRUD

"""Role Model Form 
"""
class RoleForm(ModelForm):
    class Meta:
        model = Role

"""View to list all roles. Only accessable to super admins
"""
@login_required(login_url='/login/')
def role_table(request, template_name='role/role_table.html'):
    if request.user.is_staff == True:
        roles = Role.objects.all()
        data = {}
    	data['object_list'] = roles
    	roles_as_json = serializers.serialize('json', roles)
    	roles_as_json =json.loads(roles_as_json)
    	return render(request, template_name, {'data':data,\
			 'roles_as_json':roles_as_json})
    else:
	return redirect('home')

"""View to create a new role as per Role Model Form.
Only accessable to Super Admins.
"""
@login_required(login_url='/login/')
def role_create(request, template_name='role/role_form.html'):
    if request.user.is_staff==True:
    	form = RoleForm(request.POST or None)
    	if form.is_valid():
            form.save()
            return redirect('role_table')
    	return render(request, template_name, {'form':form})
    else:
	return redirect('home')

"""View to update an existing role
Only accessable to Super Admins.
"""
@login_required(login_url='/login/')
def role_update(request, pk, template_name='role/role_form.html'):
    if request.user.is_staff == True:
    	role = get_object_or_404(Role, pk=pk)
    	form = RoleForm(request.POST or None, instance=role)
    	if form.is_valid():
            form.save()
            return redirect('role_table')
    	return render(request, template_name, {'form':form})
    else:
	return redirect('home')

"""View to delete an existing role.
Only accessable to super admins
"""
@login_required(login_url='/login/')
def role_delete(request, pk, template_name='role/role_confirm_delete.html'):
    if request.user.is_staff == True:
    	role = get_object_or_404(Role, pk=pk)    
    	if request.method=='POST':
            role.delete()
            return redirect('role_table')
    	return render(request, template_name, {'object':role})
    else:
	return redirect('home')

###################################
# USER CRUD

"""UserProfile model form for additional details about the user
"""
class UserProfileForm(ModelForm):
    raw_id_fields=("user", 'last_activity_date',)
    readonly_fields=("user",'last_activity_date',)
    class Meta:
        model = UserProfile
	fields=('website','company_name','job_title','date_of_birth',\
			'address','phone_number','gender', 'notes', 'last_activity_date')

"""User model form for user addition and update forms.
"""
class UserForm(ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    class Meta:
        model = User
	fields = ('username', 'password','email', 'first_name', 'last_name')
	widgets = {
        #'password': forms.PasswordInput(),
    	}
	
    """Override the save method to update password
    """
    def save(self, commit=True):
    	user = super(UserForm, self).save(commit=False)
	oldpassword = user.password
	newpassword = self.cleaned_data["password"]
	if newpassword:
		logger.info("New password specified")
    		user.set_password(self.cleaned_data["password"])
	else:
		logger.info("password not specified.")
		oldpassword=User.objects.get(pk=user.id).password
		user.password=oldpassword
    	if commit:
		logger.info("commit.")
		user.save()
    	return user

    """For uploading avatars. Not used yet
    """
    """
    def clean_avatar(self):
        avatar = self.cleaned_data['avatar']
        try:
            w, h = get_image_dimensions(avatar)
            #validate dimensions
            max_width = max_height = 100
            if w > max_width or h > max_height:
                raise forms.ValidationError(
                    u'Please use an image that is '
                     '%s x %s pixels or smaller.' % (max_width, max_height))

            #validate content type
            main, sub = avatar.content_type.split('/')
            if not (main == 'image' and sub in ['jpeg', 'pjpeg', 'gif', 'png']):
                raise forms.ValidationError(u'Please use a JPEG, '
                    'GIF or PNG image.')

            #validate file size
            if len(avatar) > (20 * 1024):
                raise forms.ValidationError(
                    u'Avatar file size may not exceed 20k.')

        except AttributeError:
            #Handles case when we are updating the user profile
            #and do not supply a new avatar
            pass

        return avatar
    """

"""Model form for image avatar for users.
Currently not used
"""
class ImageUploadForm(forms.Form):
    avatar = forms.FileField(
        label='Select an image file'
        #content_types = 'application/elp'
    )

"""Upload view for avatar for a user. Not currently made visible. Not used yet.
"""
"""
@login_required(login_url='/login/')
def upload_avatar(request, template_name='myapp/avatar.html'):
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid;
    currentuser=request.user;
    current_user_role = User_Roles.objects.get(user_userid=request.user).role_roleid.role_name;
    try:
	current_user_profile=UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist, e:
	current_user_profile=None
        print("User profile does NOT exist. Creating it..")
        current_user_profile=UserProfile(user=request.user, organisation_requested=organisation)
	current_user_profile.admin_approved=True
        current_user_profile.save()

    current_organisation=organisation

    if request.method == 'POST':
	form=ImageUploadForm(request.POST, request.FILES)
	if form.is_valid():
	    current_user_profile=UserProfile.objects.get(user=request.user)
	    current_user_profile.avatar = request.FILES['avatar']
	    current_user_profile.save()
	    return redirect ('home')
	else:
            #Form isn't POST. 
            print("!!POST FORM IS INVALID!!")
            form = ImageUploadForm() # A empty, unbound form
            # Load documents for the list page
    form=ImageUploadForm()
    current_user = request.user.username
    # Render list page with the documents and the form
    return render_to_response(
        template_name,
        {'form': form, 'current_user': current_user,'currentuser':currentuser,'current_user_role':current_user_role,'current_organisation':current_organisation,'current_user_profile':current_user_profile},
        context_instance=RequestContext(request)
    )
"""


"""View to render all users within the user's organisation.
If super user/system admin all organisation users will be displayed. 
This renders the data to the template that renders the data to a prime
ui table"""
@login_required(login_url='/login/')
def user_table(request, template_name='user/user_table.html', created=None):
    organisation = User_Organisations.objects.get(\
				user_userid=request.user\
					).organisation_organisationid;
    #Syntax to ignore un aproved users.
    users= User.objects.filter(\
	pk__in=User_Organisations.objects.filter(\
	    organisation_organisationid=organisation\
		).values_list(\
		    'user_userid', flat=True)\
	).exclude(\
	    pk__in=UserProfile.objects.filter(\
		admin_approved=False).values_list(\
		    'user', flat=True)\
	).filter(\
	    is_active=True)

    if request.user.is_staff == True:
	users = User.objects.filter(is_active=True)

    user_role = User_Roles.objects.get(user_userid=request.user).role_roleid;
    organisational_admin_role = Role.objects.get(pk=2)

    current_user_role = user_role.role_name;
    current_user = "Hi, " + request.user.first_name + ". You are a " +\
	 current_user_role + " in " +\
		 organisation.organisation_name + " organisation."
    if request.user.is_staff == True:
	current_user = "SUPER ADMIN: Hi, " + request.user.first_name +\
		 ". You are a " + current_user_role + " in " +\
		     organisation.organisation_name +\
			 " organisation and all organisations."
    data={}
    if created:
	try:
		logger.info("A success redirect.")
		usercreated=User.objects.get(id=created)
		if usercreated in users:
			data['state']="Username : " + \
			    usercreated.username + \
  				" created successfully"
		else:
			data['state']=""
	except User.DoesNotExist, e:
		data['state']=""
    else:
    	data['state']=""
    if user_role == organisational_admin_role:
	org_role = True
	try:
                organisation_code=Organisation_Code.objects.get(\
					    organisation=organisation)
        except Organisation_Code.DoesNotExist, e:
                organisation_code = Organisation_Code(\
  					    organisation=organisation)
                random_code = random.randrange(1000000)
                random_org_code=str(organisation.id)+str(random_code)
                organisation_code.code=random_org_code
                organisation_code.save()
	data['organisation_code']=organisation_code

	users_notification= User.objects.filter(\
	    pk__in=User_Organisations.objects.filter(\
		organisation_organisationid=organisation\
		    ).values_list(\
			'user_userid', flat=True)\
	    ).filter(\
	  	pk__in=UserProfile.objects.filter(\
		    admin_approved=False\
			).values_list(\
			    'user', flat=True)\
	    ).filter(\
		is_active=True)
	requestspending = users_notification.count()
    else:
	org_role = False
	requestspending = 0
    data['requestspending']=requestspending
    data['current_user']=current_user
    user_roles = []
    user_organisations = []
    for user in users:
        try:
            role = User_Roles.objects.get(user_userid=user\
                                        ).role_roleid
            organisation = User_Organisations.objects.get(\
                                user_userid=user\
                        ).organisation_organisationid
            user_roles.append(role)
            user_organisations.append(organisation)
        except:
            logger.info("Unable to figure out Role and/or Orga" +\
                "nisation for user: " + str(user.id) + ": " +
                    str(user.username))
            users.exclude(pk=user.pk)
    data['object_list'] = zip(users,user_roles,\
				user_organisations)
    data['role_list'] = user_roles
    data['organisation_list'] = user_organisations
    users_as_json = serializers.serialize('json', users)
    users_as_json =json.loads(users_as_json)
    user_list=zip(users_as_json, user_roles, user_organisations)
    data['org_role']=org_role
    data['user_list']=user_list
    data['users_as_json']=users_as_json
    return render(request, template_name, data)


"""View for orgaisational admins to approve users or reject them
"""
@login_required(login_url='/login/')
def admin_approve_request(request, template_name='user/admin_approve_request_table2.html'):
    role = User_Roles.objects.get(user_userid=request.user\
				 ).role_roleid;
    organisation = User_Organisations.objects.get(\
			user_userid=request.user\
			).organisation_organisationid;
    organisational_admin_role = Role.objects.get(pk=2)
    
    if role == organisational_admin_role:
	roles=Role.objects.all()
	#Syntax to ignore un aproved users.
	users= User.objects.filter(\
	    pk__in=User_Organisations.objects.filter(\
		organisation_organisationid=organisation\
		    ).values_list('user_userid', flat=True)\
	    ).filter(\
		pk__in=UserProfile.objects.filter(\
		    admin_approved=False).values_list(\
			'user', flat=True)).filter(is_active=True)
	
	if request.method == 'POST':
        	post = request.POST;
		for key in request.POST:
			if "_radio" in key:
				value=request.POST[key]
				userid, action = value.split("_")
				if action == '1':
					logger.info("Time to Approve")
					usertoapprove=User.objects.get(pk=userid)
					usertoapprove.is_active=True
					userprofile=UserProfile.objects.get(user=usertoapprove)
					userprofile.admin_approved=True
					userprofile.save()
			
					logger.info("User: " + usertoapprove.username + " approved.")
				if action == '0':
					logger.info("Time to reject..")
					usertoreject=User.objects.get(pk=userid)
					userprofile=UserProfile.objects.get(user=usertoreject)
					usertoreject.is_active=False
					usertoreject.save()
					
		
		return redirect ('user_table')
	user_roles = []
        user_profiles = []
	user_organisations = []
	
        for user in users:
                role = User_Roles.objects.get(user_userid=user).role_roleid
                organisation = User_Organisations.objects.get(\
				user_userid=user).organisation_organisationid
                user_roles.append(role)
                user_organisations.append(organisation)
		userprofile=UserProfile.objects.get(user=user)
		user_profiles.append(userprofile)

	user_mapping = zip(users, user_roles, user_profiles)

        data_as_json=serializers.serialize('json', users)
        data_as_json=json.loads(data_as_json)

        pagetitle="UstadMobile Admin User Requests"
        tabletypeid="tbladminapproverequest"
        table_headers_html=[]
        table_headers_name=[]
        table_headers_html.append("radio")
        table_headers_name.append("Approve")
        table_headers_html.append("radio2")
        table_headers_name.append("Reject")
        #table_headers_html.append("pk")
        #table_headers_name.append("ID")
        table_headers_html.append("fields.first_name")
        table_headers_name.append("First Name")
        table_headers_html.append("fields.last_name")
	table_headers_name.append("Last Name")
	table_headers_html.append("fields.username")
        table_headers_name.append("Username")
        table_headers_html.append("fields.role_name")
        table_headers_name.append("Role")
        table_headers_html.append("fields.gender")
        table_headers_name.append("Gender")
	table_headers_html.append("fields.phonenumber")
	table_headers_name.append("Phone number")
	table_headers_html.append("fields.dateofbirth")
	table_headers_name.append("Date of Birth")

        table_headers_html = zip(table_headers_html, table_headers_name)
        logicpopulation = '{"pk":"{{c.pk}}","model":"{{c.model}}", "username":"{{c.fields.username}}","first_name":"{{c.fields.first_name}}"}{% if not forloop.last %},{% endif %}'
	if not users:
		state="No new user requests"
		return render(request, template_name, {\
				'data_as_json':data_as_json,\
				 'table_headers_html':table_headers_html,\
				 'pagetitle':pagetitle,\
				 'tabletypeid':tabletypeid,\
				 'user_mapping':user_mapping,\
				 'state':state}, \
			context_instance=RequestContext(request))
	else:
        	return render(request, template_name, {\
				'data_as_json':data_as_json, \
				'table_headers_html':table_headers_html, \
				'pagetitle':pagetitle, \
				'tabletypeid':tabletypeid,\
				'user_mapping':user_mapping},\
			 context_instance=RequestContext(request))
    else:
	state="You do not have permission to see this page."
	return render(request, template_name, {'state':state})

"""View to render the create user form and get parameters from POST request and 
create the user
This is the user create by Organisational Admins -> Teachers within their org
using the Management Tab in UMCLOUD.
"""
@login_required(login_url='/login/')
def user_create(request, template_name='user/user_create.html'):
    organisation = User_Organisations.objects.get(\
		user_userid=request.user\
		).organisation_organisationid;
    form = UserForm(request.POST or None)
    #form.fields['username'].widget.attrs['readonly'] = True
    #upform.fields['date_of_birth'].widget.attrs\
    # = {'class':'dobdatepicker'}
    #roles = Role.objects.all()
    roles = Role.objects.exclude(role_name="Administrator")
    organisations = Organisation.objects.all()
    organisations=[]
    organisations.append(organisation)
    allclasses=Allclass.objects.filter(school__in=\
		School.objects.filter(organisation=organisation));
    data = {}
    data['object_list'] = roles
    data['organisation_list'] = organisations
    data['allclass_list'] = allclasses

    if request.method == 'POST':
	post = request.POST;
	password=post['password']
	passwordagain=post['passwordagain']
	if password != passwordagain:
		password=None
		state="The two passwords you gave do not match. Please try again."
                data['state']=state
                return render(request, template_name, data)

	if not user_exists(post['username']):
		
        	user = create_user_more(username=post['username'], \
					email=post['email'], \
					password=post['password'], \
					first_name=post['first_name'], \
					last_name=post['last_name'], \
					roleid=post['role'], \
					organisationid=organisation.id, \
					date_of_birth=post['dateofbirth'], \
					address=post['address'], \
					gender=post['gender'], \
					phone_number=post['phonenumber'], \
					organisation_request=organisation)
		if user:
		    current_user_role = User_Roles.objects.get(\
					user_userid=user.id).role_roleid;
		    student_role = Role.objects.get(pk=6)
		    
		    if current_user_role == student_role:
			selectedallclassids = request.POST.getlist('target');
			
		        for everyallclassid in selectedallclassids:
			    everyallclass = Allclass.objects.get(pk=everyallclassid)
			    everyallclass.students.add(user)
			    everyallclass.save()

		    state="The user " + user.username + " has been created."
		    if 'submittotable' in request.POST:
			data['state']=state
			return redirect('user_table',created=user.id)
			#return render(request, 'user/confirmation.html', data)
			#return redirect('user_table')
		    if 'submittonew' in request.POST:
			statesuccess=1
			data['statesuccess']=statesuccess
			data['state']=state
			data['object_list'] = roles
			return render(request, 'user/user_create.html',data)
		    else:
			return redirect ('user_table')
        	else:
                    state="Could not create user. Make sure you specified all fields."
		    data['state']=state
		    return render(request, template_name, data)
                    #return render_to_response('user/user_create.html',\
		    #{'state':state}, context_instance=RequestContext(request))
                #return redirect("/register", {'state':state})

    	else:
        	#Show message that the username/email address already exists in our database.
		state="That username already exists. Please enter a valid user name"
                data['state']=state
                return render(request, template_name, data)
        	#return redirect('user_table')

    return render(request, template_name, data)

"""View to render user profile (basic information)
Only user logged in is part of the same organisation can view
"""
"""
@login_required(login_url='/login/')
def user_profile(request, pk, template_name='user/user_profile.html'):
    user = get_object_or_404(User, pk=pk)
    organisation = User_Organisations.objects.get(\
                user_userid=request.user).organisation_organisationid;
    users= User.objects.filter(\
        pk__in=User_Organisations.objects.filter(\
            organisation_organisationid=organisation\
                ).values_list('user_userid', flat=True))
    if request.user.is_staff == False:
        if user not in users:
  	    return redirect('user_table')
"""


"""View to render edit form for particular user
Only user in organisation can edit.
"""
@login_required(login_url='/login/')
def user_update(request, pk, template_name='user/user_update.html'):
    user = get_object_or_404(User, pk=pk)
    organisation=User_Organisations.objects.get(\
		user_userid=request.user).organisation_organisationid;
    organisation = User_Organisations.objects.get(\
		user_userid=request.user).organisation_organisationid;
    users= User.objects.filter(\
	pk__in=User_Organisations.objects.filter(\
	    organisation_organisationid=organisation\
		).values_list('user_userid', flat=True))
    if request.user.is_staff == False:
    	if user not in users:
	    return redirect('user_table')
    form = UserForm(request.POST or None, instance=user)
    form.fields['username'].widget.attrs['readonly']=True
    try:
	userprofile=UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist, e:
	userprofile=UserProfile(user=user, organisation_requested=organisation)
	userprofile.admin_approved=True
	userprofile.save()
    upform=UserProfileForm(request.POST or None, instance=userprofile)
    upform.fields['date_of_birth'].widget.attrs = {'class':'dobdatepicker'}
    upform.fields['last_activity_date'].widget.attrs['readonly']=True

    if form.is_valid():
	if upform.is_valid():
		upform.save()
        form.save()
	return redirect('user_table')
    return render(request, template_name, {'form':form,'upform':upform})

"""View to delete a user. Only organisation admin can delete users
"""
@login_required(login_url='/login/')
def user_delete(request, pk, template_name='user/user_confirm_delete.html'):
    user = get_object_or_404(User, pk=pk)
    organisation = User_Organisations.objects.get(\
	user_userid=request.user).organisation_organisationid;
    orgusers= User.objects.filter(\
	pk__in=User_Organisations.objects.filter(\
	    organisation_organisationid=organisation\
		).values_list('user_userid', flat=True))
    if user not in orgusers:
	return redirect('user_table')
    if request.method=='POST':
	role = User_Roles.objects.get(user_userid=request.user\
                                 ).role_roleid;
	if role.id < 3:
	    if user in orgusers:
                user.delete()
	    else:
	    	return redirect('user_table')
	else:
	    return redirect('user_table')
        return redirect('user_table')
    return render(request, template_name, {'object':user})

####################################

"""External facing API to check username and password credentials in POST request. Used for external queries (eg: eXe)
Returns 200: Login success
Returns 403: Login unsuccess
Returns 500: Something wrong with POST request.
"""
@csrf_exempt
def checklogin_view(request):

        if request.method == 'POST':
                logger.info('Login request coming from outside (eXe)')
                username = request.POST.get('username');
                password = request.POST.get('password');
                logger.info("The username is")
		logger.info(username)

                #Code for Authenticating the user
	
		user = authenticate(username=request.POST['username'],\
			 password=request.POST['password'])
                if user is not None:
			authresponse = HttpResponse(status=200)
			authresponse.write("User: " + username + \
				" authentication a success.")
			return authresponse
		else:
			authresponse = HttpResponse(status=403)
			authresponse.write("User: " + username + \
				" authentication failed.")
			return authresponse

"""External API to get username/password authenticated user's course
POST parameters:
username, password
Returns a JSON 
[{"id":1, "title":"Hello World", "last-modified":"2014-10-10 10:10:10"},{...},{..}]
"""
@csrf_exempt
def getassignedecourses_json(request):
	if request.method == "POST":
	    logger.info("Course list request coming from \
			outside (UstadMobile?)")
	    username = request.POST.get('username', False)
	    password = request.POST.get('password', False)
            logger.info("For user: " + str(username))
	    #Authenticate the user
	    user = authenticate(username=\
			request.POST['username'],\
		 password=request.POST['password'])
	    if user is None:
		authresponse = HttpResponse(status=401)
                authresponse.write("Authentication failed for user: " + str(username))
                return authresponse
		
	    if user is not None:
		organisation = User_Organisations.objects.get(\
				user_userid=user)\
				.organisation_organisationid;
		individualorganisation = Organisation.objects.get(\
			organisation_name="IndividualOrganisation")
		allorgcourses = Course.objects.filter(organisation=organisation)

		alluserclasses = Allclass.objects.filter(students__in=[user])
		matched_courses=Course.objects.filter(Q(organisation=\
			organisation, students__in=[user]) | \
			 Q(organisation=organisation, \
			     allclasses__in=alluserclasses))

		#We traditionally search for users who are in their own organisations
		# and the couress are part of their organisation
		# Now that invitation can assign indicidual org uses to other organisation's courses, 
		# we search for courses where students are set but not bound to being in the 
		# organisation where the course was originally ploaded from. 
		if not matched_courses:
		    users_in_individual=User.objects.filter(pk__in=User_Organisations.objects.filter(\
                           organisation_organisationid=individualorganisation\
                            ).values_list('user_userid', flat=True))
		    if user in users_in_individual:
			logger.info("user in individual org")
			matched_courses=Course.objects.filter(Q(\
                         students__in=[user]) | \
                          Q(organisation=organisation, \
                             allclasses__in=alluserclasses))


		logger.info("Matched courses:")
		logger.info(matched_courses)
		json_courses = simplejson.dumps([
			{
			    'id':str(o.tincanid)+'/'+str(o.id),
			    'title':o.name,
			    'last-modified':str(o.upd_date)
			}for o in matched_courses])	
        	return HttpResponse(json_courses, mimetype="application/json")

	else:
	    authresponse = HttpResponse(status=500)
            authresponse.write("Not a POST request. Assigned Course IDs retrival failed.")
            return authresponse

"""External API To get assigned blocks from username/password authenticated user. 
POST parameters: 
username, password
Returns a JSON
[{"22":{""title":"First Block", "last-modified":"date"}},{...},{...}]
"""
"""depricated
@csrf_exempt
def getassignedblocks_json(request):
	if request.method == "POST":
            print("Course list request coming from \
                        outside (UstadMobile?)")
            username = request.POST.get('username', False)
            password = request.POST.get('password', False)
            print("For user: " + username)
            #Authenticate the user
            user = authenticate(username=\
                        request.POST['username'],\
                 password=request.POST['password'])
            if user is not None:
                organisation = User_Organisations.objects.get(\
                                user_userid=user)\
                                .organisation_organisationid;
                allorgcourses = Course.objects.filter(organisation=organisation)
                alluserclasses = Allclass.objects.filter(students__in=[user])
                matched_courses=Course.objects.filter(Q(organisation=\
                        organisation, students__in=[user]) | \
                            Q(organisation=organisation, \
                                allclasses__in=alluserclasses))
		#We need a matched blocks
		
                json_blocks = simplejson.dumps([
                        {o.id:{
                            'title':o.name,
                            'last-modified':str(o.upd_date)
                            }
                        }for o in matched_blocks])
                return HttpResponse(json_blocks, mimetype="application/json")

        else:
            authresponse = HttpResponse(status=500)
            authresponse.write("Not a POST request. Assigned Block IDs retrival failed.")
            return authresponse
"""

"""External API to get blocks for a course for authenticated user 
credentials.
POST parameters:
username, password, course id (primary key)

 Returns JSON
[{"title":"Course Title", "description":"Test Course", "id":"http:/tin.can.id/unique-123-454-6dfd-564fsd", "blocks":[{"id":"http://a.v.c/1212-asdad3d3ad-3d-3","title":"Block Title"},{..},{..}]},{..},{..}]
"""
@csrf_exempt
def get_course_blocks(request):
	if request.method == "POST":
            logger.info("Course list request coming from \
                        outside (UstadMobile?)")
            username = request.POST.get('username', False)
            password = request.POST.get('password', False)
	    try:
	        courseid = request.POST.get('courseid', False)
	        coursetincanprefix=courseid.rsplit('/',1)[0]
	        coursepk=courseid.rsplit('/',1)[1]
	    except:
		authresponse=HttpResponse(status=500)
                authresponse.write("The course ID is either not given or improper. It should be like: http:/a.b.c/d/e/42")
		return authresponse
		
            logger.info("For user: " + username)
            #Authenticate the user
            user = authenticate(username=\
                        request.POST['username'],\
                 password=request.POST['password'])
	    if user is None:
		authresponse=HttpResponse(status=401)
                authresponse.write("Unable to authorise user: " + str(username))
                return authresponse

		
            if user is not None:
                organisation = User_Organisations.objects.get(\
                                user_userid=user)\
                                .organisation_organisationid;
                allorgcourses = Course.objects.filter(organisation=organisation)
                alluserclasses = Allclass.objects.filter(students__in=[user])
                matched_courses=Course.objects.filter(Q(organisation=\
                        organisation, students__in=[user]) | \
                            Q(organisation=organisation, \
                                allclasses__in=alluserclasses))
		try:
		    course=Course.objects.get(id=coursepk, organisation=organisation, tincanid=coursetincanprefix)
		except:
		    authresponse=HttpResponse(status=500)
		    authresponse.write("Course id does not exist (Is your tincanprefix and pk right?) or does not belong to your organisation")
		    return authresponse
		else:
		    all_blocks_in_course=course.packages.all()
		    json_blocks = simplejson.dumps([
			{
			  o.id:{
			    'title':o.name
			      }
		        }for o in all_blocks_in_course])
		    json_blocks = simplejson.dumps({
			"title":course.name,
			"description":course.description, 
			"id":str(course.tincanid)+'/'+str(course.id),
			"blocks":[
                        {
			  "id":o.tincanid+'/'+o.elpid,
			  "title":o.name
                        }for o in all_blocks_in_course]})

               	    return HttpResponse(json_blocks, mimetype="application/json")

        else:
            authresponse = HttpResponse(status=500)
            authresponse.write("Not a POST request. Assigned Block retrival for course failed.")
            return authresponse

"""External API for eXe to POST request invitations
POST parameters:
username, password, blockid(elplomid), emailids(json list:['a@b.c', 'b@c.c'], 
mode:organisation/individual, foreNew: set or not in request, 

Returns stats code
200: Success
500: Failed/Server Error
"""
@csrf_exempt
def invite_to_course(request):
	if request.method == "POST":
            logger.info("Invitation request coming from outside (eXe?)")
	    print(request.POST)
            username = request.POST.get('username', False)
            password = request.POST.get('password', False)
	    blockid  = request.POST.get('blockid', False)
	    emailids = request.POST.get('emailids', False)
	    mode     = request.POST.get('mode', False)
	    emailidsjson = json.loads(emailids)
	    emails=[]
	    for item in emailidsjson:
		emails.append(item)
	    mode     = request.POST.get('mode', False)
            #Authenticate the user
	    blocks=[]
            user = authenticate(username=\
                        request.POST['username'],\
                 password=request.POST['password'])
            if user is None:
		authresponse = HttpResponse(status=401)
		username=request.POST['username']
                authresponse.write("Authorisation failed for user: " + str(username))
                return authresponse
	    else:
		
		individual_organisation = Organisation.objects.get(\
			organisation_name="IndividualOrganisation")
                organisation = User_Organisations.objects.get(\
                                user_userid=user)\
                                .organisation_organisationid;
		try:
		    #Check if the block youa re about to give permissions to, is
		    #in your organisation and exists..
		    block = Document.objects.get(elpid=blockid, success="YES", active=True, \
			publisher__in=User.objects.filter(pk__in=\
			    User_Organisations.objects.filter(\
				organisation_organisationid=organisation).values_list(\
					'user_userid', flat=True)))
		    try:
			blocks.append(block)
			course=Course.objects.get(packages__in=blocks)
		    except:
			authresponse=HttpResponse(status=504)
			authresponse.write("Course with Block id not found. Please publish block first")
			return authresponse
		except:
		    authresponse=HttpResponse(status=503)
		    authresponse.write("Block requested does not exist or is in your organisation")
		    return authresponse
		else:
		    for current_email in emails:
			logger.info("Current email:")
			logger.info(current_email)
			try:
		            if mode == "organisation":
		    	    	invitation=Invitation(\
				    organisation=organisation, invitee=user,\
				    email=current_email,\
			  	    block=block, course=course)
			    elif mode == "individual":
			    	invitation = Invitation(\
				    organisation=individual_organisation,\
				    invitee=user,\
				    email=current_email, \
				    block=block, course=course)
			    else:
			    	authresponse=HttpResponse(status=500)
                    	    	authresponse.write("Unable to figure the mode out..")
                    	    	return authresponse
			    invitation.save()
			    logger.info("All good, time to send emails..")
			    sender=user.first_name + ' ' + user.last_name
			    if sender == "":
				sender=user.username
			    invitation_id=str(invitation.invitation_id)
			    hostname="http://umcloud1.ustadmobile.com"
			    devhostname="http://54.77.18.106:8004"
			    try:
				logger.info(socket.gethostname())
			    	send_mail('You are invited to join ' + course.name, 'Hi,\n' +\
				'\n' + sender + ' has invited you to access the course ' + course.name + \
				' using eXe course creation software.\nPlease click the link to acess the course.' +\
				 '\nClick here: '+hostname+'/register/invitation/?id='+invitation_id +\
					 '\n(Do not share this link. It is private to you). \
				\n\nRegards, \nUstad Mobile\ninfo@ustadmobile.com\n@ustadmobile', \
				 'info@ustadmobile.com' , [current_email], fail_silently=False)
			    except:
				authresponse = HttpResponse(status=506)
				authresponse.write("Failed to send emails. Check if you have set it up and the settings are correct.")
				return authresponse
			    #@@@@@@@@@@@@@@@@@@@@@@@@@
		  	    #@@@@@@@@@@@@@@@@@@@@@@@@@
			    #Email this invitation code.
			    #@@@@@@@@@@@@@@@@@@@@@@@@@
			    #@@@@@@@@@@@@@@@@@@@@@@@@@
			except:
                            authresponse = HttpResponse(status=500)
                            authresponse.write("Unable to create invitation object.")
                            return authresponse
		    authresponse = HttpResponse(status=200)
		    authresponse.write("Invitation objects created. Emails sent")
		    return authresponse



                allorgcourses = Course.objects.filter(organisation=organisation)
                alluserclasses = Allclass.objects.filter(students__in=[user])
                matched_courses=Course.objects.filter(Q(organisation=\
                        organisation, students__in=[user]) | \
                            Q(organisation=organisation, \
                                allclasses__in=alluserclasses))

        else:
            authresponse = HttpResponse(status=500)
            authresponse.write("Not a POST request. Invitation set up failed.")
            return authresponse


"""External API. Original xml implementation of getting assigned courses and blocks
"""
@csrf_exempt
def getassignedcourseids_view(request):
        if request.method == 'POST':
                logger.info('Login request coming from outside (eXe)')
                username = request.POST.get('username',False);
                password = request.POST.get('password', False);
                #Code for Authenticating the user
		logger.info("Username;")
		logger.info(username)
                user = authenticate(username=request.POST['username'], password=request.POST['password'])
                if user is not None:
			xmlreturn="<?xml version=\"1.0\" ?>"
			xmlreturn+="<getasssignedcourseids><username>"+username+"</username>"
			organisation = User_Organisations.objects.get(user_userid=user).organisation_organisationid;
			#Check and get list of courses..
			
			#we first get all courses from the user's organisation
			allorgcourses = Course.objects.filter(organisation=organisation)
			alluserclasses = Allclass.objects.filter(students__in=[user])
			matchedcourses=Course.objects.filter(Q(organisation=organisation, students__in=[user]) | Q(organisation=organisation, allclasses__in=alluserclasses))
			assigned_course_ids=[]
			assigned_course_packages=[]
			assigned_course_packageids=[]
			if matchedcourses: 	#If there are matched courses
				for everycourse in matchedcourses:
					xmlreturn+="<course>"
					xmlreturn+=everycourse.name+"</course>"
					xmlreturn+="<id>"+str(everycourse.id)+"</id>"
		
					assigned_course_ids.append(everycourse.id)
					everycoursepackages = everycourse.packages.all()
					if everycoursepackages:
						assigned_course_packages.extend(everycourse.packages.all())

					xmlreturn+="<packages>"
					for everypackage in everycoursepackages:
						xmlreturn+="<package>"
						xmlreturn+=everypackage.name
						xmlreturn+="</package>"
						xmlreturn+="<id>"
						xmlreturn+=str(everypackage.id)
						xmlreturn+="</id>"
						xmlreturn+="<folder>"
						xmlreturn+=everypackage.uid + "/" + everypackage.name
						xmlreturn+="</folder>"
						xmlreturn+="<xmldownload>"
						xmlreturn+=everypackage.uid + "/" + everypackage.name + "_ustadpkg_html5.xml"
						xmlreturn+="</xmldownload>"
					

					xmlreturn+="</packages>"
				xmlreturn+="</getassignedcourseids>"
				for everypackage in assigned_course_packages:	
					everypackageid = everypackage.id
					assigned_course_packageids.append(everypackageid)
	
                        	authresponse = HttpResponse(status=200)
				#authresponse.write("Courses found for user: " + username)
				authresponse.write(xmlreturn)
				authresponse['assigned_course_ids']=assigned_course_ids
                        	return authresponse
			else:
				authresponse = HttpResponse(status=404)
				authresponse['assigned_course_ids']=assigned_course_ids
				authresponse.write("No courses found for username: " + username)
				return authresponse
                else:
                        authresponse = HttpResponse(status=403)
                        authresponse.write("User: " + username + " authentication failed.")
                        return authresponse
	else:
		authresponse = HttpResponse(status=500)
		authresponse.write("Not a POST request. Assigned Course IDs retrival failed.")
		return authresponse


"""
External API to check if requested user id's role is a teacher
Takes in user's authentication
"""
@csrf_exempt
def is_teacher(request):
    state, authresponse = login_basic_auth(request)
    if state == False:
        return authresponse
    if state == True:
        request.user = authresponse
    try:
        user=request.user
    except:
        authresponse = HttpResponse(status=401)
        authresponse.write("Not logged in or unknown user.")
        return authresponse
    else:
        if user is not None:
	    teacher_role = Role.objects.get(role_name='Teacher')
	    user_role = User_Roles.objects.get(user_userid=user).role_roleid
	    json_result = simplejson.dumps({
                'role':user_role.role_name })
            return HttpResponse(json_result, mimetype="application/json")
		
	else:
	    authresponse = HttpResponse(status=401)
	    authresponse.write("Unable to get user.")
	    return authresponse


"""
External API to get all the classes assigned to teacher id given
Takes in teacher authentication
"""
@csrf_exempt
def get_teacher_allclasses(request):
    state, authresponse = login_basic_auth(request)
    if state == False:
        return authresponse
    if state == True:
        request.user = authresponse
    try:
        user=request.user
    except:
        authresponse = HttpResponse(status=401)
        authresponse.write("Not logged in or unknown user.")
        return authresponse
    else:
        if user is not None:
            teacher_role = Role.objects.get(role_name='Teacher')
            user_role = User_Roles.objects.get(user_userid=user).role_roleid
	    if (user_role == teacher_role):
		allteachers=[]
 		allteachers.append(user)
 		allclasses=Allclass.objects.filter(teachers__in=allteachers);
		
		json_allclasses = simplejson.dumps([
                        {
                            'id':str(o.id),
                            'name':o.allclass_name,
                        }for o in allclasses])
                return HttpResponse(json_allclasses, mimetype="application/json")

	    else:
		authresponse = HttpResponse(status=401)
		authresponse.write("Unauthorized. Not a teacher")
		return authresponse
                
        else:
            authresponse = HttpResponse(status=401)
            authresponse.write("Unable to get user.")
            return authresponse


"""
External API to get a list of all student ids in a class id given
Takes in teacher authentication
"""
@csrf_exempt
def get_allclass_students(request, pk):
    state, authresponse = login_basic_auth(request)
    if state == False:
        return authresponse
    if state == True:
        request.user = authresponse
    try:
        user=request.user
    except:
        authresponse = HttpResponse(status=401)
        authresponse.write("Not logged in or unknown user.")
        return authresponse
    else:
        if user is not None:
            teacher_role = Role.objects.get(role_name='Teacher')
            user_role = User_Roles.objects.get(user_userid=user).role_roleid
            if (user_role == teacher_role):
		allclass = Allclass.objects.get(pk=pk)
	  	if allclass is not None:
		    #Check if the teacher is assigned to this course.
		    allclassteachers = allclass.teachers.all()
	 	    if user in allclassteachers:
		    	all_students = allclass.students.all()
		    	json_allstudents = simplejson.dumps([
			    {
			    	'id':str(o.id),
			    	'username':str(o.username),
				'full_name':str(o.first_name) + " " + str(o.last_name),
			    }for o in all_students])
		    	return HttpResponse(json_allstudents, mimetype="application/json")
		    else:
			authresponse = HttpResponse(status=403)
			authresponse.write("You cannot view this class. You are not a teacher of it.")
			return authresponse

		else:
		    authresponse = HttpResponse(status=400)
                    authresponse.write("The class id was invalid.")
                    return authresponse
		    
            else:
                authresponse = HttpResponse(status=401)
                authresponse.write("Unauthorized. Not a teacher")
                return authresponse

        else:
            authresponse = HttpResponse(status=401)
            authresponse.write("Unable to get user.")
            return authresponse




"""Method / Function to handle resumablejs uploads to UMCloudDj
"""
"""
def handle_resumable_js(request):
    chunks_dir = getattr(settings, 'FILE_UPLOAD_TEMP_DIR', None)
    if not chunks_dir:
	raise ImproperlyConfigured(
	    'You must set settings.FILE_UPLOAD_TEMP_DIR')
	
"""

class ResumableBlockUploadView(View):
    def get(self, *args, **kwargs):
        """Checks if chunk has allready been sended.
        """
	try:
            r = ResumableFile(self.storage, self.request.GET)
            if not (r.chunk_exists or r.is_complete):
                return HttpResponse('chunk not found', status=404)
            return HttpResponse('chunk already exists')
	except:
	    return HttpResponse("Not a valid request..", status=400)

    def post(self, *args, **kwargs):

        try:
	    logger.info('Block Upload request (resumable?) coming from outside (eXe?)')
            if self.request.POST.get('forceNew') != 'false':
                forceNew = self.request.POST.get('forceNew');
            else:
                forceNew = None
            if self.request.POST.get('noAutoassign') != 'false':
                noAutoassign = self.request.POST.get('noAutoassign');
            else:
                noAutoassign = None

	    state, authresponse = login_basic_auth(self.request)
	    user = None
	    if state == True:
		user = authresponse

            if user is not None:
                logger.info("Login a success!..")
                #We Sign in the user..
                login(self.request, user)

                organisation = User_Organisations.objects.get(\
                   user_userid=user).organisation_organisationid;

                #This is the new thing
                data = {}
	    else:
		return HttpResponse(status=403)
	except:
	    logger.info("Unable to login / check authentication for request..")
	    return HttpResponse(status=500)

        """Saves chunks then checks if the file is complete.
        """
	logger.info("Getting chunk..")
        chunk = self.request.FILES.get('file')
        r = ResumableFile(self.storage, self.request.POST)
        if r.chunk_exists:
            return HttpResponse('chunk already exists')
	logger.info("Processing chunk..")
        r.process_chunk(chunk)
	logger.info("    Checking if complete..")
        if r.is_complete:
	    logger.info("Completed. Now deleting chunks and starting export..")
            filename = self.process_file(r.filename, r)
            r.delete_chunks()
	    #Now you can process things..

 	    if filename:
		logger.info("Chunks processed Okay. Got updated filename: " + filename)
	        exefile = "eXeUpload/UPLOAD_CHUNKS/" +  filename
	    else:
		logger.info("Unable to process chunks in resumable upload.")
		authresponse = HttpResponse(status=500)
		authresponse['error']="Unable to process chunks in resumable upload."
		return authresponse

	    blockcourse = True
	    data['forceNew'] = forceNew
            data['noAutoassign'] = noAutoassign
            data['blockCourse'] = blockcourse
	    user = self.request.user
	    data['publisher'] = user
            return_value, newdoc, data_updated = handle_block_upload(exefile, data)

            #If block failed to upload and / or validatinon failed
            if return_value == False or return_value is None:
                #return render(self.request, self.template_name, data_updated)
		authresponse = HttpResponse(status=500)
                authresponse.write("Invalid ")
		authresponse.write(data_updated['state'])
		authresponse['error']=data_updated['state']
		return authresponse
            else:
                data = data_updated

            rete = return_value[0]
            elpepubid = return_value[1]
            uid = return_value[2]
            unid = return_value[3]
            elpiname = return_value[4]
            uidwe = return_value[4]
            elplomid = return_value[5]
	    blockcourseid = return_value[6]

	    if rete=="newsuccess":
		print("A success export")
                courseURL = '/media/eXeExport' + '/' + unid + '/' + elpiname + '/' + 'deviceframe.html'
                setattr(newdoc, 'url', "cow")
                newdoc.save()
                setattr(newdoc, 'success', "YES")
                setattr(newdoc, 'url', courseURL)
                setattr(newdoc, 'name', uidwe)
                setattr(newdoc, 'publisher', user)

                newdoc.save()
                print("Existing Id: " + str(newdoc.elpid))
                if newdoc.elpid=='replacemewithxmldatas':
                    if elpepubid != None:
                        setattr(newdoc, 'elpid', elpepubid)
                        newdoc.save()
                    else:
                        newdoc.success="NO"
                        state="Couldn't get block's Unique ID. Please check."
                        newdoc.save()
                        logger.info("!!No Block ID got from Block file uploaded!!")
                        uploadresponse=HttpResponse(status=500)
                        uploadresponse.write("Failed to create and export")
                        uploadresponse['error'] = "Exe failed to export"
                        return uploadresponse

		"""
                logger.info("Going to create the course...")
                #Update  14th October 2014: We want blocks coming from eXe to be created as single courses.
                blockcourse = Course(name=newdoc.name, category="-",\
                    description="Block course for "+newdoc.name,\
                         publisher=user, organisation=organisation)
                blockcourse.save()
                logger.info("assigning students to course..")
                try:
                    for every_user in newdoc.students.all():
                        blockcourse.students.add(every_user)
                        blockcourse.save()
                    logger.info("Assigning block to course..")
                    blockcourse.packages.add(newdoc);
                    setattr(blockcourse, 'success', "YES")
                    blockcourse.save()
                    logger.info("Block course: " + blockcourse.name + " saved successfully!")
                except:
                    logger.info("Could not create course..")
                    newdoc.students.remove(all);
                    newdoc.delete()
                    blockcourse.delete()
		"""


                #form is valid (upload file form)
                # Redirect to the document list after POST
		blockcourse = None
		try:
		    print("Getting block course..")
		    blockcourse = Course.objects.get(\
			pk=blockcourseid)
		    print("Got blockcourse : " + str(blockcourse.id))
		except:
		    print("Unable to get blockcourse.")
		
                uploadresponse = HttpResponse(status=200)
                uploadresponse['courseid'] = getattr(blockcourse, 'id')
                uploadresponse['coursename'] = getattr(blockcourse, 'name')
                return uploadresponse

            elif rete=="newfail":
                uploadresponse=HttpResponse(status=500)
                uploadresponse.write("Failed to create and export")
                uploadresponse['error'] = "Exe failed to export"
                return uploadresponse

            elif rete=="newfailcopy":
                uploadresponse=HttpResponse(status=500)
                uploadresponse.write("Exported, did not complete.")
                uploadresponse['error'] = "Exported but failed to complete"
                return uploadresponse

            elif rete=="updatesuccess":
                setattr(newdoc, 'success', "NO")
                setattr(newdoc, 'active', False)
                newdoc.save()
                newdoc.delete()

                # Redirect to the document list after POST
                uploadresponse = HttpResponse(status=200)
                uploadresponse.write("Course's block updated.")
                return uploadresponse

            elif rete=="updatefail":
                uploadresponse = HttpResponse(status=500)
                uploadresponse.write("Exe Export faild but uploaded")
                uploadresponse['error'] = "Exe export failed to start"
                return uploadresponse



	    
	print("Continuing..")
        return HttpResponse()

    def process_file(self, filename, file):
        """Process the complete file.
        """
	print("Doing additional things to the file..")
	ext = "um."
        filename = "%s.%s" % (uuid.uuid4(), ext) + filename
	print("filename: " + str(filename))

	if self.storage.save(filename, file):
	    return filename
	else:
	    return False
	

    @property
    def chunks_dir(self):
        chunks_dir = getattr(settings, 'FILE_UPLOAD_TEMP_DIR', None)
        if not chunks_dir:
            raise ImproperlyConfigured(
                'You must set settings.FILE_UPLOAD_TEMP_DIR')
        return chunks_dir

    @property
    def storage(self):
        return FileSystemStorage(location=self.chunks_dir)


"""External API to send elp file as POST request with authentication to upload and set the block to a course
by default
POST parameters:
username, password, foreceNew(set or not set), noAutoassign(set or not set)

"""
@csrf_exempt
def sendelpfile_view(request):
	logger.info("Receiving the elp file..")

	if request.method == 'POST':
		logger.info('Login request coming from outside (eXe)')
		username = request.POST.get('username');
		password = request.POST.get('password');
		if request.POST.get('forceNew') != 'false':
		    forceNew = request.POST.get('forceNew');
		else:
		    forceNew = None
		if request.POST.get('noAutoassign') != 'false':
		    noAutoassign = request.POST.get('noAutoassign');
		else:
		    noAutoassign = None
		logger.info("The username is")
		logger.info(username)
		logger.info("The file: ")
		logger.info(request.FILES)

		#Code for Authenticating the user
		user = authenticate(username=request.POST['username'], \
				password=request.POST['password'])
    		if user is not None:
			logger.info("Login a success!..")
        		#We Sign the user..
			login(request, user)

			organisation = User_Organisations.objects.get(\
				user_userid=user).organisation_organisationid;

			#This is the new thing
			data = {}

			exefile = request.FILES['exeuploadelp']
			print("exefile type:")
			print(type(exefile))
			
			data['publisher'] = user
		 	data['forceNew'] = forceNew
			data['noAutoassign'] = noAutoassign
            		return_value, newdoc, data_updated = handle_block_upload(exefile, data)
            		#This is the new thing

            		#If block failed to upload and / or validatinon failed
            		if return_value == False or return_value is None:
                	    return render(request, template_name, data_updated)
            		else:
                	    data = data_updated


            		rete = return_value[0]
	                elpepubid = return_value[1]
            		uid = return_value[2]
            		unid = return_value[3]
            		elpiname = return_value[4]
			uidwe = return_value[4]
           	 	elplomid = return_value[5]

            		if rete=="newsuccess":
			  	print("A success export")
                		courseURL = '/media/eXeExport' + '/' + unid + '/' + elpiname + '/' + 'deviceframe.html'
                		setattr(newdoc, 'url', "cow")
                		newdoc.save()
                		setattr(newdoc, 'success', "YES")
                		setattr(newdoc, 'url', courseURL)
                		setattr(newdoc, 'name', uidwe)
                		setattr(newdoc, 'publisher', user)

                		newdoc.save()
				print("Existing Id: " + str(newdoc.elpid))
				if newdoc.elpid=='replacemewithxmldatas':
                    		    if elpepubid != None:
                        		setattr(newdoc, 'elpid', elpepubid)
                        		newdoc.save()
                    		    else:
                        		newdoc.success="NO"
                        		state="Couldn't get block's Unique ID. Please check."
                        		newdoc.save()
                        		print("!!No Block ID got from Block file uploaded!!")
					uploadresponse=HttpResponse(status=500)
                                	uploadresponse.write("Failed to create and export")
                                	uploadresponse['error'] = "Exe failed to export"
                                      	return uploadresponse

				logger.info("Going to create the course...")
				#Update  14th October 2014: We want blocks coming from eXe to be created as single courses.
				blockcourse = Course(name=newdoc.name, category="-",\
					 description="Block course for "+newdoc.name,\
						 publisher=user, organisation=organisation)
				blockcourse.save()
				logger.info("assigning students to course..")
				try:
				    for every_user in newdoc.students.all():
				    	blockcourse.students.add(every_user)
					blockcourse.save()
				    logger.info("Assigning block to course..")	
				    blockcourse.packages.add(newdoc);
				    setattr(blockcourse, 'success', "YES")
				    blockcourse.save()
				    logger.info("Block course: " + blockcourse.name + " saved successfully!")
				except:
				    logger.info("Could not create course..")
				    newdoc.students.remove(all);
				    newdoc.delete()
			    	    blockcourse.delete()

	
                		#form is valid (upload file form)
                		# Redirect to the document list after POST
				uploadresponse = HttpResponse(status=200)
                        	uploadresponse['courseid'] = getattr(blockcourse, 'id')
                        	uploadresponse['coursename'] = getattr(blockcourse, 'name')
                        	return uploadresponse

			elif rete=="newfail":
				uploadresponse=HttpResponse(status=500)
				uploadresponse.write("Failed to create and export")
				uploadresponse['error'] = "Exe failed to export"
				return uploadresponse

			elif rete=="newfailcopy":
				uploadresponse=HttpResponse(status=500)
                                uploadresponse.write("Exported, did not complete.")
                                uploadresponse['error'] = "Exported but failed to complete"
                                return uploadresponse

            		elif rete=="updatesuccess":
                		setattr(newdoc, 'success', "NO")
				setattr(newdoc, 'active', False)
                		newdoc.save()
				newdoc.delete()
	
                		# Redirect to the document list after POST
				uploadresponse = HttpResponse(status=200)
				uploadresponse.write("Course's block updated.")
				return uploadresponse

			elif rete=="updatefail":
                                uploadresponse = HttpResponse(status=500)
                                uploadresponse.write("Exe Export faild but uploaded")
                                uploadresponse['error'] = "Exe export failed to start"
                                return uploadresponse
		else:
			uploadresponse = HttpResponse(status=403)
                        uploadresponse.write("LOGIN FAILED. USERNAME and PASSWORD DO NOT MATCH. AUTHENTICATION FAILURE")
                        return uploadresponse
        else:
                logger.info('Not a POST request');

                uploadresponse = HttpResponse(status=500)
                uploadresponse.write("Request is not POST")
                uploadresponse['error'] = "Request is not POST"
                return uploadresponse


"""External invitation links will be checked  and redirected here. 
If valid, will redirect to organisation or individual user creation
page with email adress pre filled.
Upon user creation, will assign user to course
"""
#@csrf_exempt
def check_invitation_view(request):
	invitationid = request.GET.get('id')
	logger.info("Invitation id is:" + str(invitationid) )
	try:
	    invitation = Invitation.objects.get(invitation_id=invitationid, done=False)
	    logger.info("Starting registration process for : " + invitation.email)

	except:	
	    try:
		invitation=Invitation.objects.get(invitation_id=invitationid)
		if invitation:
		    return render_to_response('login.html', {\
			'statesuccess':1,\
			'state':'Your account is created. Log in to see your course',\
			'invitation':invitation\
			}, context_instance=RequestContext(request))
	    except:
	        logger.info("invitation id does not exists")
	        authresponse = HttpResponse(status=403)
	        authresponse.write("Invalid invitation id.")
	        if invitationid:
	            return authresponse
		else:
	            return redirect('register_selection')
	else:
	    try:
		alreadyauser=User.objects.get(email=invitation.email)
		if alreadyauser:
			invitation.block.students.add(alreadyauser)
		 	invitation.block.save()

			invitation.course.students.add(alreadyauser)
			invitation.course.save()

			invitation.done = True
			invitation.save()
			c = {}
        		c.update(csrf(request))
        		return render_to_response('login.html', {\
						'invitation':invitation\
				}, context_instance=RequestContext(request))
	    except:
		logger.info("A fresh new user is to be created..")
	    individual_organisation = Organisation.objects.get(\
				organisation_name="IndividualOrganisation")
	    if invitation.organisation  == individual_organisation:
		logger.info("This invitation is for individual organisation")
		c = {}
        	c.update(csrf(request))
        	return render(request, 'user/user_create_website_individual.html', \
			{'invitationemail':invitation.email, \
			 'invitationcourse':invitation.course,\
			 'invitationid':invitation.id})
	    elif invitation.organisation:
		logger.info("This invitation is for " + \
			invitation.organisation.organisation_name + " organisation.")
		print("This invitation is for:"+\
		    invitation.organisation.organisation_name)
		try:
		    organisationalcode = Organisation_Code.objects.get(\
					organisation=invitation.organisation).code
		except Organisation_Code.DoesNotExist, e:
		    oc=Organisation_Code.objects.create(organisation=invitation.organisation)
		    random_code=randrange(1000000)
		    random_org_code=str(invitation.organisation.id)+\
                                        str(random_code)
		    oc.code=random_org_code
		    oc.save()
		    organisationalcode=Organisation_Code.objects.get(\
			organisation=invitation.organisation).code
		    
		    
		organisation_name = invitation.organisation.organisation_name
		state="Valid code"
		
	 	c = {}
                c.update(csrf(request))
                return render(request, 'user/user_create_website_organisation.html',\
		 {'invitationemail':invitation.email, \
		  'invitationcourse':invitation.course,\
		  'invitationid':invitation.id, \
		  'organisationalcode':organisationalcode,\
		  'organisation_name':organisation_name, 'state':state})

            authresponse = HttpResponse(status=200)
            authresponse.write("Continuing...")
            return authresponse

"""Gets block details, url and folder.
GET request takes in full url tincan prefix plus elp lom id as "id"
Returns JSON
"""
def getblock_view(request):
        blockid = request.GET.get('id')
	try:
	    blockid= blockid.rsplit('/',1)[1]
	    blocktincanid=blockid.rsplit('/',1)[0]
	except:
	    pass
        logger.info("External request of public course..")

        try:
                matchedCourse = Document.objects.filter(\
			elpid=str(blockid)).get(elpid=str(blockid))
                if matchedCourse:
                        logger.info("Course exists!")
                        logger.info("The unique folder for course id: " +\
			    blockid + " is: " + matchedCourse.uid +\
				 "/" + matchedCourse.name)
                        coursefolder = matchedCourse.uid + "/" + \
			    matchedCourse.name

                        json_course = simplejson.dumps({
                            'blockurl':coursefolder })
                        return HttpResponse(json_course, mimetype="application/json")
                else:
                        response2 =  HttpResponse(status=403)
                        logger.info("Sorry, a course of that ID was not found globally")
                        response2.write("folder:na")
                        return response2

        except Document.DoesNotExist, e:
                response2 =  HttpResponse(status=403)
                logger.info("Sorry, a course of that ID was not found globally")
                response2 = HttpResponse(status=403)
                response2.write("folder:na")
                return response2
        
        return redirect("/")


"""Gets block details as GET parameters and sets headers and resposne body with block details.
This was the original implementation for the app to talk and download blocks. Retained because 
currently the app uses this API.
"""
def getcourse_view(request):
	courseid = request.GET.get('id')
	logger.info("External request of public course..")

	try:
		matchedCourse = Document.objects.filter(id=str(courseid)).get(id=str(courseid))
        	if matchedCourse:
                	logger.info("Course exists!")
                	logger.info("The unique folder for course id: " + courseid + " is: " + matchedCourse.uid + "/" + matchedCourse.name)
                	coursefolder = matchedCourse.uid + "/" + matchedCourse.name
                	xmlDownload = coursefolder + "_ustadpkg_html5.xml"
                	data = {
                        	'folder' : coursefolder,
                        	'xmlDownload' : xmlDownload
                	}
                	#response =  HttpResponse(status=200)
                	response = HttpResponse("folder:" + coursefolder)
                	response = HttpResponse("xmlDownload:" + xmlDownload)
                	response = render_to_response("getcourse.html", {'coursefolder': coursefolder, 'xmlDownload': xmlDownload}, context_instance=RequestContext(request))
                	response['folder'] = coursefolder
                	response['xmlDownload'] = xmlDownload
                	return response
			json_course = simplejson.dumps({
                            'blockurl':coursefolder })
                	return HttpResponse(json_course, mimetype="application/json")

			
		else:
                	response2 =  HttpResponse(status=403)
                	logger.info("Sorry, a course of that ID was not found globally")
			response2.write("folder:na")
                	return response2

	except Document.DoesNotExist, e:
                response2 =  HttpResponse(status=403)
                logger.info("Sorry, a course of that ID was not found globally")
                response2 = HttpResponse(status=403)
		response2.write("folder:na")
                return response2
	
	return redirect("/")

"""View to render the template to register a new user as
an individual
"""
def register_individual_view(request, ):
	c = {}
	c.update(csrf(request))
	return render(request, 'user/user_create_website_individual.html')

"""View to render the template to register a new user as 
an organisation
"""
def register_organisation_view(request,):
	try:
		if 'organisationalcode' in request.session:
			organisationalcode=request.session['organisationalcode']
			print(organisationalcode)
			request.session.flush();
        		organisation_requested = Organisation_Code.objects.get(\
			    code=organisationalcode).organisation
			organisation_name=organisation_requested.organisation_name;
        		state="Valid code"
			c = {}
        		c.update(csrf(request))
        		return render(request, \
			    'user/user_create_website_organisation.html', \
				{'organisationalcode':organisationalcode, \
				 'organisation_name':organisation_name, \
				 'state':state})
		else:
			state="Please enter your organisation code first"
			return redirect('register_selection')
    	except Organisation_Code.DoesNotExist, e:
        	state="Please enter your organisation code first"
		return redirect('register_selection')
	
"""View to render the template to create a new user when 
register button is clicked.
"""
def register_selection_view(request, ):
        c = {}
        c.update(csrf(request))
        return render(request, 'user/user_create_website_selection.html')

"""View to render the login page.
"""
def loginview(request):
	c = {}
	c.update(csrf(request))
	return render_to_response('login.html', c, context_instance=RequestContext(request))

"""This is the def that will authenticate the user over the umcloud website
"""
def auth_and_login(request, onsuccess='/', onfail='/login'):
    #Returns user object if parameters match the database.
    try:
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
    except:
	return redirect ('login')
    if user is not None:
	try:
		user_role = User_Roles.objects.get(user_userid=user).role_roleid;
		if user_role.id > 4:
			state="Sorry, students and teachers cannot login at the moment."
			return render_to_response('login.html', {'state':state},context_instance=RequestContext(request))
	except:	
		state="Error logging you in. You do not have any role assigned. Contact your organisation agmin."
                return render_to_response('login.html', {'state':state},context_instance=RequestContext(request))
			
	try:
		if user.is_superuser:
			login(request, user)
			logger.info("User=" + user.username+" has just logged in.")
			return redirect(onsuccess)

		userprofile = UserProfile.objects.get(user=user)
		if userprofile.admin_approved:
			login(request, user)
			logger.info("User=" + user.username+" has just logged in.")
			return redirect(onsuccess)
		else:
			state="You are not yet approved by your organisation. Contact your organisation's admin"
			statesuccess=1
                	return render_to_response('login.html', {'state':state,'statesuccess':statesuccess},context_instance=RequestContext(request))
	
	except UserProfile.DoesNotExist:
		logger.info("User profile does not exist")
		login(request, user)
		logger.info("User=" + user.username+" has just logged in.")
                return redirect(onsuccess)

    else:
	#Shows a "incorrect credentials" message
	state="Wrong username/password combination"
	return render_to_response('login.html', {'state':state},context_instance=RequestContext(request))
        return redirect(onfail)  

"""Common function used in register views to create user as per POST parameters
sent to this function.
"""
def create_user_website(username, email, password, first_name, last_name, website, job_title, company_name, date_of_birth, address, phone_number, gender, organisation_request):
    #Usage:
    #user = create_user_website(username=post['email'], email=post['email'], password=post['password'], 
    # first_name=post['first_name'], last_name=post['last_name'], website=post['website'], 
    # job_title=post['job_title'], company_name=post['company_name'])
    #date_of_birth=post['dateofbith'], address=post['address'], phone_number=post['phonenumber'], gender=post['gender'], organisation_request=post['organisationrequest']
    #try:
    if True:
        b=datetime.datetime.strptime(date_of_birth, '%m/%d/%Y').strftime('%Y-%m-%d')
	date_of_birth=b

    	user = User(username=username, email=email, first_name=first_name, last_name=last_name)
    	user.set_password(password)
    	user.save()
    	logger.info("User object created..")
    	logger.info("Creating profile..")
	individual_organisation = Organisation.objects.get(pk=1)
    
 	try:
		if organisation_request == "":
			logger.info("No organisation code specified. Defaulting to Individual Organisation")
			organisation_requested = individual_organisation
		else:
			organisation_requested = Organisation_Code.objects.get(code=organisation_request).organisation
		
    		user_profile = UserProfile(user=user, website=website, job_title=job_title, company_name=company_name, gender=gender, phone_number=phone_number, address=address, date_of_birth=date_of_birth, organisation_requested=organisation_requested)

    		student_role = Role.objects.get(pk=6)
    		new_role_mapping = User_Roles(name="website", user_userid=user, role_roleid=student_role)

		new_organisation_mapping = User_Organisations(user_userid=user, organisation_organisationid=organisation_requested)

		user_profile.save()
                logger.info("User profile created..")

		new_role_mapping.save()
		logger.info("Role Mapping created..")

		new_organisation_mapping.save()
		logger.info("Organisation mapping created..")

    		#Check if previous were a success.
    		logger.info("User Role mapping (website) success.")

		if organisation_requested == individual_organisation:
			logger.info("Here we approve the individual org fellos")
			#user_profile.admin_approved=True
			#user_profile.save()

		reason="success"
    		return user, reason
	except Organisation_Code.DoesNotExist:
		reason = "Something went wrong in checking organisation code"
		return None, reason
    #except:
    else:
	reason = "Username exists"
	return None, reason


def create_user_more(username, email, password, first_name, last_name, roleid, organisationid, date_of_birth, address, gender, phone_number, organisation_request):
    try:
    	user = User(username=username, email=email, first_name=first_name, last_name=last_name)
    	user.set_password(password)
    	user.save()
	try:
    	    role=Role.objects.get(pk=roleid)
    	    organisation = Organisation.objects.get(pk=organisationid)

	    try:
    	    	#Create role mapping. 
    	    	user_role = User_Roles(name="blah", user_userid=user, role_roleid=role)
    	    	user_role.save()
	    except:
		logger.info("Could not save role.")
		user.delete()
		return None

	    try:
    	    	#Create organisation mapping.
    	    	user_organisation = User_Organisations(user_userid=user, organisation_organisationid=organisation)
    	    	user_organisation.save()
	    except:
		logger.info("Could not set organisation")
		user_role.delete()
		user.delete()
		return None

    	    #Create same user in UM-TinCan LRS
    
    	    logger.info("User Role mapping success.")
	    try:
	    	b=datetime.datetime.strptime(date_of_birth, '%m/%d/%Y').strftime('%Y-%m-%d')
            	date_of_birth=b
	    	user_profile = UserProfile(user=user, gender=gender, phone_number=phone_number, address=address, date_of_birth=date_of_birth, organisation_requested=organisation_request)
	    	user_profile.admin_approved=True
	    	user_profile.save()
	    	logger.info("User Profile mapping success.")
	    except:
		logger.info("User Profile mapping could not be set")
		user_organisation.delete()
		user_role.delete()
		user.delete()
		return None
	except:
	    logger.info("Something went wronng")
	    user.delete()
	    return None

    	return user
    except:
	logger.info("Something went wrong.")
	return None

"""Common function used by views to check if a user exists
"""
def user_exists(username):
    user_count = User.objects.filter(username=username).count()
    if user_count == 0:
        return False
    return True

"""View to check organisation code inputted from the register options in
register view"""
def organisation_sign_up_in(request):
    logger.info("Checking organisation code")
    post=request.POST
    if request.method != 'POST':
	print("Not a post request. Are you testing?")
	state="Not a POST request or invalid code"
	return render_to_response('user/user_create_website_selection.html'\
	    ,{'state':state}, \
		context_instance=RequestContext(request))
    try:
	if 'organisationalcode' in request.POST:
	    organisation_request=post['organisationalcode']
	else:
	    state="The system could not process this (Request is broken)"
            return render_to_response('user/user_create_website_selection.html',\
		{'state':state},\
		    context_instance=RequestContext(request))
	organisation_request=post['organisationalcode']
	logger.info("Code given:")
	logger.info(organisation_request)
	organisation_requested = Organisation_Code.objects.get(\
	    code=organisation_request).organisation
	state="Valid code"
	request.session['organisationalcode']=organisation_request
	return redirect('register_organisation')
    except Organisation_Code.DoesNotExist, e:
	state="Invalid code"
	return render_to_response('user/user_create_website_selection.html',\
	    {'state':state},\
		context_instance=RequestContext(request))
    state="Nothing has happened"
    return render_to_response('user/user_create_website_selection.html',\
	{'state':state}, context_instance=RequestContext(request))

"""submit link that handles user creation from website. 
"""
def sign_up_in(request):
    logger.info("Creating new user from website..")
    organisation_list=Organisation.objects.all()
    if request.method !='POST':
	return redirect('login')
	return redirect('register_selection')
	
    post = request.POST
    if not user_exists(post['username']): 
	password=post['password']
	passwordagain=post['passwordagain']
	if password != passwordagain:
		password=None
		state="The two passwords you gave do not match. Please try again."
                #return render(request, template_name, data)
		return render_to_response('user/user_create_website_selection.html',{'state':state,'organisation_list':organisation_list}, context_instance=RequestContext(request))


		
        user, reason = create_user_website(username=post['username'], email=post['email'], password=post['password'], first_name=post['first_name'], last_name=post['last_name'], website=post['website'], job_title=post['job_title'], company_name=post['company_name'], date_of_birth=post['dateofbirth'], address=post['address'], phone_number=post['phonenumber'], gender=post['gender'], organisation_request=post['organisationrequest'])

	if user:
	    try:
		if post['courseid']:
		    userprofile=UserProfile.objects.get(user=user)
		    userprofile.admin_approved=True
		    userprofile.save()

		    """
		    blockid=post['blockid']
		    block=Document.objects.get(elpid=blockid)
		    block.students.add(user)
		    block.save()
		    """

		    courseid=post['courseid']
		    course=Course.objects.get(id=courseid)
	    	    course.students.add(user)
		    course.save()

	 	    invitationid = post['invitationid']
		    invitation = Invitation.objects.get(id=invitationid)
		    invitation.done = True
		    invitation.save()
		    return redirect('login')
	    except:
		#INSTEAD redirect to success page.
		return render_to_response('confirmation.html',{'state':'Congratulations, your request has been sent to the organisation manager.You will be emailed when you get approved.'}, context_instance=RequestContext(request))
        	#return auth_and_login(request)
	else:
		return render_to_response('user/user_create_website_selection.html',{'state':reason,'organisation_list':organisation_list}, context_instance=RequestContext(request))
    else:
        #Shows message that the username/email address already exists in our database.
        state="The Username already exists.."
        return render_to_response('user/user_create_website_selection.html',{'state':state,'organisation_list':organisation_list}, context_instance=RequestContext(request))

"""In-App authentication for phone numbers. 
View to create non-user-validated users for users with phone numbers from within the App only.
"""
@csrf_exempt
def phone_inapp_registration(request):
    logger.info("Starting this..")
    country_courses = None
    if request.method !='POST':
        logger.info("Not a POST request")
        #Bad request: 400.
        authresponse = HttpResponse(status=400)
        authresponse.write("Not POST")
        return authresponse
    try:
        version = request.META['UM-In-App-Registration-Version']
    except:
        try:
            version = request.META['HTTP_UM_IN_APP_REGISTRATION_VERSION']
        except:
            version = request.META.get('UM-In-App-Registration-Version',\
                                         None)
            if not version:
                import urllib
                bdy = urllib.unquote_plus(request.body)
                v = re.search(\
                    'UM\WIn\WApp\WRegistration\WVersion=(?P<num>[\d\.]*)\&?', bdy)
                if v:
                    version = v.group('num')
    if version:
        regex = re.compile("^1\.0(\.\d+)?$")
        if regex.match(version):
            pass
        else:
            return HttpResponseBadRequest(\
                "UM-In-App-Registration-Version is not supported")
    else:
        return HttpResponseBadRequest(\
            "UM-In-App-Registration-Version header missing")

    post = request.POST
    phonenumber = post.get('phonenumber', None)
    if not phonenumber:
        logger.info("No Phone number in request")
        return HttpResponseBadRequest("No phone number in request")

    name = post.get('name', None)
    email = post.get('email', None)
    username = post.get('username', None)
    usernamegiven = False
    if username is not None:
        usernamegiven = True
    password = post.get('password', None)
    code = post.get('regcode', None)
    #Check quality of phone number

    # Create random username and password (6 digits)
    if password is None:
        password = random.randrange(100000,999999)
    if username is None:
        username = ''.join(random.choice(string.ascii_lowercase) for x in range(5))\
                                             + str(random.randrange(1000,9999))
    usernames = User.objects.all().values_list('username', flat=True)
    while (username in usernames):
	if usernamegiven == False :
            username = ''.join(random.choice(string.ascii_letters) for x in range(5))\
                                             + str(random.randrange(1000,9999))
	else:
	    #Return "this username has already been created error"
	    print("Error: Username already exists..");
	    errormessage = "Username already taken. Please choose another one!"
	    json_credentials = simplejson.dumps( {'errormessage': errormessage})
            return HttpResponse(json_credentials, mimetype="application/json", status=400)

    print("Created username:" + username)
    if not name:
 	name = username
    
    #Organisation mapping.
    if phonenumber.startswith("+"):
        clean_number = phonenumber[1:]
    elif phonenumber.startswith("00"):
        clean_number = phonenumber[2:]
    elif phonenumber.startswith("0"):
        clean_number = phonenumber[1:]

    if not email:
        email = str(clean_number) + "@ustadmobile.email"
    first_name = str(name)
    last_name = "InAppRegistration"
    
    user = User(username=username, email=email, first_name=first_name,\
                 last_name=last_name)
    user.set_password(password)
    user.save()
    logger.info("User object created..")
    logger.info("Creating profile..")

    phonenumber = phonenumber.strip()
    if not phonenumber.startswith("+"):
	if not phonenumber.startswith("00"):
	    phonenumber = "+" + str(phonenumber)
	else:
	    phonenumber = phonenumber[2:]
            phonenumber = "+" + str(phonenumber)

    ph_number = phonenumbers.parse(phonenumber, None)
    country_code = ph_number.country_code
    logger.info("Country code is :"  + str(country_code))
    organisation = None
    if code is not None:
	try:
            organisation = Organisation_Code.objects.get(\
                code=code).organisation
        except Organisation_Code.DoesNotExist, e:
            print("Please enter your organisation code first")

    if not code and not organisation:
        country_courses=None
    	try:
            country_mapping = Country_Organisation.objects.get(\
                country_code=int(country_code))
            organisation = country_mapping.organisation
            logger.info("orgaisation found by country code: " + organisation.organisation_name)
            if organisation:
                #Assign to courses.
                country_courses = country_mapping.allcourses.all()
        except:
            logger.info("Not assigned to a country")
            organisation = Organisation.objects.get(pk=1)

    gender = post.get('gender', None)
    if not gender:
	gender = ""
    gender = str(gender)
    try:
        user_profile = UserProfile(user=user, website="www.ustadmobile.com", \
            job_title="In-App Phone Registration", \
            gender=gender, phone_number=phonenumber,\
            organisation_requested=organisation)
	user_profile.save()
    except Exception, e:
	errormessage = str(e)
        logger.info("Something went wrong in making user profile")
        json_credentials = simplejson.dumps( {'errormessage': errormessage})
        return HttpResponse(json_credentials, mimetype="application/json", status=500)
	
        #authresponse = HttpResponse(status=500)
        #authresponse.write("Internal Error in making user profile")
        #return authresponse
    try:
        student_role = Role.objects.get(pk=6)
        new_role_mapping = User_Roles(name="ph_inapp_reg", \
                            user_userid=user, role_roleid=student_role)

        new_organisation_mapping = User_Organisations(user_userid=user, \
                    organisation_organisationid=organisation)

        user_profile.save()
        logger.info("User profile created..")

        new_role_mapping.save()
        logger.info("Role Mapping created..")


        new_organisation_mapping.save()
        logger.info("Organisation mapping created..")

        #Check if previous were a success.
        logger.info("User Role mapping (website) success.")

        user_profile.admin_approved=True
        user_profile.save()

    except Exception, e:
	errormessage = str(e)
        logger.info("Something went wrong in making user profile")
        json_credentials = simplejson.dumps( {'errormessage': errormessage})
        return HttpResponse(json_credentials, mimetype="application/json", status=500)
	#authresponse = HttpResponse(status=500)
        #authresponse.write("Internal Error in Role mapping, organisation mapping.")
        #return authresponse

    try:
        #Assign student to courses
        if country_courses:
	    print("Am I doing this?")
            for every_course in country_courses:
                every_course.students.add(user)
                every_course.save()
		#Do something with user. 


        json_credentials = simplejson.dumps( {'username': username,
                           'password': password,
                            })
        return HttpResponse(json_credentials, mimetype="application/json")
    except Exception, e:
	print("Internal Error")
	print(str(e))
	errormessage = str(e)
        logger.info("Something went wrong in making user profile")
        json_credentials = simplejson.dumps( {'errormessage': errormessage})
        return HttpResponse(json_credentials, mimetype="application/json", status=500)
	#authresponse = HttpResponse(status=500)
        #authresponse.write("Internal Error in assigning courses and Student roles.")
        #return authresponse

    authresponse = HttpResponse(status=200)
    authresponse.write("Test")
    return authresponse


from opds.views import login_basic_auth
@csrf_exempt
def teacher_enroll_student(request):
    if request.method !='POST':
        logger.info("Not a POST request")
        #Bad request: 400.
        authresponse = HttpResponse(status=400)
        authresponse.write("Not POST")
        return authresponse
    
    try:
        version = request.META['UM-In-App-Registration-Version']
    except:
        try:
            version = request.META['HTTP_UM_IN_APP_REGISTRATION_VERSION']
        except:
            version = request.META.get('UM-In-App-Registration-Version',\
                                         None)
            if not version:
                import urllib
                bdy = urllib.unquote_plus(request.body)
                v = re.search(\
                    'UM\WIn\WApp\WRegistration\WVersion=(?P<num>[\d\.]*)\&?', bdy)
                if v:
                    version = v.group('num')
    if version:
        regex = re.compile("^1\.0(\.\d+)?$")
        if regex.match(version):
            pass
        else:
            return HttpResponseBadRequest(\
                "UM-In-App-Registration-Version is not supported")
    else:
        return HttpResponseBadRequest(\
            "UM-In-App-Registration-Version header missing")

    post = request.POST

    class_id = post.get('class_id', None)
    if class_id is None and class_id == '':
        logger.info("Class id is none")
        authresponse = HttpResponse(status=401)
        authresponse.write("No class id specified")
        return authresponse

    user = None
    
    #Check basic authentication (for teacher user)
    state, authresponse = login_basic_auth(request)
    if state == False:
        return authresponse
    if state == True:
        user = authresponse

    #Check user is ok
    if user is None:
        authresponse = HttpResponse(status=401)
        authresponse.write("User is invalid")
        return authresponse
    
    #Check if user is a teacher
    try:
        teacher_role = Role.objects.get(role_name='Teacher')
        user_role = User_Roles.objects.get(user_userid=user).role_roleid
        if teacher_role != user_role:
            logger.info("Not a teacher")
            authresponse = HttpResponse(status=401)
            authresponse.write("User is not a teacher")
            return authresponse
    except:
	authresponse = HttpResponse(status=401)
	authresponse.write("Couldnt get role of user.")
	return authresponse

    #Check if class with class id is valid
    try:
        this_class = Allclass.objects.get(pk=class_id)
    except:
        logger.info("Not a valid class id")
        authresponse = HttpResponse(status=401)
        authresponse.write("Not a valid class id: " + str(class_id))
        return authresponse


    #Check if user is a teacher of the class
    this_class_teachers = this_class.teachers.all()
    if user not in this_class_teachers:
        logger.info("Teacher not a teacher of this class.")
        authresponse = HttpResponse(status=401)
        authresponse.write("Teacher not a teacher of this class.")
        return authresponse

    #All good. Now we can take in information to creat the Student user. 
            

    phonenumber = post.get('phonenumber', None)
    
    #if not phonenumber:
    #    logger.info("No Phone number in request")
    #    return HttpResponseBadRequest("No phone number in request")

    name = post.get('name', None)
    if name is None or name == "":
	print("no name provided")
	errormessage = "Please fill in a name"
	json_credentials = simplejson.dumps( {'errormessage':errormessage} )
	return HttpResponse(json_credentials, mimetype="application/json", status=400)

    email = post.get('email', None)
    username = post.get('username', None)
    usernamegiven = False
    if username is not None and username != "":
        usernamegiven = True
    password = post.get('password', None)
    code = post.get('regcode', None)
    #Check quality of phone number

    # Create random username and password (6 digits)
    if password is None or password == "":
        password = random.randrange(100000,999999)
    if username is None or username =="":
        username = ''.join(random.choice(string.ascii_lowercase) for x in range(5))\
                                             + str(random.randrange(1000,9999))
    usernames = User.objects.all().values_list('username', flat=True)
    while (username in usernames):
        if usernamegiven == False :
            username = ''.join(random.choice(string.ascii_letters) for x in range(5))\
                                             + str(random.randrange(1000,9999))
        else:
            #Return "this username has already been created error"
            print("Error: Username already exists..");
            errormessage = "Username already taken. Please choose another one!"
            json_credentials = simplejson.dumps( {'errormessage': errormessage})
            return HttpResponse(json_credentials, mimetype="application/json", status=400)

    print("Created username:" + username)
    if not name:
        name = username

    #Organisation mapping.
    if phonenumber:
        if phonenumber.startswith("+"):
            clean_number = phonenumber[1:]
        elif phonenumber.startswith("00"):
            clean_number = phonenumber[2:]
        elif phonenumber.startswith("0"):
            clean_number = phonenumber[1:]

    if not email:
        email = str(username) + "@ustadmobile.email"
    first_name = str(name)
    last_name = "TeacherEnrollStudent"

    new_user = User(username=username, email=email, first_name=first_name,\
                 last_name=last_name)
    new_user.set_password(password)
    new_user.save()
    logger.info("User object created..")

    

    logger.info("Creating User profile..")

    if phonenumber:
        phonenumber = phonenumber.strip()
        if not phonenumber.startswith("+"):
            if not phonenumber.startswith("00"):
                phonenumber = "+" + str(phonenumber)
            else:
                phonenumber = phonenumber[2:]
                phonenumber = "+" + str(phonenumber)

    #Organisation will be the same as the teachers organisation in this case..
    organisation = User_Organisations.objects.get(user_userid=user).organisation_organisationid;
    
    gender = post.get('gender', None)
    if not gender:
        gender = ""
    gender = str(gender)
    try:
	if phonenumber:
            user_profile = UserProfile(user=new_user, website="www.ustadmobile.com", \
                job_title="In-App Phone Registration", \
                gender=gender, phone_number=phonenumber,\
                organisation_requested=organisation)
	elif not phonenumber and gender:
	    user_profile = UserProfile(user=new_user, website="www.ustadmobile.com", \
                job_title="In-App Phone Registration", \
                gender=gender,\
                organisation_requested=organisation)
	elif not phonenumber and not gender:
	    user_profile = UserProfile(user=new_user, website="www.ustadmobile.com", \
                job_title="In-App Phone Registration", \
                organisation_requested=organisation)


        user_profile.save()
    except Exception, e:
        errormessage = str(e)
	logger.info("Something went wrong in making user profile")
        json_credentials = simplejson.dumps( {'errormessage': errormessage})
        return HttpResponse(json_credentials, mimetype="application/json", status=500)

        #authresponse = HttpResponse(status=500)
        #authresponse.write("Internal Error in making user profile")
        #return authresponse
    try:
        student_role = Role.objects.get(pk=6)
        new_role_mapping = User_Roles(name="teacher_enroll_student", \
                            user_userid=new_user, role_roleid=student_role)

        new_organisation_mapping = User_Organisations(user_userid=new_user, \
                    organisation_organisationid=organisation)

        user_profile.save()
        logger.info("User profile created..")

        new_role_mapping.save()
        logger.info("Role Mapping created..")


        new_organisation_mapping.save()
        logger.info("Organisation mapping created..")

        #Check if previous were a success.
        logger.info("User Role mapping (website) success.")

        user_profile.admin_approved=True
        user_profile.save()
	
	#Add student to class
	this_class.students.add(new_user)
	this_class.save()
	

    except Exception, e:
        errormessage = str(e)
        logger.info("Something went wrong in making user profile")
        json_credentials = simplejson.dumps( {'errormessage': errormessage})
        return HttpResponse(json_credentials, mimetype="application/json", status=500)
        #authresponse = HttpResponse(status=500)
        #authresponse.write("Internal Error in Role mapping, organisation mapping.")
        #return authresponse

    try:
        json_credentials = simplejson.dumps( {'username': username,
                           'password': password,
                            })
        return HttpResponse(json_credentials, mimetype="application/json")
    except Exception, e:
        print("Internal Error")
        print(str(e))
        errormessage = str(e)
        logger.info("Something went wrong in making user profile")
        json_credentials = simplejson.dumps( {'errormessage': errormessage})
        return HttpResponse(json_credentials, mimetype="application/json", status=500)


"""View to log out existing user and redirect back to login page
"""
def logout_view(request):
    logger.info("User="+request.user.username+" has logged out.")
    logout(request)
    return redirect('login')

"""View was used to render this view after a success login
"""
@login_required(login_url='/login/')
def secured(request):
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid
    current_user = request.user.username + " (" + organisation.organisation_name + ")"
    current_user_role = User_Roles.objects.get(user_userid=request.user.id).role_roleid.role_name;
    current_user = "Hi, " + request.user.first_name + ". You are a " + current_user_role + " in " + organisation.organisation_name + " organisation."
    logger.info("Logged in user: " + request.user.username + " an " + current_user_role + " in " + organisation.organisation_name + " organisation.")
    return render_to_response("secure.html", 
	{'current_user': current_user},
	context_instance=RequestContext(request)
    )


"""View to render template for uploading new block 
"""
@login_required(login_url='/login/')
def upload_view(request):
    current_user = request.user.username
    return render_to_response("upload.html", {'current_user': current_user},
        context_instance=RequestContext(request))

"""View to render the management  page on home screen
"""
@login_required(login_url='/login/')
def management_view(request):
    current_user = request.user.username
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid
    current_user_role = User_Roles.objects.get(user_userid=request.user.id).role_roleid.role_name;
    current_user = "Hi, " + request.user.first_name + ". You are a " + current_user_role + " in " + organisation.organisation_name + " organisation."

    current_user = "Hi, " + request.user.first_name + ". You are a " + current_user_role + " in " + organisation.organisation_name + " organisation."
    #superadmin_role
    if request.user.is_staff == True:
	superadmin_role=True
    else:
	superadmin_role=False
    current_role = User_Roles.objects.get(user_userid=request.user.id).role_roleid
    if current_role.id == 2:
	orgadmin_role=True
    else:
	orgadmin_role=False

    return render_to_response("manage.html", {'current_user': current_user, 'superadmin_role':superadmin_role, 'orgadmin_role':orgadmin_role},
        context_instance=RequestContext(request))

"""View to render reporting page at home screen.
"""
@login_required(login_url='/login/')
def reports_view(request):
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid
    current_user_role = User_Roles.objects.get(user_userid=request.user.id).role_roleid.role_name;
    current_user = "Hi, " + request.user.first_name + ". You are a " + current_user_role + " in " + organisation.organisation_name + " organisation."
    logger.info("User=" +request.user.username + " accessed /reports/")
    return render_to_response("reports.html", {'current_user': current_user},
        context_instance=RequestContext(request))

@csrf_exempt
def test_request(request):
    print("Testing request:")
    print(request)
    print(request.POST)
    print(request.GET)
    authresponse = HttpResponse(status=200)
    authresponse.write("Hello")
    return authresponse
    
