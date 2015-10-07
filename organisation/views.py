
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
import time
import os
import urllib
import urllib2, base64, json
from random import randrange


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
    	if form.is_valid():
        	form.save()
        	return redirect('organisation_table')
    	return render(request, template_name, {'form':form})

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


# Create your views here.
