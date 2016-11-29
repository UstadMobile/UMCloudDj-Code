
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, redirect, get_object_or_404 
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib import auth
from django.template import RequestContext

from django.forms import ModelForm
from school.models import School
from organisation.models import Organisation
from organisation.models import UMCloud_Package
from organisation.models import User_Organisations
from UMCloudDj.views import create_user_more, user_exists
from uploadeXe.models import Role
from uploadeXe.models import User_Roles
from uploadeXe.models import Country_Organisation
from organisation.models import Organisation_Code

from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
import datetime
from datetime import timedelta
import time
import os
import urllib
import urllib2, base64, json
from random import randrange
from holiday.models import Calendar
from holiday.views import make_calendar_object
from sheetmaker.models import status_label
from sheetmaker.models import organisation_status_label

from django_cron import CronJobBase, Schedule
from django.core.mail import send_mail

from allclass.models import Allclass, Allclass_alert_settings, Alert, Alert_type
from school.models import School_alert_settings
from organisation.models import Org_alert_settings
from report_statement.views import is_date_a_holiday, get_attendance_daily
from users.models import UserProfile

"""
The organisation model form that is used for update and creation
"""
class Country_OrganisationForm(ModelForm):
    class Meta:
        model = Country_Organisation


@login_required(login_url='/login/')
def country_organisation_table(request, template_name='organisation/country_organisation_table.html'):
    if (request.user.is_staff == True):
        print("ok")
	corganisations = Country_Organisation.objects.all()
        organisation_packages = []
	data = {}
        data['object_list']=corganisations
        data['organisations']=corganisations
        return render(request, template_name, data)

    else:
        state="You do not have permission to see this page."
        return render(request, template_name, {'state':state})

@login_required(login_url='/login/')
def country_organisation_new(request, template_name='organisation/country_organisation_new.html'):
    if (request.user.is_staff == True):
	print("ok")
	form = Country_OrganisationForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect('countryorgtable')
        return render(request, template_name, {'form':form})

    else:
	state="You do not have permission to see this page."
        return render(request, template_name, {'state':state})

@login_required(login_url='/login/')
def country_organisation_create(request, template_name='organisation/country_organisation_create.html'):
    if (request.user.is_staff == True):
        print("ok")
	organisations=Organisation.objects.all()
	data={}
	data['organisations']=organisations
	if request.method == 'POST':
	    post=request.POST
	    try:
	        country_code=post['country_code']
	        organisationid = post['organisationid']
	    except: 
		state="Invalid Code/Org"
		data['state']=state
		return render(request, template_name, data)
	    if country_code != "" and country_code != None and\
		 organisationid != None and organisationid != "":
		organisation=Organisation.objects.get(pk=organisationid)
		try:
		    countryorg = Country_Organisation(country_code=country_code,\
			organisation=organisation)
		    countryorg.save()
		except:
		    state="Could not create the relationship"
		    data['state']=state
		    return render(request, template_name, data)
		return redirect('countryorgtable')
	return render(request, template_name, data)

    else:
        state="You do not have permission to see this page."
        return render(request, template_name, {'state':state})

@login_required(login_url='/login/')
def country_organisation_edit(request, pk, template_name='organisation/country_organisation_edit.html'):

    if (request.user.is_staff == True):
        print("ok")
	corganisation = get_object_or_404(Country_Organisation, pk=pk)
        form = Country_OrganisationForm(request.POST or None, instance=corganisation)
        if form.is_valid():
                form.save()
                return redirect('countryorgtable')
        return render(request, template_name, {'form':form})

    else:
        state="You do not have permission to see this page."
        return render(request, template_name, {'state':state})

"""
@login_required(login_url='/login/')
def country_organisation_update(request, pk, template_name='organisation/country_organisation_update.html'):
    if (request.user.is_staff == True):
	print("ok2")
	corganisation = get_object_or_404(Country_Organisation, pk=pk)
	
"""

"""
Super Admin option to delete country organisation relationship
"""
@login_required(login_url='/login/')
def country_organisation_delete(request, pk, template_name='organisation/organisation_confirm_delete.html'):
    if (request.user.is_staff==True):
        corganisation = get_object_or_404(Country_Organisation, pk=pk)
        if request.method=='POST':
                corganisation.delete()
                return redirect('countryorgtable')
        return render(request, template_name, {'object':corganisation})
    else:
        print("Not a staff.")
        state="You do not have permission to see this page."
        return render(request, template_name, {'state':state})



