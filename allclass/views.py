from django.shortcuts import render

from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, redirect, get_object_or_404 #Added 404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib import auth
from django.template import RequestContext

#Testing..
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
import glob #For file ^VS 130420141454

###################################
# Allclass CRUD

class AllclassForm(ModelForm):
    class Meta:
        model = Allclass
	fields = ('allclass_name','allclass_desc','allclass_location')


"""
@login_required(login_url='/login/')
def allclass_list(request, template_name='allclass/allclass_list.html'):
    allclasses = Allclass.objects.all()
    school_allclasses = []
    data = {}
    data['object_list'] = allclasses
    data['school_list'] = school_allclasses
    return render(request, template_name, data)
"""

@login_required(login_url='/login/')
def allclass_table(request, template_name='allclass/allclass_table.html'):
    allclasses = Allclass.objects.all()

    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid;
    allclasses = Allclass.objects.filter(school__in=School.objects.filter(organisation=organisation));

    school_allclasses = []
    for allclass in allclasses:
	school_name=allclass.school.school_name
        #school = School_Allclasses.objects.get(allclass_classid=allclass).school_schoolid
        school_allclasses.append(school_name)

    data = {}
    data['object_list'] = allclasses
    data['object_list'] = zip(allclasses, school_allclasses)
    data['school_list'] = school_allclasses
    allclasses_as_json = serializers.serialize('json', allclasses)
    allclasses_as_json =json.loads(allclasses_as_json)

    return render(request, template_name, {'data':data, 'allclasses_as_json':allclasses_as_json})
    #return render(request, template_name, data)


@login_required(login_url='/login/')
def allclass_create(request, template_name='allclass/allclass_create.html'):
    form = AllclassForm(request.POST or None)
    schools = School.objects.all()
    
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid;
    schools = School.objects.filter(organisation=organisation)

    teacher_role = Role.objects.get(pk=5)
    student_role = Role.objects.get(pk=6)
    
    teachers = User.objects.filter(pk__in=User_Roles.objects.filter(role_roleid=teacher_role).values_list('user_userid', flat=True))
    teachers = User.objects.filter(pk__in=User_Organisations.objects.filter(organisation_organisationid=organisation).values_list('user_userid', flat=True)).filter(pk__in=User_Roles.objects.filter(role_roleid=teacher_role).values_list('user_userid', flat=True))

    students = User.objects.filter(pk__in=User_Roles.objects.filter(role_roleid=student_role).values_list('user_userid', flat=True))
    students = User.objects.filter(pk__in=User_Organisations.objects.filter(organisation_organisationid=organisation).values_list('user_userid', flat=True)).filter(pk__in=User_Roles.objects.filter(role_roleid=student_role).values_list('user_userid', flat=True))

    courses = Course.objects.filter(success="YES",organisation=organisation)
    
    data = {}
    data['object_list'] = schools
    data['teacher_list'] = teachers
    data['student_list'] = students
    data['course_list'] = courses

    if request.method == 'POST':
        post = request.POST;
	print("checking..")
	class_name = post['class_name']
	allclass_count = Allclass.objects.filter(allclass_name=class_name).count()
    	if allclass_count == 0:
                print("Creating the Class..")
		class_name=post['class_name']
		class_desc=post['class_desc']
		class_location=post['class_location']
		#teacherid=post['teacherid']

		studentidspicklist=post.getlist('target')
		print("students selected from picklist:")
		print(studentidspicklist)

		courseidspicklist=post.getlist('target2')
		print("courses selected from picklist")
		print(courseidspicklist)
		
		
		try:
                        schoolid=post['schoolid']
			currentschool = School.objects.get(pk=schoolid)
                
                	allclass = Allclass(allclass_name=class_name, allclass_desc=class_desc, allclass_location=class_location,school=currentschool)
                	allclass.save()
                	school = School.objects.get(pk=schoolid)
                	print("Class School mapping success.")

                except:
                        print("No school given")
			allclass = Allclass(allclass_name=class_name, allclass_desc=class_desc, allclass_location=class_location)
                        allclass.save()


		print("Class Students mapping success.")

		#Create Class - StudentS mapping
		for everystudentid in studentidspicklist:
			print("Looping student:")
			print("////////////////////////////")
			print(User.objects.all())
			print("///////////////////////////")
			print(everystudentid)
			try:
				currentstudent=User.objects.get(pk=everystudentid)
				allclass.students.add(currentstudent)
				allclass.save()
			except:
				pass

		for everycourseid in courseidspicklist:
			print("Looping course:")
			print(everycourseid)
			try:
				currentcourse = Course.objects.get(pk=everycourseid)
				for everystudentid in studentidspicklist:
					currentstudent=User.objects.get(pk=everystudentid)
					currentcourse.students.add(currentstudent)
			except:
				pass
		
			#course.allclass.add(currentcourse)
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
                        #return redirect('allclass_table')
                if 'submittonew' in request.POST:
			statesuccess=1
                        data['statesuccess']=statesuccess
			return render(request, template_name, data)
                        #return redirect('allclass_new')
                else:
                        return redirect ('allclass_table')
        else:
		print("Class already exists")
                #Show message that the class name already exists in our database. (For the current organisation)
		state="The Class Name already exists.."
                data['state']=state
                return render(request, template_name, data)
                #return redirect('allclass_table')

    return render(request, template_name, data)

