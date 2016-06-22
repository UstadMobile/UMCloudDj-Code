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

from allclass.models import Allclass
from allclass.views import split_list
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter, A4
from sheetmaker.attendancesheet import AttendanceSheet

from uploadeXe.models import Weekday
from holiday.models import Calendar
from holiday.views import make_calendar_object

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
    calendars = Calendar.objects.filter(organisation=organisation)

    data = {}
    data['object_list'] = organisations
    data['calendars'] = calendars
    selected_calendar = None
    selected_calendar = organisation.calendar
    if not selected_calendar:
	selected_calendar = None
    data['selected_calendar'] = selected_calendar

    if request.method == 'POST':
        post = request.POST;
        try:
		name = post['school_name']
		weekends_id = post.getlist('days')
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

			print("School Weekend mapping");
			if weekends_id:
			    school.weekends.clear()
			for day_id in weekends_id:
			    this_day = Weekday.objects.get(pk=day_id)
			    school.weekends.add(this_day)
			    school.save()
			
			print("Checking if Holiday Calendar is given:")
			print(post)
			selected_calendar = post['holiday_calendar']
			new_holiday_calendar_name = post['holiday_name']
			print("new: " + new_holiday_calendar_name)
			hidden_holidays = post['hidden_holidays']
			if selected_calendar != None or selected_calendar != "":
				if str(selected_calendar) != str(0):
					print(selected_calendar)
					print(type(selected_calendar))
					print("Selecting the calendar : " + str(selected_calendar))
					holiday_calendar = Calendar.objects.get(pk=int(selected_calendar))
					if holiday_calendar:
						if school.holidays.all():
							school.holidays.clear()
						school.holidays.add(holiday_calendar)
						school.save()
						print("Changed OK")
					else:
						print("No cal found.");
				else:
					print("Making new calendar..")
					if new_holiday_calendar_name != "" or new_holiday_calendar_name  != None:
						holiday_calendar, state, statesuccess = make_calendar_object(new_holiday_calendar_name, hidden_holidays, organisation)
						if holiday_calendar:
							school.holidays.clear()
							school.holidays.add(holiday_calendar)
							school.save()
							print("Made OK")
						
				

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
	except Exception as e:
		print('Something went wrong')
		print(str(e))
    return render(request, template_name, data)


"""
This view will render a new school update form and take in the form 
to update the school by primary key and update as per 
POST parameters using School Model Form.
"""
@login_required(login_url='/login/')
def school_update(request, pk, template_name='school/school_form.html'):
    school = get_object_or_404(School, pk=pk)
    weekends = school.weekends.all()
    form = SchoolForm(request.POST or None, instance=school)
    organisation = User_Organisations.objects.get(\
                        user_userid=request.user\
                        ).organisation_organisationid;
    calendars = Calendar.objects.filter(organisation=organisation)
    school_calendars = school.holidays.all()
    selected_calendar = None
    if school_calendars:
	selected_calendar = school_calendars[0]
    org_calendar = None
    org_calendar = organisation.calendar
    if not org_calendar:
        org_calendar = None

    data = {}
    data['form'] = form
    data['school'] = school
    data['calendars'] = calendars
    data['weekends'] = weekends
    data['selected_calendar'] = selected_calendar
    data['org_calendar'] = org_calendar
    if form.is_valid():
        form.save()
	post = request.POST
	weekend_ids = request.POST.getlist('days')
	print("School Weekend mapping");
        if weekend_ids:
        	school.weekends.clear()
        for day_id in weekend_ids:
               	this_day = Weekday.objects.get(pk=day_id)
                school.weekends.add(this_day)
                school.save()

	print("Checking if Holiday Calendar is given:")
	post = request.POST
        selected_calendar = post['holiday_calendar']
        new_holiday_calendar_name = post['holiday_name']
        print("new: " + new_holiday_calendar_name)
        hidden_holidays = post['hidden_holidays']
        if selected_calendar != None or selected_calendar != "":
                if str(selected_calendar) != str(0):
                        print(selected_calendar)
                        print(type(selected_calendar))
                        print("Selecting the calendar : " + str(selected_calendar))
                        holiday_calendar = Calendar.objects.get(pk=int(selected_calendar))
                        if holiday_calendar:
                                if school.holidays.all():
                                        school.holidays.clear()
                                school.holidays.add(holiday_calendar)
				school.save()
                                print("Changed OK")
                        else:
                                print("No cal found.");
                else:
                        print("Making new calendar..")
                        if new_holiday_calendar_name != "" or new_holiday_calendar_name  != None:
                                holiday_calendar, state, statesuccess = make_calendar_object(new_holiday_calendar_name, hidden_holidays, organisation)
                                if holiday_calendar:
                                        school.holidays.clear()
                                        school.holidays.add(holiday_calendar)
                                        school.save()
                                        print("Made OK")




        return redirect('school_table')
    return render(request, template_name, data)

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

"""School Attendance Pdf generation
"""
def attendance_pdf(request, school_id):
    school = get_object_or_404(School, pk=school_id)
    user_organisation = User_Organisations.objects.get(\
	user_userid=request.user\
	).organisation_organisationid;
    school_organisation = school.organisation
    if user_organisation != school_organisation:
	print("You do not have access")
	return redirect('school_table')

    response = HttpResponse(content_type = "application/pdf")
    canvas = Canvas(response, pagesize = A4)
    #Generate student_name_list
    #Get all classes in this school:
    allclasses = Allclass.objects.filter(school=school)
    student_name_list = []
    for every_class in allclasses:
	student_name_list=[]
	allstudents = every_class.students.all()
	for every_student in allstudents:
		student_name_list.append(every_student.first_name + " " + every_student.last_name)
	split_student_name_list = split_list(student_name_list, 66)
	if split_student_name_list is None or split_student_name_list == "" or split_student_name_list == []:
		continue
	i=0;
	print("Class: " + every_class.allclass_name + " has " + str(len(student_name_list)) + " studnets.")
	for every_sheet in split_student_name_list:
		i = i + 1;
		sheet = AttendanceSheet( student_names = every_sheet, \
                        status_labels = ["Present", None, None, "Absent"], \
			title = str(every_class.allclass_name + \
				" Class, Page " + str(i) + "/" + \
				str(len(split_student_name_list))))
		sheet.render_to_canvas(canvas)
    canvas.save()
    print("returning school sheet..")
    return response
# Create your views here.
