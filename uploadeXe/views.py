from django.shortcuts import render
# -*- coding: utf-8 -*-
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from django.shortcuts import render_to_response, redirect, get_object_or_404 #Added 404

import os 
#UMCloudDj.uploadeXe
#from uploadeXe.models import Document
from uploadeXe.models import Package as Document
from uploadeXe.forms import ExeUploadForm
from uploadeXe.models import Course

#Testing..
from django.forms import ModelForm
from organisation.models import Organisation
from organisation.models import UMCloud_Package
from organisation.models import User_Organisations
from school.models import School
from allclass.models import Allclass
from uploadeXe.models import Role
from uploadeXe.models import User_Roles
from django.contrib.auth.models import User
from django import forms


from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
import datetime
import time
import os
import urllib
import urllib2, base64, json
import hashlib
from django.conf import settings
import zipfile
from xml.dom import minidom

"""
def my_view(request):
	current_user = request.user.username
	print("Logged in username: " + current_user)
	return render_to_response(
        	'/base.html',
        	{'current_user': current_user, 'form': form},
        	context_instance=RequestContext(request)
	)
"""



######################################################################
#Package CRUD

class DocumentForm(ModelForm):
    class Meta:
        model = Document
	fields = ('name',)
	

@login_required(login_url='/login/')
def delete(request, pk, template_name='myapp/package_confirm_delete.html'):
    document = get_object_or_404(Document, pk=pk)
    if request.method=='POST':
        document.delete()
        return redirect('manage')
    return render(request, template_name, {'object':document})


@login_required(login_url='/login/')
def manage(request, template_name='myapp/manage.html'):
    documents = Document.objects.filter(publisher=request.user, success="YES")
    current_user = request.user.username
    courses_as_json = serializers.serialize('json', documents)
    courses_as_json = json.loads(courses_as_json)

    return render(request, template_name, {'courses_as_json':courses_as_json})

@login_required(login_url='/login/')
def edit(request, pk, template_name='myapp/update.html'):
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid;
    document = get_object_or_404(Document, pk=pk)
    form = DocumentForm(request.POST or None, instance=document)
    student_role = Role.objects.get(pk=6)
    allstudents=User.objects.filter(pk__in=User_Roles.objects.filter(role_roleid=student_role).values_list('user_userid', flat=True))

    alluserorg=User.objects.filter(pk__in=User_Organisations.objects.filter(organisation_organisationid=organisation).values_list('user_userid', flat=True))   
    assignedstudents=document.students.all();

    allcourses = Course.objects.filter(success="YES", organisation=organisation)

    assignedcourses=Course.objects.filter(packages=document)
    url=document.url;

    if form.is_valid():
	form.save()

	print("Going to update the assigned students..")
	studentidspicklist=request.POST.getlist('target')
	document.students.clear()
	assignedclear = document.students.all();
        for everystudentid in studentidspicklist:
                currentstudent=User.objects.get(pk=everystudentid)
                document.students.add(currentstudent)
                document.save()

  	print("Going to update course where the package should be present..")
	courseidspicklist=request.POST.getlist('target2')
	for everycourseid in courseidspicklist:
		everycourse = Course.objects.get(pk=everycourseid)
		everycourse.packages.add(document)
		everycourse.save()
	

	return redirect('manage')

    return render(request, template_name, {'form':form, 'url':url,'all_courses':allcourses, 'assigned_courses':assignedcourses,'all_students':allstudents,'assigned_students':assignedstudents})

@login_required(login_url='/login/')
def new(request, template_name='myapp/new.html'):
    # Handle file upload
    print("Current User logged in is: " + request.user.email)

    teacher_role = Role.objects.get(pk=5)
    student_role = Role.objects.get(pk=6)

    teachers = User.objects.filter(pk__in=User_Roles.objects.filter(role_roleid=teacher_role).values_list('user_userid', flat=True))

    students = User.objects.filter(pk__in=User_Roles.objects.filter(role_roleid=student_role).values_list('user_userid', flat=True))
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid;
    allcourses = Course.objects.filter(success="YES", organisation=organisation)

    data = {}
    data['teacher_list'] = teachers
    data['student_list'] = students
    data['all_courses'] = allcourses

    current_user = request.user.username
    # Render list page with the documents and the form
    return render_to_response(
        template_name,
        {'all_courses':data['all_courses'],'student_list':data['student_list'],'current_user': current_user},
        context_instance=RequestContext(request)
    )

