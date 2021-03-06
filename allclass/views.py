#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.shortcuts import render

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
from allclass.models import Allclass
from uploadeXe.models import Role
from uploadeXe.models import User_Roles
from uploadeXe.models import Course

from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
import datetime
import time
import os
import urllib
import urllib2, base64, json
from django import forms #To fix issue #12
import logging

from reportlab.pdfgen import canvas
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter, A4
from sheetmaker.attendancesheet import AttendanceSheet

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from uploadeXe.models import DateTime
from uploadeXe.models import Weekday
from uploadeXe.models import Week_Day_Time

from holiday.models import Calendar
from holiday.views import make_calendar_object

from allclass.models import Enrollment

from sheetmaker.models import status_label, organisation_status_label

import uuid
import requests
from django.conf import settings

HOST_NAME = getattr(settings, "HOST_NAME", None)

logger = logging.getLogger(__name__)
module_dir = os.path.dirname(__file__)

###################################
# Allclass CRUD

"""
Model Form for Allclass that shows only Name, Desc and Location
"""
class AllclassForm(ModelForm):
    allclass_desc = forms.CharField(required = False) #To fix issue #12
    allclass_location = forms.CharField(required = False) #To fix issue #12
    class Meta:
        model = Allclass
	fields = ('id','allclass_name','allclass_desc','allclass_location')

"""
This view renders all classes in loged in user's organisation and
displays it to template that renders the primeui-table
"""
@login_required(login_url='/login/')
def allclass_table(request, template_name='allclass/allclass_table.html'):
    organisation = User_Organisations.objects.get(\
						user_userid=request.user\
						).organisation_organisationid;
    allclasses = Allclass.objects.filter(\
					school__in=School.objects.filter(\
						organisation=organisation)\
					);
    school_allclasses = []
    for allclass in allclasses:
	school_name=allclass.school.school_name
        school_allclasses.append(school_name)

    data = {}
    data['object_list'] = allclasses
    data['object_list'] = zip(allclasses, school_allclasses)
    data['school_list'] = school_allclasses
    allclasses_as_json = serializers.serialize('json', allclasses)
    allclasses_as_json =json.loads(allclasses_as_json)

    return render(request, template_name, {'data':data, 'allclasses_as_json':allclasses_as_json})