###################################
# Organisation CRUD

"""
The organisation model form that is used for update and creation
"""
class OrganisationForm(ModelForm):
    class Meta:
        model = Organisation
	fields = ('organisation_desc', 'public')

"""
The organisation code model form that is used to set org code and update
it
"""
class OrganisationCodeForm(ModelForm):
    class Meta:
	model = Organisation_Code
	fields=('code',)

"""
This view renders the organisations or logged in user and displays
to a template html that renders it to a prime ui html table.
Only super admins have access to this page.
"""
@login_required(login_url='/login/')
def organisation_table(request, template_name='organisation/organisation_table.html'):
    if (request.user.is_staff==True):
	organisations = Organisation.objects.all()
    	organisation_packages = []

    	data = {}
	organisation_code=[]		
	organisation_manager=[]
	for org in organisations:
		try:
			org_code=Organisation_Code.objects.get(organisation=org)
			organisation_code.append(org_code.code)
		except Organisation_Code.DoesNotExist, e: 
			#If organisation code doesn;t exist.
			# When org admin loggs in the code 
			# will be set. This is for super admin
			# views.
			nullcode="-"
			organisation_code.append(nullcode)	
		try:
			organisation_admin_role=Role.objects.get(pk=2)
			if organisation_admin_role.role_name != "Organisational Manager": 
			    organisation_admin_role = Role.objects.get(\
					role_name = "Organisational Manager")
			#Get the first org manager set
			org_manager=User.objects.filter(\
			    pk__in=User_Organisations.objects.filter(\
				organisation_organisationid=org\
				    ).values_list('user_userid', flat=True)\
			    ).filter(\
				pk__in=User_Roles.objects.filter(\
				    role_roleid=organisation_admin_role\
					).values_list('user_userid',flat=True))[0]
			#print("Found org manager for org: " + org.organisation_name)
			organisation_manager.append(org_manager.username)
		
		except:
			print("Didnt find org manager for org: " + org.organisation_name )
			organisation_manager.append("-")
		
			
    	#data['object_list'] = zip(organisations,organisation_packages)
    	data['umpackage_list'] = organisation_packages
	object_list = zip(organisations, organisation_code, organisation_manager)
	data['object_list']=object_list
	data['organisations']=organisations
    	return render(request, template_name, data)

    else:
        state="You do not have permission to see this page."
        return render(request, template_name, {'state':state})

"""
View to render view that Organisation Manager sees for its own
organisation
"""
@login_required(login_url='/login/')
def my_organisation(request, template_name='organisation/my_organisation.html'):
    current_role = User_Roles.objects.get(\
		user_userid=request.user.id).role_roleid
    organisation = User_Organisations.objects.get(\
			user_userid=request.user\
			).organisation_organisationid
    if current_role.id == 2:
 	if current_role.role_name == "Organisational Manager":
	    #print("You are an organisational Manager")
	    try:
		organisation_code=Organisation_Code.objects.get(
				    organisation=organisation)
	    except Organisation_Code.DoesNotExist, e:
		organisation_code = Organisation_Code(\
				    organisation=organisation)
		random_code = randrange(1000000)
		random_org_code=str(organisation.id)+\
					str(random_code)
		organisation_code.code=random_org_code
		organisation_code.save()
	    return render(request, template_name,{\
			'organisation':organisation,\
			'organisation_code':organisation_code})
    else:
	state="You do not have permission to see this page."
        return render(request, template_name, {'state':state})

"""
View to update the organisation's details.
"""
@login_required(login_url='/login/')
def my_organisation_update(request, pk, template_name='organisation/my_organisation_form.html'):
    current_role = User_Roles.objects.get(\
			user_userid=request.user.id\
			).role_roleid
    organisation = User_Organisations.objects.get(\
			user_userid=request.user\
			).organisation_organisationid
    organisation_code = Organisation_Code.objects.get(\
			organisation=organisation)
    data={}
    data['organisation']=organisation
    if current_role.id == 2 and \
	current_role.role_name=="Organisational Manager"\
 	    and pk == str(organisation_code.id):
        #("You are an organisational manager and editing \
	#your own organisation")
	organisation_code = get_object_or_404(Organisation_Code, \
						pk=pk)
        form = OrganisationCodeForm(request.POST or None, \
				instance=organisation_code)
	public = organisation.public;

        if form.is_valid():
                form.save()
		return redirect('my_organisation')
        return render(request, template_name, {'form':form, \
	        'public':public, 'organisation':organisation})
    else:
        print("Not a staff.")
        data['state']="You do not have permission to see this page."
        return render(request, template_name, data)

