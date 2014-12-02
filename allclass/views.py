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

###################################
# Allclass CRUD

"""
Model Form for Allclass that shows only Name, Desc and Location
"""
class AllclassForm(ModelForm):
    class Meta:
        model = Allclass
	fields = ('allclass_name','allclass_desc','allclass_location')

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
    
    data = {}
    data['object_list'] = schools
    data['teacher_list'] = teachers
    data['student_list'] = students
    data['course_list'] = courses

    if request.method == 'POST':
        post = request.POST;
	class_name = post['class_name']
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
				allclass.students.add(currentstudent)
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

    assignedstudents=allclass.students.all();

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


    allschools=School.objects.filter(organisation=organisation)
    assignedschool=allclass.school

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
        	allclass.students.clear()
        assignedclear = allclass.students.all();
        for everystudentid in studentidspicklist:
                currentstudent=User.objects.get(\
					pk=everystudentid)
                allclass.students.add(currentstudent)
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
	for everycourseid in courseidspicklist:
		everycourse = Course.objects.get(\
					pk=everycourseid)
		everycourse.allclasses.add(allclass)
		everycourse.save()
	
        return redirect('allclass_table')
    else:
	print("ALLCLASS UPDATE FORM IS NOT VALID")
	
    return render(request, template_name, \
		{'form':form,'all_schools':allschools, \
			'assignedschool':assignedschool, \
			'all_courses':allcourses, \
			'assigned_courses':assignedcourses, \
			'all_students':allstudents,\
			'assigned_students':assignedstudents,\
			'all_teachers':allteachers,\
			'assigned_teachers':assignedteachers\
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

# Create your views here.
