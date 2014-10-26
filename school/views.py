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
from organisation.models import Organisation
from organisation.models import UMCloud_Package
from organisation.models import User_Organisations
from school.models import School
from django.contrib import messages

from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
import datetime
import time
import os
import urllib
import urllib2, base64, json

###################################
# School CRUD

"""
This is the model form for school that outputs for 
view and edit the name and description of a school.
"""
class SchoolForm(ModelForm):
    class Meta:
        model = School
        fields = ('school_name', 'school_desc')

"""
This view renmders all schools in logged in users organisation.
It displays it to the template that renders it to a primeui table.
"""
@login_required(login_url='/login/')
def school_table(request, template_name='school/school_table.html', rstate=''):
    organisation = User_Organisations.objects.get(\
			user_userid=request.user\
			).organisation_organisationid;
    schools=School.objects.filter(organisation=organisation)
    organisation_schools = []
    data = {}
    data['object_list'] = schools
    data['orgschools_list'] = organisation_schools
    schools_as_json = serializers.serialize('json', schools)
    schools_as_json =json.loads(schools_as_json)
    return render(request, template_name, {\
			'data':data, \
			'schools_as_json':schools_as_json\
					})

"""
This view will render a new school create form and take in the form 
to create a new school as per POST parameters using School Model Form.
"""
@login_required(login_url='/login/')
def school_create(request, template_name='school/school_create.html', rstate=''):
    form = SchoolForm(request.POST or None)
    organisations=[]
    organisation = User_Organisations.objects.get(\
			user_userid=request.user\
			).organisation_organisationid;
    organisations.append(organisation)

    data = {}
    data['object_list'] = organisations

    if request.method == 'POST':
        post = request.POST;
        try:
		name = post['school_name']
		school_count = School.objects.filter(school_name=name).count()
		if school_count == 0:
                	print("Creating the School..")
			school_name = post['school_name']
			school_desc = post['school_desc']
 			currentorganisation=organisation
    			school = School(school_name=school_name, \
					school_desc=school_desc, \
					organisation=currentorganisation)
    			school.save()
    
    			print("Organisation School mapping success.")

			state="The School has been created."
			data['state']=state
			if 'submittotable' in request.POST:
                        	return render(request, 'school/confirmation.html', \
						data)
                	if 'submittonew' in request.POST:
				return render(request, \
					template_name, \
					data,\
					context_instance=RequestContext(request))
                	else:
                        	return redirect ('school_table')
        	else:
                	#Show message that the school name already 
			#exists in our database.
			state="The School Name already exists.."
                	data['state']=state
                	return render(request, template_name, data)
	except:
		print('Something went wrong')
    return render(request, template_name, data)


"""
This view will render a new school update form and take in the form 
to update the school by primary key and update as per 
POST parameters using School Model Form.
"""
@login_required(login_url='/login/')
def school_update(request, pk, template_name='school/school_form.html'):
    school = get_object_or_404(School, pk=pk)
    form = SchoolForm(request.POST or None, instance=school)
    if form.is_valid():
        form.save()
        return redirect('school_table')
    return render(request, template_name, {'form':form})

"""
This view will delete a school for the user that belongs to the same org.
"""
@login_required(login_url='/login/')
def school_delete(request, pk, template_name='school/school_confirm_delete.html'):
    organisation = User_Organisations.objects.get(\
			user_userid=request.user\
			).organisation_organisationid;
    try:
    	school = get_object_or_404(School, pk=pk)
    except:
	print("School doens't exist")
	return redirect('school_table')
    schools = School.objects.filter(organisation=organisation)
    if school not in schools:
	print("User trying to delete school from ANOTHER organisation!")
	return redirect('school_table')
    if request.method=='POST':
	#Check if school is in request.user's organisation 
	#and if request.user is not a Student..
        school.delete()
        return redirect('school_table')
    return render(request, template_name, {'object':school})

# Create your views here.