class status_label_status(object):
    status = ""
    label = ""

    # The class "constructor" - It's actually an initializer
    def __init__(self, status, label):
	self.status = status;
	self.label = label;

"""View to update the organisation details and change / set the 
holiday calendar
"""
def my_organisation_edit(request, pk, template_name='organisation/my_organisation_edit.html'):
	current_role = User_Roles.objects.get(\
                        user_userid=request.user.id\
                        ).role_roleid
    	organisation = User_Organisations.objects.get(\
                        user_userid=request.user\
                        ).organisation_organisationid
    	organisation_code = Organisation_Code.objects.get(\
                        organisation=organisation)
    	data={}
    	data['organisation']=organisation
	data['organisation_code']=organisation_code
	calendars = Calendar.objects.filter(organisation=organisation)
	selected_calendar = None
	selected_calendar = organisation.calendar
	if not selected_calendar:
		selected_calendar = None
	all_labels = status_label.objects.all()
	selected_org_status_labels = organisation_status_label.objects.filter(organisation=organisation)
	selected_status_labels = []
	status_labels = []
	for every_org_status_label in selected_org_status_labels:
	    selected_status_labels.append(every_org_status_label.status_label)
	for elabel in all_labels:
	    if elabel in selected_status_labels:
	    	status_labels.append(status_label_status(True, elabel))	
	    else:
		status_labels.append(status_label_status(False, elabel))
	data['calendars'] = calendars
	data['selected_calendar'] = selected_calendar
	data['status_labels'] = status_labels
	data['selected_status_labels'] = selected_status_labels
	#data['organisation_code'] = organisation_code
	if current_role.id == 2 and \
            current_role.role_name=="Organisational Manager"\
           	and pk == str(organisation.id):
        	#("You are an organisational manager and editing \
        	#your own organisation")
		
        	form = OrganisationForm(request.POST or None, \
                                instance=organisation)
		data['form'] = form
        	#public = organisation.public;

        	if form.is_valid():
                	form.save()
			post = request.POST
			code = post['id_code']
			organisation_code.code = code
			organisation_code.save()

			print("Checking if Holiday Calendar is given:")
			try:
			    selected_calendar = post['holiday_calendar']
			except:
			    selected_calendar = None
			
			if selected_calendar:
			    new_holiday_calendar_name = post['holiday_name']
			    print("new: " + new_holiday_calendar_name)
			    hidden_holidays = post['hidden_holidays']
			    if selected_calendar != None or selected_calendar != "":
				if str(selected_calendar) != str(0):
					holiday_calendar = Calendar.objects.get(pk=int(selected_calendar))
					if holiday_calendar:
						organisation.calendar = holiday_calendar
						organisation.save()
						print("Changed OK")
					else:
						print("No cal found.");
				else:
					print("Making new calendar..")
					if new_holiday_calendar_name != "" or new_holiday_calendar_name  != None:
						holiday_calendar, state, statesuccess = make_calendar_object(new_holiday_calendar_name, hidden_holidays, organisation)
						if holiday_calendar:
							organisation.calendar = holiday_calendar
							organisation.save()
							print("Made OK")

			#Adding the status_label to organisation
			print("all status labels:")
			selected_status_labels = post.getlist('labels')
			all_labels = status_label.objects.all()
			selected_labels = []
			for every_label in selected_status_labels:
			    this_label = status_label.objects.get(pk=int(every_label))
			    selected_labels.append(this_label)
			    try:
				every_label_org = organisation_status_label.objects.get(status_label = this_label)
				print("every_label_org:")
				print(every_label_org)
			    except:
				every_label_org = organisation_status_label(organisation = organisation, \
							status_label = this_label)
				every_label_org.save()
				print("every_label_org saved")
				print(every_label_org)
			print("all labels:")
			print(all_labels)
			print("selected labels:")
			print(selected_labels)
			for each_label in all_labels:
			    if each_label not in selected_labels:
				#Delete this
				try:
				    print("Deleteing label org assignment..")
				    delete_this_org_label = organisation_status_label.objects.get(status_label = each_label)
				    delete_this_org_label.delete()
				    print("..deleted.")
				except:
				    pass
			
                	return redirect('my_organisation')
        	return render(request, template_name, data)
    	else:
        	print("Not a staff.")
        	data['state']="You do not have permission to see this page."
        	return render(request, template_name, data)
    