"""
This view will render a new alclass create form and take in the form 
to create a new class as per POST parameters using Allclass Model Form.
"""
@login_required(login_url='/login/')
def allclass_create(request, template_name='allclass/allclass_create.html'):
    form = AllclassForm(request.POST or None) #gets the All class form.
    organisation = User_Organisations.objects.get(\
						user_userid=request.user\
						).organisation_organisationid;
    schools = School.objects.filter(organisation=organisation)
    calendars = Calendar.objects.filter(organisation=organisation)
	
    school_calendar = None
    #school_calendar = allclass.school.holidays.all()[0]

    teacher_role = Role.objects.get(pk=5)
    if teacher_role.role_name != "Teacher":
	teacher_role.Role.objects.get(role_name="Teacher")
    student_role = Role.objects.get(pk=6)
    if student_role.role_name != "Student":
	student_role.role_name = Role.objects.get(role_name="Student")
    
    # Get all users in the user's organisation and
    # role is a teacher
    teachers = User.objects.filter(\
		pk__in=User_Organisations.objects.filter(\
		    organisation_organisationid=organisation\
			).values_list('user_userid', flat=True)\
		).filter(\
		    pk__in=User_Roles.objects.filter(\
			role_roleid=teacher_role).values_list(\
				'user_userid', flat=True))
    # Get all users in user's organisation and
    # role is a student
    students = User.objects.filter(\
		pk__in=User_Organisations.objects.filter(\
		    organisation_organisationid=organisation\
			).values_list('user_userid', flat=True)\
		).filter(\
		    pk__in=User_Roles.objects.filter(\
			role_roleid=student_role).values_list(\
			    'user_userid', flat=True))

    everyone = User.objects.filter(\
		pk__in=User_Organisations.objects.filter(\
		    organisation_organisationid=organisation\
			).values_list('user_userid', flat=True))

    students = everyone #To make sure we don't just have to
			#have students assigned to class

    courses = Course.objects.filter(success="YES",\
				organisation=organisation)
    org_calendar = None
    org_calendar = organisation.calendar
    if not org_calendar:
        org_calendar = None

    data = {}
    data['object_list'] = schools
    data['teacher_list'] = teachers
    data['student_list'] = students
    data['course_list'] = courses
    data['calendars'] = calendars
    data['school_calendar'] = school_calendar
    data['org_calendar']=org_calendar

    if request.method == 'POST':
        post = request.POST;
	class_name = post['class_name']
	days_ids = post.getlist('days')
	logger.info("Day IDS: " + str(days_ids))
	allclass_count = Allclass.objects.filter(\
			allclass_name=class_name).count()
	#Creating the class..
    	if allclass_count == 0:
                print("Creating the Class..")
		class_name=post['class_name']
		class_desc=post['class_desc']
		class_location=post['class_location']

		studentidspicklist=post.getlist('target')
		print("students selected from picklist:")
		print(studentidspicklist)

		courseidspicklist=post.getlist('target2')
		print("courses selected from picklist")
		print(courseidspicklist)
		
		#Mapping school to class..
		try:
                        schoolid=post['schoolid']
			currentschool = School.objects.get(pk=schoolid)
                
                	allclass = Allclass(allclass_name=class_name, \
					allclass_desc=class_desc, \
					allclass_location=class_location,\
					school=currentschool)
                	allclass.save()
                	school = School.objects.get(pk=schoolid)
                	print("Class School mapping success.")

                except:
                        print("No school given")
			allclass = Allclass(allclass_name=class_name, \
					allclass_desc=class_desc, \
					allclass_location=class_location)
                        allclass.save()


		print("Class Students mapping success.")

		#Create Class - StudentS mapping
		for everystudentid in studentidspicklist:
			try:
				currentstudent=User.objects.get(\
						pk=everystudentid)
				#allclass.students.add(currentstudent)
				#Changed
				allclass.students_add(currentstudent)
				allclass.save()
			except:
				pass

		for everycourseid in courseidspicklist:
			try:
				currentcourse = Course.objects.get(\
							pk=everycourseid)
				for everystudentid in studentidspicklist:
					currentstudent=User.objects.get(\
							pk=everystudentid)
					currentcourse.students.add(\
							currentstudent)
			except:
				pass
		
		print("Mapping of courses and students done for all students in the class")
			
		try:
			teacherid=post['teacherid']
			currentteacher=User.objects.get(pk=teacherid)
			allclass.teachers.add(currentteacher)
			allclass.save()
		except:
			print("No teacher given")

		print("Mapping days for this class..");	

		for day_id in days_ids:
			this_day = Weekday.objects.get(pk=day_id)
			this_week_day_time = Week_Day_Time(day=this_day)
			this_week_day_time.save()
			allclass.days.add(this_week_day_time)
		allclass.save()

		print("Mapping holiday calendar if any")
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
                                	if allclass.holidays.all():
                                        	allclass.holidays.clear()
                                	allclass.holidays.add(holiday_calendar)
					allclass.save()
                                	print("Changed OK")
                        	else:
                                	print("No cal found.");
                	else:
                        	print("Making new calendar..")
                        	if new_holiday_calendar_name != "" or new_holiday_calendar_name  != None:
                                	holiday_calendar, state, statesuccess = make_calendar_object(new_holiday_calendar_name, hidden_holidays, organisation)
                                	if holiday_calendar:
                                        	allclass.holidays.clear()
                                        	allclass.holidays.add(holiday_calendar)
                                        	allclass.save()
                                        	print("Made OK")

		data['state']="The class: " + allclass.allclass_name + " has been created."

		if 'submittotable' in request.POST:
			statesuccess=1
                        data['statesuccess']=statesuccess
			return render(request,'allclass/confirmation.html',data)

                if 'submittonew' in request.POST:
			statesuccess=1
                        data['statesuccess']=statesuccess
			return render(request, template_name, data)
                else:
                        return redirect ('allclass_table')
        else:
                #Show message that the class name already exists in our database.\
		# (For the current organisation)
		state="The Class Name already exists.."
                data['state']=state
                return render(request, template_name, data)

    return render(request, template_name, data)

