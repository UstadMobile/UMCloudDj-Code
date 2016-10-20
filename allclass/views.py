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

from uploadeXe.models import DateTime
from uploadeXe.models import Weekday
from uploadeXe.models import Week_Day_Time

from holiday.models import Calendar
from holiday.views import make_calendar_object

from allclass.models import Enrollment

logger = logging.getLogger(__name__)

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
    #student_list = allclass.students.all()
    #Changed:
    student_list = allclass.students_all()
	
    logger.info(len(student_list))
    student_name_list = []

    for every_student in student_list:
	student_name_list.append(every_student.first_name + " " + every_student.last_name)

    logger.info("Number of students: " + str(len(student_name_list)))
    response = HttpResponse(content_type = "application/pdf")

    split_student_name_list = split_list(student_name_list, 66)
    logger.info("Number of sheets: " + str(len(split_student_name_list)))
    if split_student_name_list is None or split_student_name_list == "" or split_student_name_list == []:
        return redirect('allclass_table')

    canvas = Canvas(response, pagesize = A4)    
    i=0;
    for every_sheet in split_student_name_list:
	i = i + 1;
	logger.info("Sheet: " + str(i))
	sheet = AttendanceSheet( student_names = every_sheet, \
			status_labels = ["Present", None, None, "Absent"], \
			#status_labels = ["Present", "Late", "Excused", "Absent"],\
			title = str(allclass.allclass_name + \
				" Class Page " + str(i) +"/"+ \
				str(len(split_student_name_list))))
	sheet.render_to_canvas(canvas)
	logger.info("Sheet Created")
    #sheet.make_canvas(response)
    canvas.save()
    logger.info("returning sheet..")
    return response



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