"""
Check if organisation exist. Common function
"""
def organisation_exists(name):
    organisation_count = Organisation.objects.filter(\
			organisation_name=name).count()
    if organisation_count == 0:
        return False
    return True

"""
View to create organisation. Common function.
"""
def create_organisation(organisation_name, organisation_desc, umpackageid):
    umpackage = UMCloud_Package.objects.get(pk=umpackageid)
    organisation = Organisation(organisation_name=organisation_name, \
				organisation_desc=organisation_desc, \
				set_package=umpackage)
    organisation.save()

    #("Organisation Package mapping success.")
    return organisation

"""
This view will render a new organisation create form and take in the form
to create a new organisation as per POST parameters. using Organisation form.
This view will only be accesible for super admins.
"""
@login_required(login_url='/login/')
def organisation_create(request, template_name='organisation/organisation_create.html'):
    if (request.user.is_staff==True):
	form = OrganisationForm(request.POST or None)
	organisations=Organisation.objects.all()
    	umpackages = UMCloud_Package.objects.all()
    	data = {}
    	data['object_list'] = umpackages
	data['organisation_list'] = organisations

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
			if not organisation_exists(post['organisation_name']):
				try:
					umpackageid=post['umpackageid']
				except:
					umpackageid=2
                        	organisation = create_organisation(\
				    organisation_name=post['organisation_name'], \
				    organisation_desc=post['organisation_desc'], \
				    umpackageid=post['umpackageid'])
                        	#return redirect('organisation_table')

				org_admin_role_id=Role.objects.get(\
						role_name="Organisational Manager").id
                		user = create_user_more(\
					username=post['username'], email=post['email'], \
					password=post['password'], \
					first_name=post['first_name'], \
					last_name=post['last_name'], \
					roleid=org_admin_role_id, \
					organisationid=organisation.id, \
					date_of_birth=post['dateofbirth'], \
					address=post['address'], gender=post['gender'], \
					phone_number=post['phonenumber'], \
					organisation_request=organisation)
                		if user:
					#("User created..")
                    			current_user_role = User_Roles.objects.get(\
							user_userid=user.id).role_roleid;

                    			student_role = Role.objects.get(pk=6)
					teacher_role = Role.objects.get(pk=5)

                    			state="The user " + user.username +\
						 " and organisation " + \
						organisation.organisation_name + \
							" has been created."
					print("Creating the default teacher and school")
					
					org_school = School(school_name=organisation.organisation_name + \
						"_school", \
						school_desc="This is the default school for Organisation: "+ \
						organisation.organisation_name,organisation_id=organisation.id)
        				org_school.save()
					
					org_teacher = User.objects.create(username=organisation.organisation_name+\
							"_teacher", password=post['password'], \
							first_name="Default", last_name="Teacher")
					org_teacher.save()
					org_teacher_role = User_Roles(name="org_create", \
						user_userid=org_teacher, role_roleid=teacher_role)
					org_teacher_role.save()
					org_teacher_organisation = User_Organisations(\
					    user_userid=org_teacher, \
						organisation_organisationid=organisation)
					org_teacher_organisation.save()
					#("Mapping done.")
					
					print("Checking if Holiday Calendar is given:")
                        		selected_calendar = post['holiday_calendar']
                        		new_holiday_calendar_name = post['holiday_name']
                        		print("new: " + new_holiday_calendar_name)
                        		hidden_holidays = post['hidden_holidays']
                        		if selected_calendar != None or selected_calendar != "":
                                		if str(selected_calendar) != str(0):
                                        		holiday_calendar = Calendar.objects.get(pk=int(selected_calendar))
                                        		if holiday_calendar:
                                                		organisation.calendar = holiday_calendar
                                                		organisation.save()
                                                		print("Changed OK")
                                        		else:
                                                		print("No cal found.");
                                		else:
                                        		print("Making new calendar..")
                                        		if new_holiday_calendar_name != "" or new_holiday_calendar_name  != None:
                                                		holiday_calendar, state, statesuccess = make_calendar_object(new_holiday_calendar_name, hidden_holidays, organisation)
                                                		if holiday_calendar:
                                                        		organisation.calendar = holiday_calendar
                                                        		organisation.save()
                                                        		print("Made OK")

					return redirect('organisation_table')
                		else:
					print("Something went wrong when creating the user.. ")
					organisation.delete()
                    			state="The Username Creation failed. Contact us."
                    			data['state']=state
                    			return render(request, template_name, data)
			else:
				print("Organisation already exists..")
                                #Show message that the username/email address already exists in our database.
				state="The Organisation already exists.."
                                data['state']=state
                                return render(request, template_name, data)
		else:
			print("Username already exists..")
                        #Show message that the username/email address already exists in our database.
                        state="The Username already exists.."
                        data['state']=state
                        return render(request, template_name, data)

	return render(request, template_name, data)
    else:
        state="You do not have permission to see this page."
        return render(request, template_name, {'state':state})