"""Splits an Array in chunks by chunk size
"""
def split_list(list, chunk_size):
	result_list = []
	while list:
		result_list.append(list[:chunk_size])
		list = list[chunk_size:]
	return result_list

def whatisthis(s):
    if isinstance(s, str):
        print "ordinary string"
    elif isinstance(s, unicode):
        print "unicode string"
    else:
        print "not a string"

"""
This will start the Class Attendance Sheet PDF generation for class given
"""
@login_required(login_url='/login/')
def allclass_makepdf(request, allclass_id):
    logger.info("Making pdf")
    organisation = User_Organisations.objects.get(\
                        user_userid=request.user\
                        ).organisation_organisationid;
    allclass = get_object_or_404(Allclass, pk=allclass_id)
    #Check if you have access to do this.
    logger.info("Checking permissions..")
    allclass_org = allclass.school.organisation
    if allclass_org != organisation:
	return redirect('allclass_table')
    logger.info("Generating pdf..")

    pdfmetrics.registerFont(TTFont("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))

    #student_list = allclass.students.all()
    #Changed:
    student_list = allclass.students_all()
	
    logger.info(len(student_list))
    student_name_list = []

    for every_student in student_list:
	#student_name_list.append(every_student.first_name + " " + every_student.last_name)
	add_this = every_student.first_name + " " + every_student.last_name
	print("Type of add_this variable:")
	print(type(add_this))
	maybe_add_this = add_this.encode('utf-8').decode('utf-8')
	student_name_list.append(add_this)
	print(student_name_list)

	"""
	name_test=u'ﺲﺸﻤﺷﺓ'
	name_test_encoded = name_test.encode('utf-8')
	print(name_test_encoded)
	student_name_list.append(name_test)
	"""

	"""
	print("Value:")
	#print(every_student.first_name)
	print("Value type:")
	print(type(every_student.first_name))
	print("Encode utf")
	print(every_student.first_name.encode('utf-8'))
	print("Decode utf")
	#print(every_student.first_name.decode('utf-8'))
	print("Encode ascii")
	#print(every_student.first_name.encode('ascii'))
	"""

    logger.info("Number of students: " + str(len(student_name_list)))
    response = HttpResponse(content_type = "application/pdf")

    split_student_name_list = split_list(student_name_list, 66)
    logger.info("Number of sheets: " + str(len(split_student_name_list)))
    if split_student_name_list is None or split_student_name_list == "" or split_student_name_list == []:
        return redirect('allclass_table')

    canvas = Canvas(response, pagesize = A4)    
    present = None
    late = None
    excused = None
    absent = None
    selected_status_label = []
    selected_org_status_label = organisation_status_label.objects.filter(organisation=organisation)
    if not selected_org_status_label:
	present = "Present"
	absent = "Absent"

    for every_osl in selected_org_status_label:
	selected_status_label.append(every_osl.status_label)
    for every_label in selected_status_label:
	if every_label.name == "Present":
	    present = every_label.name
	if every_label.name == "Late":
	    late = every_label.name
	if every_label.name == "Excused":
	    excused = every_label.name
	if every_label.name == "Absent":
	    absent = every_label.name
	    
    i=0;
    for every_sheet in split_student_name_list:
	i = i + 1;
	logger.info("Sheet: " + str(i))
	sheet = AttendanceSheet( student_names = every_sheet, \
			#status_labels = ["Present", None, None, "Absent"], \
			status_labels = [present, late, excused, absent],\
			#status_labels = ["Present", "Late", "Excused", "Absent"],\
			title = str(allclass.allclass_name + \
				", ID: " + str(allclass.id) + ", Page " + str(i) +"/"+ \
				str(len(split_student_name_list))), label_font="DejaVuSans")
	sheet.render_to_canvas(canvas)
	logger.info("Sheet Created")
    #sheet.make_canvas(response)
    canvas.save()
    logger.info("returning sheet..")
    return response

"""
Create Statement JSON
create_statement_json(\
                        first_teacher, \ #Authority
                        "http://activitystrea.ms/schema/1.0/host", "hosted",\ #Verb
                        "http://www.ustadmobile.com/activities/attended-class/" + allclass.id,\ #Object
                        "Attended "+allclass.allclass_name+" class",\ #Object
                        registration_id, \ #Registration
                        None \ #Actor
                        )
"""
def create_statement_dict(authority, verb_id, verb_name, object_id, \
    object_name, registration_id, actor, timestamp_object):
    timestamp = timestamp_object.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
    statement_json = {}
    statement_json['version'] = "1.0.1"
    #.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
    #authority_profile = UserProfile.objects.get(user=authority)
    if actor is None:
	actor = authority

    verb_json={}
    verb_name_json={}
    #statement_json['key'] = value
    verb_json['id'] = verb_id
    verb_name_json['en-US'] = verb_name
    verb_json['display'] = verb_name_json

    object_json={}
    object_definition_json = {}
    object_name_json = {}
    object_name_json['en-US'] = object_name
    object_definition_json['name'] = object_name_json
    object_json['definition'] = object_definition_json
    object_json['id'] = object_id
    object_json['objectType'] = "Activity"
    
    authority_json = {}
    authority_json['mbox'] = "mailto:" + authority.email
    authority_json['name'] = authority.username
    authority_json['objectType'] = "Agent"

    context_json = {}
    if registration_id is not None:
	if actor is None:
        	context_json['registration'] = registration_id
	else:
		instructor_account= {}
		instructor_json = {}
		instructor_account['homePage'] = HOST_NAME + "/umlrs/"
		instructor_account['name'] = authority.username
		instructor_json['account'] = instructor_account
		instructor_json['objectType'] = "Agent"
		context_json['registration'] = registration_id
		context_json['instructor'] = instructor_json
		

    if actor is None:
	actor = authority

    actor_json = {}
    actor_account = {}
    actor_account['homePage'] = HOST_NAME + "/umlrs/"
    actor_account['name'] = actor.username
    actor_json['account'] = actor_account
    actor_json['objectType'] = "Agent"

    statement_json['object'] = object_json
    statement_json['authority'] = authority_json
    statement_json['verb'] = verb_json
    statement_json['actor'] = actor_json
    statement_json['context'] = context_json
    statement_json['timestamp'] = timestamp

    return statement_json


"""
This will show the attendance form to be taken online
"""
@login_required(login_url='/login/')
def attendance_form(request, pk, template_name='allclass/attendance_form.html'):
    organisation = User_Organisations.objects.get(\
                        user_userid=request.user\
                        ).organisation_organisationid;
    allclass = get_object_or_404(Allclass, pk=pk)
    form = AllclassForm(request.POST or None, \
                                instance=allclass)

    #Assigned Student mapping
    student_role = Role.objects.get(pk=6)
    if student_role.role_name != "Student":
        student_role = Role.objects.get(role_name="Student")
    allstudents = User.objects.filter(\
        pk__in=User_Organisations.objects.filter(\
            organisation_organisationid=organisation\
                ).values_list('user_userid', flat=True)\
        ).filter(\
            pk__in=User_Roles.objects.filter(\
                role_roleid=student_role).values_list(\
                    'user_userid', flat=True))

    #assignedstudents=allclass.students.all();
    #Changed:
    assignedstudents=allclass.students_all();


    #Assigned Teachers mapping
    teacher_role = Role.objects.get(pk=5)
    if teacher_role.role_name != "Teacher":
        teacher_role = Role.objects.get(role_name="Teacher")
    allteachers = User.objects.filter(\
        pk__in=User_Organisations.objects.filter(\
            organisation_organisationid=organisation\
                ).values_list('user_userid', flat=True)\
        ).filter(\
            pk__in=User_Roles.objects.filter(\
                role_roleid=teacher_role).values_list(\
                    'user_userid', flat=True))
    assignedteachers=allclass.teachers.all();

    allcourses=Course.objects.filter(organisation=organisation)
    assignedcourses=Course.objects.filter(\
                                allclasses__in =[allclass])
    today = datetime.datetime.now().date().strftime("%b %d %Y")
    a_list=[0,1,2,3]
    dates = []
    for every_item in a_list:
	dates.append((datetime.datetime.now() - datetime.timedelta(days=every_item)).date().strftime("%b %d, %Y"))
	


    if request.method == 'POST':
        post = request.POST;
	print(post)
	try:
		attendance_date_id = int(post['date'])
		attendance_date = datetime.datetime.now() - datetime.timedelta(days=attendance_date_id)
		print("Attendance date time id: " + str(attendance_date_id))
		print("Attendance date time: " + str(attendance_date))
	except:
		attendance_date = datetime.datetime.now()
		print("Attendance date exception. Taking today..")
	statements_to_send = []
        if request.POST:
		registration_dict = {}
		registration_id = str(uuid.uuid4())
		first_teacher = assignedteachers[0]
		registration_dict = create_statement_dict(\
			first_teacher, \
			"http://activitystrea.ms/schema/1.0/host", "hosted",\
			"http://www.ustadmobile.com/activities/attended-class/" + str(allclass.id),\
			"Attended "+allclass.allclass_name+" class",\
			registration_id, \
			None, \
			attendance_date \
			)
		registration_json = json.dumps(registration_dict)
		#statements_to_send.append(registration_json)
		statements_to_send.append(registration_dict)
			
	for key in request.POST:
		student_dict = {}
                if "_radio" in key:
                        value=request.POST[key]
                        userid, action = value.split("_")
                        if action == '1':
				#Attended
                                logger.info("User Present")
                                usertoattend=User.objects.get(pk=userid)
				student_dict = create_statement_dict(\
					first_teacher,\
					"http://adlnet.gov/expapi/verbs/attended", "Attended",\
					"http://www.ustadmobile.com/activities/attended-class/" + str(allclass.id),\
					"Attended " + allclass.allclass_name + " class",\
					registration_id,\
					usertoattend,\
					attendance_date \
					)

                        if action == '0':
				#Skipped
                                logger.info("User Absent ")
                                usertoabsent=User.objects.get(pk=userid)
				student_dict = create_statement_dict(\
					first_teacher,\
					"http://id.tincanapi.com/verb/skipped", "Skipped",\
                                        "http://www.ustadmobile.com/activities/attended-class/" + str(allclass.id),\
                                        "Attended " + allclass.allclass_name + " class",\
                                        registration_id,\
					usertoabsent,\
					attendance_date\
					)
			student_json = json.dumps(student_dict)
			#statements_to_send.append(student_json)
			statements_to_send.append(student_dict)
	#Send Statements
	statements_to_send_json = json.dumps(statements_to_send)
	headers = {'X-Experience-API-Version':'1.0.1'}
	cred_file_path = os.path.join(module_dir, 'cred.txt')
	cred_file = open(cred_file_path,  'r')
	cred_lines=cred_file.readlines()
	username=cred_lines[0].rstrip()
	password=cred_lines[1].rstrip()
	r = requests.post(HOST_NAME + "/umlrs/statements", \
		statements_to_send_json, headers=headers,\
		auth=(username, password))
	print("Result:")
	print(r.status_code)
	print(r)
	
		
	return redirect ('allclass_table')

	

    pagetitle="Attendance Form for Class:" + allclass.allclass_name
    tabletypeid="tblattendanceform"
    table_headers_html=[]
    table_headers_name=[]
    table_headers_html.append("radio")
    table_headers_name.append("Present")
    table_headers_html.append("radio2")
    table_headers_name.append("Absent")
    table_headers_html.append("fields.first_name")
    table_headers_name.append("First Name")
    table_headers_html.append("fields.last_name")
    table_headers_name.append("Last Name")
    table_headers_html.append("fields.username")
    table_headers_name.append("Username")

    table_headers_html = zip(table_headers_html, table_headers_name)
    logicpopulation = '{"pk":"{{c.pk}}","model":"{{c.model}}", "username":"{{c.fields.username}}","first_name":"{{c.fields.first_name}}"}{% if not forloop.last %},{% endif %}'

    return render(request, template_name, \
                {\
                        'assigned_students':assignedstudents,\
                        'assigned_teachers':assignedteachers,\
                        'allclass':allclass,\
			'today': today,\
			'all_dates':zip(dates,a_list),\
			'table_headers_html':table_headers_html,\
			'pagetitle':pagetitle,\
			'tabletypeid':tabletypeid,\
                })

    


"""
This view will update a new alclass update form and take in the form 
to update a new class as per POST parameters using Allclass Model Form.
"""
@login_required(login_url='/login/')
def allclass_update(request, pk, template_name='allclass/allclass_form.html'):
    organisation = User_Organisations.objects.get(\
			user_userid=request.user\
			).organisation_organisationid;
    allclass = get_object_or_404(Allclass, pk=pk)
    form = AllclassForm(request.POST or None, \
				instance=allclass)

    #Assigned Student mapping
    student_role = Role.objects.get(pk=6)
    if student_role.role_name != "Student":
	student_role = Role.objects.get(role_name="Student")
    allstudents = User.objects.filter(\
	pk__in=User_Organisations.objects.filter(\
	    organisation_organisationid=organisation\
	   	).values_list('user_userid', flat=True)\
	).filter(\
	    pk__in=User_Roles.objects.filter(\
		role_roleid=student_role).values_list(\
		    'user_userid', flat=True))

    #assignedstudents=allclass.students.all();
    #Changed:
    assignedstudents=allclass.students_all();

    unassigned_students = list(set(allstudents) - set(assignedstudents))

    #Assigned Teachers mapping
    teacher_role = Role.objects.get(pk=5)
    if teacher_role.role_name != "Teacher":
	teacher_role = Role.objects.get(role_name="Teacher")
    allteachers = User.objects.filter(\
	pk__in=User_Organisations.objects.filter(\
	    organisation_organisationid=organisation\
		).values_list('user_userid', flat=True)\
	).filter(\
	    pk__in=User_Roles.objects.filter(\
		role_roleid=teacher_role).values_list(\
		    'user_userid', flat=True))
    assignedteachers=allclass.teachers.all();

    allcourses=Course.objects.filter(organisation=organisation)
    assignedcourses=Course.objects.filter(\
				allclasses__in =[allclass])

    all_days = allclass.days.all();
    #logger.info(all_days)

    allschools=School.objects.filter(organisation=organisation)
    assignedschool=allclass.school

    calendars = Calendar.objects.filter(organisation=organisation)
    allclass_calendars = allclass.holidays.all()
    selected_calendar = None
    if allclass_calendars:
        selected_calendar = allclass_calendars[0]
    school_calendar = None

    try:
        school_calendar = allclass.school.holidays.all()[0]
    except:
        if not school_calendar:
		school_calendar = None

    school_calendar = None
    if allclass.school.holidays.all():
    	school_calendar = allclass.school.holidays.all()[0]

    org_calendar = None
    org_calendar = organisation.calendar
    if not org_calendar:
	org_calendar = None


    if form.is_valid():
        form.save()
	
	print("Going to update the assigned school..")
	schooliddropdown=request.POST.get('school')
	try:
		schooldropdown = School.objects.get(\
					pk=schooliddropdown)
	except:
		pass
		schooldropdown=None
	allclass.school=schooldropdown

        print("Going to update the assigned students..")
        studentidspicklist=request.POST.getlist('target')
	if studentidspicklist:
        	#allclass.students.clear()
		#Changed:
		#New way of clearing student list from Class' enrollment
		#"Clearning relationships"
                #Can't clear relationships becaue if we do then
                # we add whatevers on the list, then the dates
                # on the enrollment will be updated for all.
                # We have to handle removal in a different way..
		pass
        #assigned_students = allclass.students.all();
   	#Changed:
	assigned_students = allclass.students_all();
	students_to_remove = []
	students_worked_on = []
	date_now = datetime.datetime.now()
	#Changed:
	#Maybe get rid of the add bit here
	print("Assigned Students list: " + str(studentidspicklist) + " with len: " + str(len(studentidspicklist)))
	if len(studentidspicklist) > 0: 
            for everystudentid in studentidspicklist:
                currentstudent=User.objects.get(\
			pk=everystudentid)
		students_worked_on.append(currentstudent)
                #allclass.students.add(currentstudent)
		"""
		#Don't do this if we are adding it later
		allclass.students_add(currentstudent)
		"""
                #allclass.save()
	else:
	    students_worked_on = assigned_students

	students_to_remove = list(set(assigned_students) - set(students_worked_on))
	for every_student_to_remove in students_to_remove:
		#Changed/Added:
		allclass.students_remove(every_student_to_remove)
		allclass.save()
	students_to_add = list(set(students_worked_on) - set(assigned_students))
	for every_student_to_add in students_to_add:
		print("Adding student")
		#Changed/Added:
		allclass.students_add(every_student_to_add)
		allclass.save()

        print("Going to update the assigned teacher..")
        teacheridspicklist=request.POST.getlist('target2')
	if teacheridspicklist:
        	allclass.teachers.clear()
        assignedclear = allclass.teachers.all();
        for everyteacherid in teacheridspicklist:
                currentteacher=User.objects.get(\
					pk=everyteacherid)
                allclass.teachers.add(currentteacher)
                allclass.save()

	print("Going to update the assigned course")
	courseidspicklist=request.POST.getlist('target3')
	

	if courseidspicklist:
		logger.info("Got to clear class courses before re adding..")
		allassignedcourses = Course.objects.filter(allclasses__in=[allclass])
		for everycourse in allassignedcourses:
			everycourse.allclasses.remove(allclass)

	for everycourseid in courseidspicklist:
		everycourse = Course.objects.get(\
					pk=everycourseid)
		everycourse.allclasses.add(allclass)
		everycourse.save()

	days_ids = request.POST.getlist('days')
	print("Mapping days for this class..");

	if days_ids != None:
	    print("Clearing all the days..")
	    allclass.days.clear()
	    allclass.save()
	for day_id in days_ids:
		this_day = Weekday.objects.get(pk=day_id)
		this_week_day_time = Week_Day_Time(day=this_day)
		this_week_day_time.save()
		allclass.days.add(this_week_day_time)
	allclass.save()
	
	print("Mapping holidays..")
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
                                if allclass.holidays.all():
                                        allclass.holidays.clear()
                                allclass.holidays.add(holiday_calendar)
				allclass.save()
                                print("Changed OK")
                        else:
                                print("No cal found.");
                else:
                        print("Making new calendar..")
                        if new_holiday_calendar_name != "" or new_holiday_calendar_name  != None:
                                holiday_calendar, state, statesuccess = make_calendar_object(new_holiday_calendar_name, hidden_holidays, organisation)
                                if holiday_calendar:
                                        allclass.holidays.clear()
                                        allclass.holidays.add(holiday_calendar)
                                        allclass.save()
                                        print("Made OK")
	
        return redirect('allclass_table')
    else:
	print("ALLCLASS UPDATE FORM IS NOT VALID")
	print("...Or just viewing the class.")
	
    return render(request, template_name, \
		{'form':form,'all_schools':allschools, \
			'assignedschool':assignedschool, \
			'all_courses':allcourses, \
			'assigned_courses':assignedcourses, \
			'all_students' : unassigned_students,\
			'assigned_students':assignedstudents,\
			'all_teachers':allteachers,\
			'assigned_teachers':assignedteachers,\
			'allclass':allclass,\
			'alldays':all_days,\
			'selected_calendar':selected_calendar,\
			'calendars':calendars,\
			'school_calendar':school_calendar,\
			'org_calendar':org_calendar\
			
		})

"""
View to delete allclass if required.
"""
@login_required(login_url='/login/')
def allclass_delete(request, pk, template_name='allclass/allclass_confirm_delete.html'):
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid;
    try:
        allclass = get_object_or_404(Allclass, pk=pk)
    except:
	return redirect('allclass_table')
    allclasses=Allclass.objects.filter(school__in=School.objects.filter(organisation=organisation));

    #User can only delete his organisations' class
    if allclass not in allclasses:
  	print("User trying to delete class not in its organisation!")
	return redirect ('allclass_table')

    if request.method=='POST':
	#Need to enable only organisation admins to teachers the ability to delete a class
        allclass.delete()
        return redirect('allclass_table')
    return render(request, template_name, {'object':allclass})

"""
Gets the max number of enrollments in that class and returns the next
available roll number
"""
def get_next_roll_number(allclass):
	print("Roll number calculation")
        no = len(User.objects.filter(enrollment__allclass = allclass))
        try:
            max_roll_number = Enrollment.objects.filter(allclass = allclass).order_by("-roll_number")[0].roll_number
	    print("Max: " + str(max_roll_number) + " no: " + str(no))
            if max_roll_number != no and max_roll_numbr != 0:
                print("Max roll number not equal to the number of students. I wonder why.")
                if max_roll_number > no:
                    print("Taking the next roll number")
                    no = max_roll_number
	    if max_roll_number == 0:
		no = None
        except:
            pass
        if not no:
                return 1
        else:
                no = no + 1
                return no


"""
Internal API to migrate all class students to new Through enrollment Many to Many
Relationship table
"""
@login_required(login_url='/login/')
def migrate_allclass_students_enrollment(request):
    print("hey")
    if not request.user.is_superuser:
        authresponse = HttpResponse(status=403)
        authresponse.write("Forbidden.")
        return authresponse
    else:
    	"""
    	We basically want to move existing students in .students to the new enrollment 
    	We can do that over the db command line. That may not be so bad. Maybe not look above
    	Or we write some logic over here
    	"""
	date_now = datetime.datetime.now()
	try:
    	    all_classes_umcloud = Allclass.objects.all()
    	    for every_class_umcloud in all_classes_umcloud:
	    	students_every_class = every_class_umcloud.students.all()
	    	for every_student in students_every_class:
	    	    enroll = Enrollment(user = every_student, active = True,\
	    	    allclass = every_class_umcloud)
		    roll_number = get_next_roll_number(every_class_umcloud)
		    roll_number_date = date_now + datetime.timedelta(0, roll_number)
		    enroll.date_joined = roll_number_date
		    enroll.roll_number = roll_number
	    	    enroll.save()
	except Exception, e:
	    print("Something went wrong in Students to Enrollment Migration")
	    print(e)
  	    print(str(e))


        authresponse = HttpResponse(status=200)
        authresponse.write("Allclasses Student to Enrollment Migration Done.")
        return authresponse

# Create your views here.