@login_required(login_url='/login/')
def allclass_update(request, pk, template_name='allclass/allclass_form.html'):
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid;
    allclass = get_object_or_404(Allclass, pk=pk)
    form = AllclassForm(request.POST or None, instance=allclass)

    #Assigned Student mapping
    student_role = Role.objects.get(pk=6)
    allstudents=User.objects.filter(pk__in=User_Roles.objects.filter(role_roleid=student_role).values_list('user_userid', flat=True))
    allstudents = User.objects.filter(pk__in=User_Organisations.objects.filter(organisation_organisationid=organisation).values_list('user_userid', flat=True)).filter(pk__in=User_Roles.objects.filter(role_roleid=student_role).values_list('user_userid', flat=True))

    assignedstudents=allclass.students.all();

    #Assigned Teachers mapping
    teacher_role = Role.objects.get(pk=5)
    allteachers = User.objects.filter(pk__in=User_Roles.objects.filter(role_roleid=teacher_role).values_list('user_userid', flat=True))
    allteachers = User.objects.filter(pk__in=User_Organisations.objects.filter(organisation_organisationid=organisation).values_list('user_userid', flat=True)).filter(pk__in=User_Roles.objects.filter(role_roleid=teacher_role).values_list('user_userid', flat=True))
    assignedteachers=allclass.teachers.all();

    allcourses=Course.objects.filter(organisation=organisation)
    assignedcourses=Course.objects.filter(allclasses__in =[allclass])


    allschools=School.objects.filter(organisation=organisation)
    assignedschool=allclass.school

    if form.is_valid():
        form.save()
	print("FORM IS VALID")
	print(request.POST.get('assignedteachers'))
	
	print("Going to update the assigned school..")
	schooliddropdown=request.POST.get('school')
	try:
		schooldropdown = School.objects.get(pk=schooliddropdown)
	except:
		pass
		schooldropdown=None
	allclass.school=schooldropdown

        print("Going to update the assigned students..")
        studentidspicklist=request.POST.getlist('target')
	print(studentidspicklist)
	if studentidspicklist:
        	allclass.students.clear()
        assignedclear = allclass.students.all();
        for everystudentid in studentidspicklist:
                currentstudent=User.objects.get(pk=everystudentid)
                allclass.students.add(currentstudent)
                allclass.save()

        print("Going to update the assigned teacher..")
        teacheridspicklist=request.POST.getlist('target2')
	print(teacheridspicklist)
	if teacheridspicklist:
        	allclass.teachers.clear()
        assignedclear = allclass.teachers.all();
        for everyteacherid in teacheridspicklist:
                currentteacher=User.objects.get(pk=everyteacherid)
                allclass.teachers.add(currentteacher)
                allclass.save()

	print("Going to update the assigned course")
	courseidspicklist=request.POST.getlist('target3')
	print(courseidspicklist)
	for everycourseid in courseidspicklist:
		print("everycourseid:")
		print(everycourseid)
		everycourse = Course.objects.get(pk=everycourseid)
		everycourse.allclasses.add(allclass)
		everycourse.save()
		print("added.")
		print("Course's classes:")
		print(everycourse.allclasses.all())
	
        return redirect('allclass_table')
    else:
	print("ALLCLASS UPDATE FORM IS NOT VALID")
	
    return render(request, template_name, {'form':form,'all_schools':allschools, 'assignedschool':assignedschool, 'all_courses':allcourses, 'assigned_courses':assignedcourses, 'all_students':allstudents,'assigned_students':assignedstudents, 'all_teachers':allteachers,'assigned_teachers':assignedteachers})

@login_required(login_url='/login/')
def allclass_delete(request, pk, template_name='allclass/allclass_confirm_delete.html'):
    allclass = get_object_or_404(Allclass, pk=pk)
    if request.method=='POST':
	#check if request.user is in the orgn and is not a student.
        allclass.delete()
        return redirect('allclass_table')
    return render(request, template_name, {'object':allclass})

"""
@login_required(login_url='/login/')
def allclass_exists(name):
    allclass_count = Allclass.objects.filter(allclass_name=name).count()
    if allclass_count == 0:
        return False
    return True
"""

# Create your views here.