"""
View to update an organisation
"""
@login_required(login_url='/login/')
def organisation_update(request, pk, template_name='organisation/organisation_form.html'):
    if (request.user.is_staff==True):
	organisation = get_object_or_404(Organisation, pk=pk)
    	form = OrganisationForm(request.POST or None, instance=organisation)
	try:
                organisation_code=Organisation_Code.objects.get(
                                    organisation=organisation)
        except Organisation_Code.DoesNotExist, e:
            	organisation_code = Organisation_Code(\
                                    organisation=organisation)
                random_code = randrange(1000000)
                random_org_code=str(organisation.id)+\
                                        str(random_code)
                organisation_code.code=random_org_code
                organisation_code.save()
	calendars = None
	calendars = Calendar.objects.filter(organisation=organisation)
	selected_calendar = None
	selected_calendar = organisation.calendar
	data = {}
	data['organisation'] = organisation
        data['organisation_code'] = organisation_code
        data['selected_calendar'] = selected_calendar
        data['calendars'] = calendars
	data['form'] = form
    	if form.is_valid():
		post = request.POST
        	form.save()
		code = post['id_code']
		organisation_code.code = code
		organisation_code.save()

		print("Checking if Holiday Calendar is given:")
                selected_calendar = post['holiday_calendar']
                new_holiday_calendar_name = post['holiday_name']
                print("new: " + new_holiday_calendar_name)
                hidden_holidays = post['hidden_holidays']
                if selected_calendar != None or selected_calendar != "":
                        if str(selected_calendar) != str(0):
                        	holiday_calendar = Calendar.objects.get(pk=int(selected_calendar))
                                if holiday_calendar:
                                        organisation.calendar = holiday_calendar
                                        organisation.save()
                                        print("Changed OK")
                                else:
                                        print("No cal found.");
                        else:
                                print("Making new calendar..")
                                if new_holiday_calendar_name != "" or new_holiday_calendar_name  != None:
                                        holiday_calendar, state, statesuccess = make_calendar_object(new_holiday_calendar_name, hidden_holidays, organisation)
                                        if holiday_calendar:
                                                organisation.calendar = holiday_calendar
                                                organisation.save()
                                                print("Made OK")

        	return redirect('organisation_table')
    	return render(request, template_name, data)

    else:
        print("Not a staff.")
        state="You do not have permission to see this page."
        return render(request, template_name, {'state':state})

"""
Super Admin option to delete an organisation
"""
@login_required(login_url='/login/')
def organisation_delete(request, pk, template_name='organisation/organisation_confirm_delete.html'):
    if (request.user.is_staff==True):
	organisation = get_object_or_404(Organisation, pk=pk)
    	if request.method=='POST':
		users= User.objects.filter(\
		    pk__in=User_Organisations.objects.filter(
			organisation_organisationid=organisation\
			    ).values_list(\
				'user_userid', flat=True))
		print("Marking organisation's users inactive.")
		for user in users:
			user.is_active = False
			user.save()
		print("Deleting organisation..")
        	organisation.delete()
        	return redirect('organisation_table')
    	return render(request, template_name, {'object':organisation})
    else:
        print("Not a staff.")
        state="You do not have permission to see this page."
        return render(request, template_name, {'state':state})

####################################

###################################
# UMCloud_Package CRUD

"""
Organisation Subscription package model
"""
class UMCloud_PackageForm(ModelForm):
    class Meta:
        model = UMCloud_Package