"""
@login_required(login_url='/login/')
def elpparse(request, template_name='myapp/elpparse.html'):
    # Handle file upload
    print("YOU AREIN ELPPARSE")
    current_user = request.user.username
    if request.method == 'POST':
        post = request.POST;
        form = ExeUploadForm(request.POST, request.FILES)
        if form.is_valid():
	    elpfile = request.FILES['exefile']
	    print("ELP FILE:")
	    print(elpfile)
	    return redirect('elpparse')
    else:
        #Form isn't POST. 
        form = ExeUploadForm() # A empty, unbound form
	return render_to_response(
        template_name,
        {'form': form, 'current_user': current_user},
        context_instance=RequestContext(request)
    	)

    return redirect('elpparse')
"""

@login_required(login_url='/login/')
def list(request, template_name='myapp/list.html'):
    # Handle file upload
    print("Current User logged in is: " + request.user.email)

    teacher_role = Role.objects.get(pk=5)
    student_role = Role.objects.get(pk=6)

    teachers = User.objects.filter(pk__in=User_Roles.objects.filter(role_roleid=teacher_role).values_list('user_userid', flat=True))

    students = User.objects.filter(pk__in=User_Roles.objects.filter(role_roleid=student_role).values_list('user_userid', flat=True))

    data = {}
    data['teacher_list'] = teachers
    data['student_list'] = students

    if request.method == 'POST':
        post = request.POST;
        form = ExeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            newdoc = Document(exefile = request.FILES['exefile'])
            print("NEWDOC")
            teacher_role = Role.objects.get(pk=5)
            student_role = Role.objects.get(pk=6)
            teachers = User.objects.filter(pk__in=User_Roles.objects.filter(role_roleid=teacher_role).values_list('user_userid', flat=True))
            students = User.objects.filter(pk__in=User_Roles.objects.filter(role_roleid=student_role).values_list('user_userid', flat=True))
            data = {}
            data['teacher_list'] = teachers
            data['student_list'] = students
            studentidspicklist=post.getlist('target')
            print("students selected from picklist:")
            print(studentidspicklist)

            uid = str(getattr(newdoc, 'exefile'))
            print("File name to upload:")
            print(uid)
            appLocation = (os.path.dirname(os.path.realpath(__file__)))
            #Get the file and run eXe command 
            #Get url / path
            setattr (newdoc, 'url', 'bull')
            setattr (newdoc, 'publisher', request.user)
            newdoc.save()

            for everystudentid in studentidspicklist:
                print("Looping student:")
                print(everystudentid)
                currentstudent=User.objects.get(pk=everystudentid)
                newdoc.students.add(currentstudent)
                newdoc.save()

            os.system("echo Current location:")
            serverlocation=os.system("pwd")
            mainappstring = "/UMCloudDj/"
            uid = str(getattr(newdoc, 'exefile'))
            print("File saved as: ")
            print(uid)
            #elphash = hashlib.md5(open(serverlocation + mainappstring + settings.MEDIA_URL + uid).read()).hexdigest()
            #print("elp hash:")
            #print(elphash)

            print(settings.MEDIA_URL)
            unid = uid.split('.um.')[-2]
            unid = unid.split('/')[-1]  #Unique id here.
            print("Unique id:")
            print (unid)
            setattr(newdoc, 'uid', unid)
            
            elpfile=appLocation + '/../UMCloudDj/media/' + uid
            elpfilehandle = open(elpfile, 'rb')
            elpzipfile = zipfile.ZipFile(elpfilehandle)
            for name in elpzipfile.namelist():
                if name.find('contentv3.xml') != -1:
                    elpxmlfile=elpzipfile.open(name)
                    elpxmlfilecontents=elpxmlfile.read()
                    elpxml=minidom.parseString(elpxmlfilecontents)
                    dictionarylist=elpxml.getElementsByTagName('dictionary')
                    stringlist=elpxml.getElementsByTagName('string')
                    elpid="replacemewithxmldata"
                    setattr(newdoc, 'elpid', elpid)
                    #print(dictionarylist[0].attributes['string'].value)
                    
                    
            uidwe = uid.split('.um.')[-1]
            uidwe = uidwe.split('.elp')[-2]
            uidwe=uidwe.replace(" ", "_")
            
            rete=ustadmobile_export(uid, unid, uidwe)
            if rete:
                courseURL = '/media/eXeExport' + '/' + unid + '/' + uidwe + '/' + 'deviceframe.html'
                setattr(newdoc, 'url', "cow")
                newdoc.save()
                setattr(newdoc, 'success', "YES")
                setattr(newdoc, 'url', courseURL)
                setattr(newdoc, 'name', uidwe)
                setattr(newdoc, 'publisher', request.user)
                newdoc.save()
                
                """
                Adding package to course
                """
                print("Going to assign the package to the selected book")
                courseidspicklist=request.POST.getlist('target2')
                for everycourseid in courseidspicklist:
                    currentcourse = Course.objects.get(pk=everycourseid)
                    currentcourse.packages.add(newdoc)
                
		"""
                retg = grunt_course(unid, uidwe)
                
                if not retg:
                    setattr(newdoc, 'success', 'NO')
                    newdoc.save()
		"""

                newdoc.save()
		# Redirect to the document list after POST
		if 'submittotable' in request.POST:
			return HttpResponseRedirect(reverse('uploadeXe.views.list'))
                if 'submittonew' in request.POST:
			return HttpResponseRedirect(reverse('uploadeXe.views.new'))
                else:
			return HttpResponseRedirect(reverse('uploadeXe.views.list'))
                    
            else:
                setattr(newdoc, 'success', "NO")
                newdoc.save()
                # Redirect to the document list after POST
                return HttpResponseRedirect(reverse('uploadeXe.views.list'))
                
    else: 
	#Form isn't POST. 
        print("!!POST FORM IS INVALID!!")
        form = ExeUploadForm() # A empty, unbound form
        # Load documents for the list page
    documents = Document.objects.filter(publisher=request.user, success="YES")
    current_user = request.user.username
    # Render list page with the documents and the form
    return render_to_response(
        template_name,
        {'student_list':data['student_list'] ,'documents': documents, 'form': form, 'current_user': current_user},
        context_instance=RequestContext(request)
    )