"""
Super Admin View of all subscription packages
"""
@login_required(login_url='/login/')
def umpackage_table(request, template_name='organisation/umpackage_table.html'):
    if (request.user.is_staff==True):
    	umpackages = UMCloud_Package.objects.all()
    	data = {}
    	data['object_list'] = umpackages
    	umpackages_as_json = serializers.serialize('json', umpackages)
    	umpackages_as_json =json.loads(umpackages_as_json)
    	return render(request, template_name, {'data':data, 'umpackages_as_json':umpackages_as_json})
    else:
        print("Not a staff.")
        state="You do not have permission to see this page."
        return render(request, template_name, {'state':state})

"""
Organisation Subscription : to create new
"""
@login_required(login_url='/login/')
def umpackage_create(request, template_name='organisation/umpackage_form.html'):
    if (request.user.is_staff==True):
	form = UMCloud_PackageForm(request.POST or None)
    	if form.is_valid():
        	form.save()
        	return redirect('umpackage_table')
    	return render(request, template_name, {'form':form})
    else:
        print("Not a staff.")
        state="You do not have permission to see this page."
        return render(request, template_name, {'state':state})

"""
To update organisation subscriptions 
only by super use/staff
"""
@login_required(login_url='/login/')
def umpackage_update(request, pk, template_name='organisation/umpackage_form.html'):
    if (request.user.is_staff==True):
	umpackage = get_object_or_404(UMCloud_Package, pk=pk)
    	form = UMCloud_PackageForm(request.POST or None, instance=umpackage)
    	if form.is_valid():
        	form.save()
        	return redirect('umpackage_table')
    	return render(request, template_name, {'form':form})
    else:
        print("Not a staff.")
        state="You do not have permission to see this page."
        return render(request, template_name, {'state':state})

"""
View for deleting a subscription. 
Only super user can have access to this.
"""
@login_required(login_url='/login/')
def umpackage_delete(request, pk, template_name='organisation/umpackage_confirm_delete.html'):
    if (request.user.is_staff==True):
	umpackage = get_object_or_404(UMCloud_Package, pk=pk)
    	if request.method=='POST':
        	umpackage.delete()
        	return redirect('umpackage_table')
    	return render(request, template_name, {'object':umpackage})
    else:
        print("Not a staff.")
        state="You do not have permission to see this page."
        return render(request, template_name, {'state':state})

####################################


class MyCronJob(CronJobBase):
    #RUN_EVERY_MINS = 120 # every 2 hours
    RUN_AT_TIMES = ['20:30']
    #RUN_AT_TIMES = ['16:22']

    #schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'organisation.my_cron_job'    # a unique code

    def do(self):
	print("Hey Hows it going!? If you can read this the cron job worked!")
	check_alert()

def check_alert():
    print("Hi, Checking alerts..")
    all_alerts = Alert.objects.all()
    if not all_alerts:
	print("No alerts found :( ")
	pass
    if all_alerts:
	print("Alerts found. Lets go through and check them..")
	try:
	  for every_alert in all_alerts:
	    check_these_allclasses = None
	    to_emails = every_alert.to_emails.split(',')
	    #Find which classes need to be checked in this alert 
	    if every_alert.allclasses == None:
		if every_alert.schools == None:
		    #Check all classes in the whole organisation 
		    organisation = every_alert.organisation;
		    check_these_allclasses = []
		    all_schools = School.objects.filter(organisation = organisation)
		    for every_school in all_schools: #TODO: Check 
			all_classes = Allclass.objects.filter(school = every_school)
			for every_class in all_classes:
			    check_these_allclasses.append(every_class)
		else:
		    check_these_allclasses = []
		    #Check all classes in schools provided..
		    for every_school in every_alert.schools.all():
			all_classes = Allclass.objects.filter(school = every_school)
			for every_allclass in all_classes: #TODO: Check! 
			    check_these_allclasses.append(every_allclass)
	    else:
		if every_alert.schools == None:
		    #Check all classes in allclasses provided..
		    check_these_allclasses  = every_alert.allclasses.all()
		else:
		    check_these_allclasses = []
		    #Check all classes in schools AND classes provided
		    for every_school in every_alert.schools.all():
			all_classes = Allclass.objects.filter(school = every_school)
			for each_class in all_classe:
			    check_these_allclasses.append(each_class)
		    for each_allclass in every_alert.allclasses.all():
			check_these_allclasses.append(each_allclass)

	    print("Got classes list:")
	    print(check_these_allclasses)

	    types = every_alert.types.all()
	    if not types:
		print("Could NOT find types for this alert..")
	    for type in types:
		if type.name == "missed_attendance":
		    print("Checking attendance for all classes..\n")
		    check_attendance_send_alert(check_these_allclasses, to_emails)
	except Exception as e:
	    print("Exception!: ")
	    print (e)
	   