def ustadmobile_export(uid, unid, uidwe):
    appLocation = (os.path.dirname(os.path.realpath(__file__)))
    #os.system('tree')
    print("Possible command: ")
    print('exe_do -s ustadMobileTestMode=True -x ustadmobile ' + "\"" +appLocation + '/../UMCloudDj/media/' + uid + "\"" + ' ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid )
    if os.system('exe_do -s ustadMobileTestMode=True -x ustadmobile ' +  "\"" + appLocation + '/../UMCloudDj/media/' + uid + "\"" + ' ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid ) == 0: # If command ran successfully,
        print("1. Exported success")
        print("Folder name: " + uidwe)
        if os.system('cp ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/ustadpkg_html5.xml ' + "\"" + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '_ustadpkg_html5.xml' + "\"" ) == 0: #ie if command got executed in success
            print("2. UstadMobile course exported successfully.")
            return True
        else:
            #Couldn't copy html file xml to main directoy. Something went wrong in the exe export
            print("!!Couldn't copy html file xml to main directoy. Something went wrong in the exe export!!")
            return False
        
    else:
        #Exe didn't run. exe_do : something went wrong in eXe.
        print("!!Exe didn't run. exe_do : something went wrong in eXe!!")
        return False
        
    
def grunt_course(unid, uidwe):
    appLocation= (os.path.dirname(os.path.realpath(__file__)))
    print("Starting grunt process..")
    os.system('mv ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/ustadmobile-settings.js ' +  appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/ustadmobile-settings.js.origi')
    os.system('cp ' + appLocation + '/../UMCloudDj/media/gruntConfig/Gruntfile.js ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/')
    os.system('cp ' + appLocation + '/../UMCloudDj/media/gruntConfig/package.json ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/')
    os.system('cp ' + appLocation + '/../UMCloudDj/media/gruntConfig/ustadmobile-settings.js ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/ustadmobile-settings.js' )
    os.system('cp ' + appLocation + '/../UMCloudDj/media/gruntConfig/umpassword.html ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/umpassword.html')
    os.system('cd ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/')
    print ('Trying this: ' + 'npm install grunt-contrib-qunit --save-dev -g --prefix ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/')
    os.system('npm install grunt-contrib-qunit --save-dev -g --prefix ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/')
    os.system('mv ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/lib/node_modules/ '+ appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/')
    print('Trying this: ' + 'grunt --base ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/ --gruntfile ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/Gruntfile.js')
    #Not running grunt until eXe changes are made - VarunaSingh 180220141732
    if os.system('grunt --base ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/ --gruntfile ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/Gruntfile.js'):
    	os.system('mv ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/ustadmobile-settings.js.origi ' +  appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/ustadmobile-settings.js')
        print("Grunt ran successfully. ")
        return True
    else:
    	#Grunt run failed. 
        print("!!Unable to run grunt. Test failed!!")
        os.system('mv ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/ustadmobile-settings.js.origi ' +  appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/ustadmobile-settings.js')
        return False
         
        #When testing is disabled ( Running until eXe changes are made - VarunaSingh 180220141732 - edit on 250220141323)
        #os.system('mv ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/ustadmobile-settings.js.origi ' +  appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/ustadmobile-settings.js') #Comment this when you have eXe changes, etc.

        #If you ever do an if condition for installing grunt on the local course..
        #else:
        #    print("Unable to install grunt for this course.. Fail.")
        #    os.system('mv ' + appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/ustadmobile-settings.js.origi ' +  appLocation + '/../UMCloudDj/media/eXeExport/' + unid + '/' + uidwe + '/ustadmobile-settings.js')



###################################################################################

##################################################################################
#Courses CRUD


class CourseForm(ModelForm):
    class Meta:
        model = Course
        fields = ('name', 'category','description')

"""
@login_required(login_url='/login/')
def course_list(request, template_name='myapp/course_list.html'):
    courses = Course.objects.all()
    packages_courses=[]
    data = {}
    data['object_list'] = courses
    data['package_list'] = packages_courses
    return render(request, template_name, data)
"""

@login_required(login_url='/login/')
def course_table(request, template_name='myapp/course_table.html'):
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid;
    courses = Course.objects.filter(success="YES", organisation=organisation)
    #courses = Course.objects.all()
    publisher_details=[]
    for course in courses:
	pub_details=course.publisher.username + "(" + course.organisation.organisation_name + ")"
	publisher_details.append(pub_details)
	
    data = {}
    data['object_list'] = courses
    data['object_list'] = zip(courses,publisher_details)

    courses_as_json = serializers.serialize('json',courses)
    courses_as_json = json.loads(courses_as_json)
    courses_as_json = zip(courses_as_json, publisher_details)

    return render(request, template_name, {'data':data, 'courses_as_json':courses_as_json})

@login_required(login_url='/login/')
def course_delete(request, pk, template_name='myapp/course_confirm_delete.html'):
    course = get_object_or_404(Course, pk=pk)
    if request.method=='POST':
        course.delete()
        return redirect('managecourses')
    return render(request, template_name, {'object':course})

@login_required(login_url="/login/")
def course_create(request, template_name='myapp/course_create.html'):
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid;
    form = CourseForm(request.POST or None)
    #packages = Document.objects.all()
    packages = Document.objects.filter(publisher=request.user, success="YES")
    packages = Document.objects.filter(success="YES", publisher__in=User.objects.filter(pk__in=User_Organisations.objects.filter(organisation_organisationid=organisation).values_list('user_userid', flat=True)))


    teacher_role = Role.objects.get(pk=5)
    student_role = Role.objects.get(pk=6)

    students = User.objects.filter(pk__in=User_Roles.objects.filter(role_roleid=student_role).values_list('user_userid', flat=True))

    students = User.objects.filter(pk__in=User_Organisations.objects.filter(organisation_organisationid=organisation).values_list('user_userid', flat=True)).filter(pk__in=User_Roles.objects.filter(role_roleid=student_role).values_list('user_userid', flat=True))

    #allclasses=Allclass.objects.all()
    allclasses = Allclass.objects.filter(school__in=School.objects.filter(organisation=organisation));

    data = {}
    data['package_list'] = packages
    data['student_list'] = students
    data['allclass_list'] = allclasses
    if request.method == 'POST':
        post = request.POST;
        print("checking..")
        course_name = post['course_name']
    	course_count = Course.objects.filter(name=course_name).count()
        if course_count == 0:
                print("Creating the Course..")
                course_name=post['course_name']
                course_desc=post['course_desc']
		course_category=post['course_category']
                packageidspicklist=post.getlist('target')
                print("packages selected from picklist:")
                print(packageidspicklist)
		studentidspicklist=post.getlist('target2')
		print("students selected from picklist:")
		print(studentidspicklist)
		allclassidspicklist=post.getlist('target3')
		print(allclassidspicklist)
		
		course_publisher = request.user
		course_organisation = User_Organisations.objects.get(user_userid=course_publisher).organisation_organisationid
		course = Course(name=course_name, category=course_category, description=course_desc, publisher=course_publisher, organisation=course_organisation)
		course.save()

                print("Mapping packages with course..")

		for everypackageid in packageidspicklist:
			print("Looping over packages..")
			print(everypackageid)
			currentpackage = Document.objects.get(pk=everypackageid)
			course.packages.add(currentpackage)
			course.save()

		print("Mapping students with course..")
		for everystudentid in studentidspicklist:
			print("Looping over students..")
			print(everystudentid)
			currentstudent=User.objects.get(pk=everystudentid)
			course.students.add(currentstudent)
			course.save()
 
   		print("Mapping allclasses with course..")
		for everyallclassid in allclassidspicklist:
			print("Looping over allclasses..")
			print(everyallclassid)
			currentallclass = Allclass.objects.get(pk=everyallclassid)
			course.allclasses.add(currentallclass)
			course.save()
			

		setattr(course, 'success','YES')
		course.save()
		print("All done for course creation.")
		data['state']="Course : " + course.name + " created successfully."
		if 'submittotable' in request.POST:
			
			return render(request, 'myapp/confirmation.html', data)
                        #return redirect('managecourses')
                if 'submittonew' in request.POST:
			statesuccess=1
			data['statesuccess']=statesuccess
			return render(request, template_name, data)
                	#return redirect('coursenew')
                else:
			data['state']="Something went wrong"
                        return redirect ('managecourses')

                return redirect('managecourses')
        else:
                print("Course already exists")
		data['state']="A course with that name already exists. Please specify another name"
		return render(request, template_name, data)
                #Show message that the class name already exists in our database. (For the current organisation)
                #return redirect('managecourses')

    return render(request, template_name, data)

@login_required(login_url='/login/')
def course_update(request, pk, template_name='myapp/course_form.html'):
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid;
    course = get_object_or_404(Course, pk=pk)
    form = CourseForm(request.POST or None, instance=course)

    #Assigned Packages mapping
    allpackages = Document.objects.all();
    allpackages = Document.objects.filter(publisher=request.user, success="YES")
    allpackages = Document.objects.filter(success="YES", publisher__in=User.objects.filter(pk__in=User_Organisations.objects.filter(organisation_organisationid=organisation).values_list('user_userid', flat=True)))
    assignedpackages = course.packages.all();

    student_role = Role.objects.get(pk=6)
    allstudents = User.objects.filter(pk__in=User_Roles.objects.filter(role_roleid=student_role).values_list('user_userid', flat=True))
    allstudents = User.objects.filter(pk__in=User_Organisations.objects.filter(organisation_organisationid=organisation).values_list('user_userid', flat=True)).filter(pk__in=User_Roles.objects.filter(role_roleid=student_role).values_list('user_userid', flat=True))
    assignedstudents = course.students.all()

    assignedallclasses = course.allclasses.all()
    allallclasses = Allclass.objects.filter(school__in=School.objects.filter(organisation=organisation));


    if form.is_valid():
        form.save()
        print("Going to update the assigned packages..")
        packagesidspicklist=request.POST.getlist('target')
        print(packagesidspicklist)
	#course.packages.clear()
        if packagesidspicklist:
		print("There is something selected for packages")
		course.packages.clear()
		assignedclear = course.packages.all();
		for everypackageid in packagesidspicklist:
			currentpackage = Document.objects.get(pk=everypackageid)
			course.packages.add(currentpackage)
			course.save()

	print("Going to update the assigned students..")
	studentidspicklist=request.POST.getlist('target2')
	print(studentidspicklist)
	course.students.clear()
	if studentidspicklist:
		print("There is something selected for students")
		course.students.clear()
	for everystudentid in studentidspicklist:
		currentstudent = User.objects.get(pk=everystudentid)
		course.students.add(currentstudent)
		course.save()

  	print("Going to update the assigned allclasses..")
	allclassidspicklist=request.POST.getlist('target3')
	print(allclassidspicklist)
	if allclassidspicklist is None:
		course.allclasses.clear()
	course.allclasses.clear()
	for everyallclassid in allclassidspicklist:
		currentallclass = Allclass.objects.get(pk=everyallclassid)
		course.allclasses.add(currentallclass)
		course.save()

        return redirect('managecourses')
    return render(request, template_name, {'form':form, 'all_students':allstudents, 'assigned_students':assignedstudents,'all_packages':allpackages,'assigned_packages':assignedpackages, 'all_allclasses':allallclasses, 'assigned_allclasses':assignedallclasses})





# Create your views here.