def check_attendance_send_alert(check_these_allclasses, to_emails):
    for every_allclass in check_these_allclasses:
	print("Getting cut off time..")
	#Get cut off time
	cut_off_time = None
	try:
	    allclass_alert_settings = Allclass_alert_settings.objects.filter(allclass = every_allclass)
	except:
	    allclass_alert_settings = None
	try:
	    school_alert_settings = School_alert_settings.objects.filter(school = every_allclass.school)
	except:
	    school_alert_settings = None
	try:
	    org_alert_settings = Org_alert_settings.objects.filter(organisation = every_allclass.school.organisation)
	except:
	    org_alert_settings = None

	if allclass_alert_settings:
	    cut_off_time = allclass_alert_settings.cut_off_time
	elif school_alert_settings:
	    cut_off_time = school_alert_settings.cut_off_time
	elif org_alert_settings:
	    cut_off_time = org_alert_settings.cut_off_time
	else:
	    cut_off_time = 1 

	print("Got cut off time: " + str(cut_off_time))
	#Get class timing
	today_date = datetime.datetime.now().date()
	#TODO:Remove this
	#today_date = datetime.datetime.now().date() - timedelta(days = 1)
	if is_date_a_holiday(today_date, every_allclass):
	    #return or skip	
	    print("Today is a holiday for the class : " + str(every_allclass.allclass_name))
	    continue 
	#TODO:Remove this
	#today_date = datetime.datetime.now().date()

	#Check attendance for date
	yesterday_date = today_date - timedelta(days = 1)
	tomorrow_date = today_date + timedelta(days = 1)
	date_dict = get_attendance_daily(today_date, tomorrow_date, every_allclass)
	#TODO: Remove this
	#date_dict = get_attendance_daily(yesterday_date, today_date, every_allclass)
	today_date_pretty = today_date.strftime("%B %d, %Y")
	#TODO: Remove this
	#today_date_pretty = yesterday_date.strftime("%B %d, %Y")
	print("Today: " )
	print(today_date_pretty)
	if not date_dict:
	    teacher_names = []
	    teacher_names_string = ""
	    teachers_in_this_class = every_allclass.teachers.all()
	    for every_teacher_in_this_class in teachers_in_this_class:
		teacher_profile = UserProfile.objects.get(user=every_teacher_in_this_class)
		if teacher_profile.phone_number != "":
			phone_number = teacher_profile.phone_number
		if teacher_names_string == "":
		    teacher_names_string = every_teacher_in_this_class.first_name + ' ' +\
                        every_teacher_in_this_class.last_name + ' (' + phone_number + ')'
		else:
		    teacher_names_string = teacher_names_string + ', ' + every_teacher_in_this_class.first_name + ' ' +\
			every_teacher_in_this_class.last_name + ' (' + phone_number + ')' 
	    # Send alert
	    print("ATTENDANCE NOT TAKEN YET. SENDING ALERT FOR CLASS " + every_allclass.allclass_name)
	    current_email = "varuna@ustadmobile.com"
	    try:
		#TODO: Remvoe this
		#to_emails= []
		#to_emails.append('varuna@ustadmobile.com')
		send_mail('Attendance Alert: ' + every_allclass.allclass_name, \
			'\nHi,\n\nThis is to inform you that the class : ' \
			+ every_allclass.allclass_name + ' has not taken the attendance today (' + \
			today_date_pretty + '). The teacher(s) : ' + \
			teacher_names_string + '' + '\n\nRegards, \nUstad Mobile\ninfo@ustadmobile.com\n@ustadmobile', \
 			'info@ustadmobile.com' , to_emails, fail_silently=False)
	    except Exception as e:
		#authresponse = HttpResponse(status=506)
		#authresponse.write("Failed to send emails. Check if you have set it up and the settings are correct.")
		print("Couldn't send email..")
		print(e)

def test_send_mail(request):
    print("Testing email..")
    try:
    	send_mail('Test email','Hi,\n This is a test email. Please ignore it.\n\n',\
	    'info@ustadmobile.com', ['varuna@ustadmobile.com'], fail_silently=False)
    except Exception as e:
	print("Couldnt send email..")
	print(e)
    authresponse = HttpResponse(status = 200)
    authresponse.write("Got mail?")

# Create your views here.
