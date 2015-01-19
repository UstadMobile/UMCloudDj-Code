from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect, get_object_or_404 

import os 
from uploadeXe.models import Package as Document
from uploadeXe.forms import ExeUploadForm
from uploadeXe.models import Course
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
from lxml import etree
import xml.etree.ElementTree as ET
import commands #Added for obtaining the elp hash
import sys
from subprocess import call


######################################################################
#Package CRUD

"""
Document is Package which is a Block. This is the form for the block. 
"""
class DocumentForm(ModelForm):
    class Meta:
        model = Document
	fields = ('name',)
	
"""
The view to render delete a particular block. 
"""
@login_required(login_url='/login/')
def delete(request, pk, template_name='myapp/package_confirm_delete.html'):
    document = get_object_or_404(Document, pk=pk)
    if request.method=='POST':
	if request.user == document.publisher:
            document.delete()
	else:
	    print("Only the publisher can delete the block")
	    return redirect('manage')
        return redirect('manage')
    return render(request, template_name, {'object':document})

"""
Manages Blocks and reders to template rendering to primeui table
"""
@login_required(login_url='/login/')
def manage(request, template_name='myapp/manage.html'):
    documents = Document.objects.filter(publisher=request.user,\
					 success="YES")
    current_user = request.user.username
    courses_as_json = serializers.serialize('json', documents)
    courses_as_json = json.loads(courses_as_json)

    return render(request, template_name, {'courses_as_json':\
					    courses_as_json})
"""
View to make edits to Blocks as oer Block model form.
Assigned students are also rendered and given to the
template for assignation and edits that are caught in
this view via POST parameters
"""
@login_required(login_url='/login/')
def edit(request, pk, template_name='myapp/update.html'):
    organisation = User_Organisations.objects.get(user_userid=request.user).\
						organisation_organisationid;
    document = get_object_or_404(Document, pk=pk)
    form = DocumentForm(request.POST or None, instance=document)
    student_role = Role.objects.get(pk=6)
    allstudents=User.objects.filter(pk__in=User_Roles.objects.filter(\
				role_roleid=student_role).\
				values_list('user_userid', flat=True))

    alluserorg=User.objects.filter(pk__in=User_Organisations.objects.filter(\
				organisation_organisationid=organisation).\
				values_list('user_userid', flat=True))   
    assignedstudents=document.students.all();

    allcourses = Course.objects.filter(success="YES", organisation=\
							organisation)

    assignedcourses=Course.objects.filter(packages=document)
    url=document.url;

    if form.is_valid():
	form.save()

	#("Going to update the assigned students..")
	studentidspicklist=request.POST.getlist('target')
	document.students.clear()
	assignedclear = document.students.all();
        for everystudentid in studentidspicklist:
                currentstudent=User.objects.get(pk=everystudentid)
                document.students.add(currentstudent)
                document.save()

  	#print("Going to update course where the package \
	#	should be present..")
	courseidspicklist=request.POST.getlist('target2')
	for everycourseid in courseidspicklist:
		everycourse = Course.objects.get(pk=everycourseid)
		everycourse.packages.add(document)
		everycourse.save()
	

	return redirect('manage')

    return render(request, template_name, {'form':form, \
			'url':url,'all_courses':allcourses, \
			'assigned_courses':assignedcourses,\
			'all_students':allstudents,\
			'assigned_students':assignedstudents})

""" View to add a new elp file and upload it after assigning
 it to a course.
"""
@login_required(login_url='/login/')
def new(request, template_name='myapp/new.html'):
    # Handle file upload
    teacher_role = Role.objects.get(pk=5)
    student_role = Role.objects.get(pk=6)

    teachers = User.objects.filter(pk__in=User_Roles.objects.\
	filter(role_roleid=teacher_role).values_list(\
				'user_userid', flat=True))

    students = User.objects.filter(pk__in=User_Roles.objects.\
	filter(role_roleid=student_role).values_list(\
				'user_userid', flat=True))
    organisation = User_Organisations.objects.get(\
				user_userid=request.user\
				).organisation_organisationid;
    allcourses = Course.objects.filter(success="YES", \
				organisation=organisation)

    data = {}
    data['teacher_list'] = teachers
    data['student_list'] = students
    data['all_courses'] = allcourses

    current_user = request.user.username
    # Render list page with the documents and the form
    return render_to_response(
        template_name,
        {'all_courses':data['all_courses'],\
	'student_list':data['student_list'],\
	'current_user': current_user},
        context_instance=RequestContext(request)
    )

"""Common function to get block if and name from epub
   file
"""
def get_epub_blockid_name(epubpath):
    print("Starting..")
    try:
        epubfilehandle = open(epubpath, 'rb')
        epubasazip = zipfile.ZipFile(epubfilehandle)
    except:
        print("!!Could Not open epub file")
        state="Unable to upload. Unable to retrieve epub file"
        return None, None, state

    #try:
    if True:
	foundFlag = False
        data={}
        for name in epubasazip.namelist():
            #As per EPUB standard, META-INF/container.xml (the
            #container file) must be present and includes the 
            #directory of assets and package file.
            if name.find('META-INF/container.xml') != -1:
                foundFlag=True
                #Container File: cf
                cf=epubasazip.open(name)
                cfc=cf.read() #Container file contents
                root=ET.fromstring(cfc)
                packagepage=None
                for child in root:
                    for chi in child:
                        if "package.opf" in chi.attrib['full-path']:
                            packagepath=chi.attrib['full-path']
                            break #We got the package file..
                packageFound=False
                if packagepath != None:
                    epubassetfolder=packagepath.rsplit('/',1)[0]
                    #package File: pf
                    try:
                        pf=epubasazip.open(packagepath)
                    except:
                        packageFound=False
                    else:
                        packageFound=True
                        pfc=pf.read()
                        pfcroot=ET.fromstring(pfc)
                        title=None
                        identifier=None
                        for child in pfcroot:
                            for chi in child:
                                if "}title" in chi.tag:
                                    title=chi.text
                                if "}identifier" in chi.tag:
                                    identifier=chi.text

                        if title != None and identifier != None:
                            elplomid=identifier
                            elpiname=title
			    #Get TinCan Prefix:
                            tincanprefix=get_prefix_from_tincanxml(epubpath)
                            return elplomid, elpiname, tincanprefix

                        else:
                            elpiname=None
                            elplomid=None
                            print("!!ERROR in getting title and BlockID!!")
                            elpid="replacemewithxmldata"
                            state="Upload Failed. A valid title and ID was not found"
                            data['state']=state
                            data['statesuccess']=0
                            return None, None, state

                if packageFound == False:
                        print("!!ERROR in getting package file from EPUB!!")
                        state="Failed to upload block. No package file as per container xml."
                        statesuccess=0
                        data['state']=state
                        data['statesuccess']=statesuccess
                        return None, None, state

        if foundFlag==False:
            print("!!Unable to find the container xml file in epub!!")
            state="Failed to upload block. Not a valid epub (no container xml)"
            statesuccess=0
            data['state']=state
            data['statesuccess']=statesuccess
            return None, None, state
    #except:
    else:
        state="Something went wrong in file upload. Contact us."
        epubfilehandle.close();
        return None, None, state
    epubfilehandle.close();
    return None, None, "Something went wrong in the upload. Please contact us."

"""Common function: To figure out what the prefix is from the tincan.xml file.
   this tincan.xml file is generated as per export in epub.
"""
def get_prefix_from_tincanxml(epubpath):
    try:
        epubfilehandler = open(epubpath, 'rb')
        epubasazip = zipfile.ZipFile(epubfilehandler)
    except:
	print("!!Unable to open epub file for tincan xml extraction")
	return None
    #try:
    if True:
        foundPrefix = False
        foundTinCanFile = False
        for eachfile in epubasazip.namelist():
	    if eachfile.find('tincan.xml') != -1:
	        foundTinCanFile = True
	        tincanxmlfile = epubasazip.open(eachfile)
	        tincanxmlfilecontents = tincanxmlfile.read()
	        root = ET.fromstring(tincanxmlfilecontents)
	        for tincanelement in root:
		    for activitieselement in tincanelement:
			    try:
			        activityid = activitieselement.attrib['id']
			    except:
			        print("Could not get activity id from tincan.xml")
				epubfilehandler.close()
			        return None
   			    else:
			        if activityid != "" and activityid != None:
				    tincanprefix = activityid.rsplit('/',1)[0]
			            if tincanprefix != "":
				        epubfilehandler.close()
					print("Found prefix!")
				        return tincanprefix
				    else:
				        epubfilehandler.close()
				        return None
			        else:
				    epubfilehandler.close()
				    return None
	if foundPrefix == False or foundTinCanFile == False:
	    return None
    #except:
    else:
	print("!!Something went wrong in epub tincanxml extraction!!")
        epubfilehandler.close()
    epubfilehandler.close()
    return None
				 

    

"""View and method to handle block/elp file uploads.
"""
@login_required(login_url='/login/')
def list(request, template_name='myapp/list.html'):
    # Handle file upload

    state=""

    teacher_role = Role.objects.get(pk=5)
    student_role = Role.objects.get(pk=6)

    teachers = User.objects.filter(pk__in=User_Roles.objects.\
		filter(role_roleid=teacher_role).\
		values_list('user_userid', flat=True))

    students = User.objects.filter(pk__in=User_Roles.objects.\
		filter(role_roleid=student_role).\
		values_list('user_userid', flat=True))

    data = {}
    data['teacher_list'] = teachers
    data['student_list'] = students

    form = ExeUploadForm() # A empty, unbound form
    documents = Document.objects.filter(\
                 publisher=request.user, success="YES", active=True)
    current_user = request.user.username
    data['documents']=documents
    data['form']=form
    data['current_user']=current_user

    if request.method == 'POST':
	elpiname=None
	elplomid = None
	print("Handling Block file upload..")
	#If method is POST, a new elp file is being
	#uploaded
        post = request.POST;
        form = ExeUploadForm(request.POST, request.FILES)
	forceNew     = request.POST.get('forceNew')
	#noAutoassign = request.POST.get('noAutoassign')
        if form.is_valid():
          #For Every file uploaded
	  for exefile in request.FILES.getlist('exefile'):
	    newdoc = Document(exefile=exefile)
            print("NEW Block file being uploaded by: " + \
				request.user.username)
            teacher_role = Role.objects.get(pk=5)
            student_role = Role.objects.get(pk=6)
            teachers = User.objects.filter(pk__in=User_Roles.\
			objects.filter(role_roleid=teacher_role).\
			values_list('user_userid', flat=True))
            students = User.objects.filter(pk__in=User_Roles.objects.\
			filter(role_roleid=student_role).values_list(\
					'user_userid', flat=True))
            data['teacher_list'] = teachers
            data['student_list'] = students
            studentidspicklist=post.getlist('target')

            uid = str(getattr(newdoc, 'exefile'))
            appLocation = (os.path.dirname(os.path.realpath(__file__)))
            setattr (newdoc, 'url', 'bull')
            setattr (newdoc, 'publisher', request.user)
	    setattr (newdoc, 'elphash','-')
	    setattr (newdoc, 'tincanid', '-')
            newdoc.save()

            for everystudentid in studentidspicklist:
                #("Looping student:")
                currentstudent=User.objects.get(pk=everystudentid)
                newdoc.students.add(currentstudent)
                newdoc.save()

            #Getting elp md5sum
	    status, serverlocation = commands.getstatusoutput("pwd")
	    serverlocation=appLocation+'/../'
            mainappstring = "/UMCloudDj/"
            uid = str(getattr(newdoc, 'exefile'))
            elphash = hashlib.md5(open(serverlocation + mainappstring \
			+ settings.MEDIA_URL + uid).read()).hexdigest()	
	    hashlist=Document.objects.all().values_list('elphash')
	    if str(elphash) in hashlist:
		print("ELP/EPUB already uploaded. Do we want to upload it again?")
		#Put action here for future logic for existing files.
	    setattr(newdoc, 'elphash', elphash)

	    #Unique Upload ID.
            unid = uid.split('.um.')[-2]
            unid = unid.split('/')[-1]  #Unique id here.
            setattr(newdoc, 'uid', unid)
            
            #EPUB/ELP is technically a ZIP file.
            elpfile=appLocation + '/../UMCloudDj/media/' + uid
            elpfilehandle = open(elpfile, 'rb')
            elpzipfile = zipfile.ZipFile(elpfilehandle)

            #If it is an epub file:
            if uid.lower().endswith('.epub'):
		print("An EPUB File has been uploaded.." + uid)
		elplomid, elpiname, tincanprefix = get_epub_blockid_name(elpfile)
		if elplomid == None and elpiname == None :
		    setattr(newdoc, 'success', 'NO')
		    setattr(newdoc, 'tincanid', '-')
		    newdoc.save()
		    state= tincanprefix
		    statesuccess=0
		    data['state']=state
		    data['statesuccess']=statesuccess
		    return render(request, template_name, data)
		else:
		    setattr(newdoc, 'elpid', elplomid)
		    setattr(newdoc, 'name', elpiname)
		    if tincanprefix == None:
			tincanprefix = "/"
		    setattr(newdoc, 'tincanid', tincanprefix)
		    newdoc.save()

            #If it is an elp file:
            elif uid.lower().endswith('.elp'):
            	print("An eXe ELP file has been uploaded..")
            	foundFlag=False
            	for name in elpzipfile.namelist():
                    if name.find('contentv3.xml') != -1:
                    	foundFlag=True
                        elpxmlfile=elpzipfile.open(name)
                        elpxmlfilecontents=elpxmlfile.read()
                        #Using minidom
                        elpxml=minidom.parseString(elpxmlfilecontents)

                        #using ET
                        root = ET.fromstring(elpxmlfilecontents)
                        for child in root:
                            foundFlag2=False
                            for chi in child:
                                if foundFlag2 == True:
                                    tincanprefix=chi.attrib['value']
                                if "}string" in chi.tag:
                                    if "xapi_prefix" in chi.attrib['value']:
                                        foundFlag2=True
                        try:
                            if not tincanprefix:
                                tincanprefix="-"
                        except:
                            tincanprefix=""
                        setattr(newdoc, 'tincanid', tincanprefix)
                        try:
                            dictionarylist=elpxml.getElementsByTagName('dictionary')
                            stringlist=elpxml.getElementsByTagName('instance')
                            lomemtry=None
                            for x in stringlist:
                                if x.getAttribute('class') == "exe.engine.lom.lomsubs.entrySub":
                                    lomentry=x
                                    break
                            elplomidobject=lomentry.getElementsByTagName('unicode')
                            elplomid=None
                            for e in elplomidobject:
                                elplomid=e.getAttribute('value')
                            setattr(newdoc, 'elpid', elplomid)
                            if not elplomid:
                                setattr(newdoc, 'elpid', "replacemewithxmldata")
                        except:
                            setattr(newdoc, 'elpid', '-')
                            elpid="replacemewithxmldata"
                            setattr(newdoc, 'elpid', elpid)

                        root = ET.fromstring(elpxmlfilecontents)
                        for child in root:
                            elpfoundFlag=False
                            for chi in child:
                                if elpfoundFlag == True:
                                    elpiname=chi.attrib['value']
                                    break
                                if "}string" in chi.tag:
                                    if "_name" in chi.attrib['value']:
                                        elpfoundFlag=True
                        if not elpiname:
                            elpiname="-"
            	if foundFlag==False:
            	    print("!!Unable to find the container xml file in elp!!")
            	    setattr(newdoc, 'success', 'NO')
		    newdoc.save()
		    #return HttpResponseRedirect(reverse(\
                    #            'uploadeXe.views.list'))

            else:
            	print("!!Unable to determine what file you have upload (elp/epub)!!")	
		setattr(newdoc, 'success', 'NO')
		newdoc.save()
		state="Unable to determine the file type. File is not a .epub or .elp file"
		statesuccess=0
		data['state']=state
		data['statesuccess']=statesuccess
		return render(request, template_name, data)

	    if elpiname == None:
		blockname="-"
	    else:
		blockname=elpiname
	    if elplomid == None:
		blockid="-"
	    else:
		blockid=elplomid
	    print(uid + "|" + unid + "|" + str(blockname) + "|" + str(blockid) + "|")
	    rete, elpepubid = ustadmobile_export(uid, unid, elpiname, elplomid, forceNew)
	 	
            if rete =="newsuccess":
		print("True, this block will be newly created.")
                courseURL = '/media/eXeExport' + '/' + unid + '/' + elpiname + '/' + 'deviceframe.html'
                setattr(newdoc, 'success', "YES")
                setattr(newdoc, 'url', courseURL)
                setattr(newdoc, 'name', elpiname)
                setattr(newdoc, 'publisher', request.user)
                newdoc.save()
		state="Your Block: " + newdoc.name + "  has been uploaded."
		statesuccess=1
		data['state']=state
		data['statesuccess']=statesuccess
		if newdoc.elpid=='replacemewithxmldata':
		    if elpepubid != None:
			setattr(newdoc, 'elpid', elpepubid)
			newdoc.save()
		    else:
		        newdoc.success="NO"
			state="Couldn't get block's Unique ID. Please check."
		        newdoc.save()
			print("!!No Block ID got from Block file uploaded!!")
			data['state']=state
            		data['statesuccess']=0
            		return render(request, template_name, data)
			#return message
                
                """
                Adding package to course
                """
                #("Going to assign the package to the selected book")
                courseidspicklist=request.POST.getlist('target2')
                for everycourseid in courseidspicklist:
                    currentcourse = Course.objects.get(pk=everycourseid)
                    currentcourse.packages.add(newdoc)
                
		"""#Commented and put on hold
		##Code for grunt testing course against webkit
                retg = grunt_course(unid, uidwe)
                
                if not retg:
                    setattr(newdoc, 'success', 'NO')
                    newdoc.save()
		"""
		#just to be sure..
                newdoc.save()

	    elif rete=="newfail":
		state="Failed to upload block. Something is wrong with the file. Please contact us."
		statesuccess=0
		data['state']=state
		data['statesuccess']=statesuccess
	 	print("Failed to create and start process for new course and export")

	    elif rete=="newfailcopy":
		state="Failed to upload the new block. Failed to verify export process. Please contact us."
                statesuccess=0
                data['state']=state
                data['statesuccess']=statesuccess
		print("Exported but Failed to verify the export process")

	    elif rete=="updatefail":
		state="Failed to update block. Failed to start export process. Please contact us."
                statesuccess=0
                data['state']=state
                data['statesuccess']=statesuccess
		print("Failed to start export process.")

	    elif rete=="updatefailcopy":
		state="Failed to update block. Failed to verify export. Please contact us."
                statesuccess=0
                data['state']=state
                data['statesuccess']=statesuccess
		print("Failed to verify export. Exported however.")
                    
            elif rete=="updatesuccess":
		state="This block: " + newdoc.name + " has been updated."
                statesuccess=1
                data['state']=state
                data['statesuccess']=statesuccess
		print("This block is going to be an update and has been updated.")
                setattr(newdoc, 'success', "NO")
		setattr(newdoc, 'active', False)
                newdoc.save()
		newdoc.delete()
                # Redirect to the document list after POST
                return HttpResponseRedirect(reverse(\
					'uploadeXe.views.list'))
	  if 'submittotable' in request.POST:
	    data['state']=state
            return render(request, template_name, data)
            #return HttpResponseRedirect(reverse('uploadeXe.views.list'))
          if 'submittonew' in request.POST:
	    data['state']=state
	    return render(request, 'myapp/new.html', data)
          else:
	    data['state']=state
            return render(request, template_name, data)
	else:
	    print("Form is not valid")
                
    else: 
	#Form isn't POST. 
        print("!!NOT A POST REQUEST!!")
        form = ExeUploadForm() # A empty, unbound form
    documents = Document.objects.filter(\
			publisher=request.user, success="YES", active=True)
    current_user = request.user.username
    # Render list page with the documents and the form
    return render_to_response(
        template_name,
        {'student_list':data['student_list'] ,\
	'documents': documents, 'form': form,\
	 'current_user': current_user},
        context_instance=RequestContext(request)
    )


"""
Common function to export an elp file and depending on the success, 
return options
eXeUpload/fe714086-e886-40c0-b472-3bf29db5211d.um.test.elp|fe714086-e886-40c0-b472-3bf29db5211d|lul-boys|4a711fd1-3c80-4c75-b55c-cb77e4b4a070|
uid/uurl: Uploaded Url : Uploaded File's url (elp/epub file)
unid Unique ID of the uploaded file.
uidwe/name: Name of the block (folder) as per uploaded file.
elplomid: block id of the creation in eXe. 

newsuccess for block is newly created and successfully expoorted.
newfail for blocks to be newly created but export process failed.
newfailcopy : elp exported but failed to verify the export process.
updatefail: Failed to start export process for updating a block(elp)
updatefailcopy: elp updated and exported but failed to verify the update
updatesuccess: elp file updated and exported successfully. All good.
"""
def ustadmobile_export(uurl, unid, name, elplomid, forceNew):
    appLocation = (os.path.dirname(os.path.realpath(__file__)))
    print("Checking block id..")
    found=Document.objects.filter(elpid=elplomid, success="YES", active=True)
    elplomid=None
    if found and not forceNew:
        print("Block ID already exists in the system." + \
        	"This export is going to be an update.")
        #To get the folder of previous export:
        folder_url=found[0].url.rsplit('/',2)[0]
	
	print("Moving previous export. Command is:")
	print('mv ' + appLocation + '/../UMCloudDj' +\
                    folder_url + ' ' + appLocation + '/../UMCloudDj' +\
                        folder_url + '_old')
        if os.system('mv ' + appLocation + '/../UMCloudDj' +\
           	    folder_url + ' ' + appLocation + '/../UMCloudDj' +\
			folder_url + '_old'):
	    print("moved successfuilly to: " + appLocation + '/../UMCloudDj' +\
			folder_url+'_old')
	else:
	    print("Error in moving " + appLocation + '/../UMCloudDj' +\
                    folder_url + " to " + appLocation + '/../UMCloudDj' +\
                        folder_url + '_old')

	if 'test' in sys.argv:
	    print("Unit Testing in Block Update ")
	    exe_do_command = appLocation + '/../exelearning-ustadmobile-work/exe/exe_do --standalone'

	else:
	    exe_do_command = appLocation + '/../exelearning-ustadmobile-work/exe/exe_do --standalone'

	print("Starting the export..")
	print("Possible command: " + exe_do_command + ' -x ustadmobile ' +\
                "\"" + appLocation + '/../UMCloudDj/media/' + uurl + "\"" + \
                        ' ' + appLocation + '/../UMCloudDj' +\
                                folder_url+'' )
        if os.system(exe_do_command + ' -x ustadmobile ' +\
               	"\"" + appLocation + '/../UMCloudDj/media/' + uurl + "\"" + \
                	' ' + appLocation + '/../UMCloudDj' +\
                         	folder_url+'' ) == 0: # If command ran successfully,
     	    print("1. Exported success")
            #("Folder name: " + name)
            if os.system('cp ' + appLocation + '/../UMCloudDj'\
                     + folder_url + '/' + name + '/ustadpkg_html5.xml ' +\
                         "\"" + appLocation + '/../UMCloudDj'\
                             + folder_url + '/' + name + '_ustadpkg_html5.xml' +\
                                 "\"" ) == 0: #ie if command got executed in success
		print("2. UstadMobile course exported successfully.")
		#("a success, trying to update date and stuff")
                found[0].upd_date=datetime.datetime.now()
                found[0].save()

		if os.system('rm -rf ' + appLocation + '/../UMCloudDj'+\
			folder_url + '_old'):
		    print("old folder deleted")
	 	else:
		    print("Unable to delete old folder")
		return "updatesuccess", None

		"""
	        if os.system('rm -rf ' + appLocation + '/../UMCloudDj'\
			 +url + '_old'):
		    print("a success, trying to update date and stuff")
		    print(found[0].id)
		    found[0].upd_date=datetime.now()

		    print(datetime.now())
		    print(found[0].upd_date)
  	  	    found[0].save()
               	    return True
		else:
		    print("Could not remove temp export folder for update")
		"""
	    
            else:
               	#Couldn't copy html file xml to main directoy. 
               	#Something went wrong in the exe export
               	print("!!Couldn't copy html file xml to main directoy. \
                      Something went wrong in the exe export!!")
		return "updatefailcopy", None
	else:
	    print("YOU SHOULDNT EVEN BE SEEING THIS..:")
	    return "updatefail", None

    else:
	print("This export is going to be a new block or ForceNew selected")
	none="none"

	if 'test' in sys.argv:
	    print("NEW UPDATE 3: YOU ARE TESTING: ")
	    exe_do_command = appLocation + '/../exelearning-ustadmobile-work/exe/exe_do --standalone'

        else:
            exe_do_command = appLocation + '/../exelearning-ustadmobile-work/exe/exe_do --standalone'

        #1. Check if it is an .elp file or .epub file that is being uploaded. 
        #2. Export to epub
        #3. Unzip it, get details

        if uurl.lower().endswith('.epub'):
            print("Going to export an EPUB file..")
            #epub file is: \"" + appLocation + '/../UMCloudDj/media/' + uurl + "\"" 
	    print("Possible command:")
	    print('unzip -q ' + "\"" + appLocation + '/../UMCloudDj/media/' + uurl + "\"" + " -d " +\
                "\"" + appLocation + '/../UMCloudDj/media/eXeExport/' +\
                          unid + "/" + "\"")
	    """
	    if os.system(exe_do_command + ' -x ustadmobile '+ "\"" + appLocation + '/../UMCloudDj/media/' + uurl + "\"" +\
		' ' + "\"" + appLocation + '/../UMCloudDj/media/' + uurl + ".new\"") == 0:
		
		print("0. Epub re exported.")
	    else:
		print("!!Unable to re export epub file!!")
		return "newfail", None
	    """
	
            if os.system('unzip -q ' + "\"" + appLocation + '/../UMCloudDj/media/' + uurl + "\"" + " -d " +\
            	"\"" + appLocation + '/../UMCloudDj/media/eXeExport/' +\
			 unid + "/" + "\"") == 0:

		try:
		    epubfile=appLocation + '/../UMCloudDj/media/' + uurl
                    epubfilehandle = open(epubfile, 'rb')
                    epubzipfile = zipfile.ZipFile(epubfilehandle)
                except:
                    print("!!Unable to open the epub file for getting block info!!")
                    return "newfail", None

		foundFlag=False
                for filename in epubzipfile.namelist():
                    #As per EPUB standard, META-INF/container.xml (the
                    #container file) must be present and includes the 
                    #directory of assets and package file.
                    if filename.find('META-INF/container.xml') != -1:
                        foundFlag=True
                        print("found cf")
                        #Container File: cf
                        cf=epubzipfile.open(filename)
                        cfc=cf.read() #Container file contents
                        root=ET.fromstring(cfc)
                        packagepage=None
                        for child in root:
                            for chi in child:
                                if "package.opf" in chi.attrib['full-path']:
                                    packagepath=chi.attrib['full-path']
                                    break #We got the package file..

                print("1. Exported to folder.")
                #Get Folder name  from : META-INF/container.xml

		if packagepath != None:
                    epubassetfolder=packagepath.rsplit('/',1)[0]
		else:
		  return "newfail", None
            	if (os.system('mv ' + "\"" + appLocation + '/../UMCloudDj/media/eXeExport/' +\
	    	    unid+"/"+epubassetfolder+"\"" + " " + appLocation+'/../UMCloudDj/media/eXeExport/'+\
	    	    	    unid + "/" + name)) == 0:
            	    print("2. Unzipped and verified.")
            	    if os.system('cp ' + appLocation + '/../UMCloudDj/media/eXeExport/'\
			    + unid + '/' + name + '/ustadpkg_html5.xml ' +\
			 	"\"" + appLocation + '/../UMCloudDj/media/eXeExport/'\
			 	    + unid + '/' + name + '_ustadpkg_html5.xml' +\
			 		"\"" ) == 0: #ie if command got executed in success
	    	    	print("3. Export process completed.")
	    	    	return "newsuccess", None
	    	    else:
	    	    	print("!!Couldn't copy html file xml to main directoy."+\
			    "Something went wrong in the exe export!!")
			return "newfailcopy", None
		else:
		    print("!!Couldn't rename EPUB folder to Block name!!")
		    return "newfailcopy", None
	    else:
	    	print("!!EPUB failed to extract.!!")
	    	return "newfail", None

	elif uurl.lower().endswith('.elp'):
	    print("Going to export an eXe ELP file..")
	    if os.system('mkdir ' + appLocation + '/../UMCloudDj/media/eXeExport/' +\
                         unid + "/") == 0:
		print("Directory prepared..")
	    else:
		print("!!Couldn't mkdir (make directory) for export!!")
                return "newfail", None
	    if name == None:
	  	name=""
	    print("Possible command : " + exe_do_command + ' -x ustadmobile ' +\
                "\"" + appLocation + '/../UMCloudDj/media/' + uurl + "\"" + \
                    ' ' + "\"" + appLocation + '/../UMCloudDj/media/eXeExport/' +\
                         unid + "/" + name + ".epub" + "\"" ) 
	    if call([appLocation + "/../exelearning-ustadmobile-work/exe/exe_do",\
		"--standalone", "-x","ustadmobile", \
		    appLocation + "/../UMCloudDj/media/" + uurl, \
			appLocation + "/../UMCloudDj/media/eXeExport/"+unid + "/" + name + ".epub"],\
			    shell=False) == 0:
	        """
	        if os.system(exe_do_command + ' -x ustadmobile ' +\
	  	"\"" + appLocation + '/../UMCloudDj/media/' + uurl + "\"" + \
		    ' ' + "\"" + appLocation + '/../UMCloudDj/media/eXeExport/' +\
			 unid + "/" + name + ".epub" + "\"" ) == 0: # If command ran successfully,
		"""
	    	print("1. Exported to epub")
		#Get the elpid:
		

		try:
		    epubfile=appLocation + '/../UMCloudDj/media/eXeExport/' +\
                         unid + "/" + name + ".epub"
                    epubfilehandle = open(epubfile, 'rb')
                    epubzipfile = zipfile.ZipFile(epubfilehandle)
		except:
		    print("!!Unable to open the epub file for getting block info!!")
		    return "newfail", None

		foundFlag=False
                for filename in epubzipfile.namelist():
                    #As per EPUB standard, META-INF/container.xml (the
                    #container file) must be present and includes the 
                    #directory of assets and package file.
                    if filename.find('META-INF/container.xml') != -1:
                        foundFlag=True
                        print("found cf")
                        #Container File: cf
                        cf=epubzipfile.open(filename)
                        cfc=cf.read() #Container file contents
                        root=ET.fromstring(cfc)
                        packagepage=None
                        for child in root:
                            for chi in child:
                                if "package.opf" in chi.attrib['full-path']:
                                    packagepath=chi.attrib['full-path']
                                    break #We got the package file..
                        if packagepath != None:
                            epubassetfolder=packagepath.rsplit('/',1)[0]
                            #package File: pf
                            pf=epubzipfile.open(packagepath)
                            pfc=pf.read()
                            pfcroot=ET.fromstring(pfc)
                            title=None
                            identifier=None
                            for child in pfcroot:
                                for chi in child:
                                    if "}title" in chi.tag:
                                        title=chi.text
                                    if "}identifier" in chi.tag:
                                        identifier=chi.text
			    if identifier == None:
				print("!!Could Not get the Block Unique ID")
				elpepubid="replacemewithxmldata"
				return "newfail", None
			    else:
				if title == None:
				    print("!Could Not get title from the elp exported to epub!")
				    title="-"
                                print("Title and Block ID obtained.")
                                elpepubid=identifier
                                elpepubname=title
                        else:
                            print("!!ERROR in getting package file from EPUB!!")
			    return "newfail", None
                if foundFlag==False:
                    print("!!Unable to find the package.opf file in epub!!")
		    return "newfail", None
		
		if name == "":
		    name=elpepubname


	    	if (os.system('unzip -q ' + "\"" + appLocation + '/../UMCloudDj/media/eXeExport/' +\
	    	    	unid + "/" + name + ".epub" + "\"" + " -d " + appLocation + \
			    '/../UMCloudDj/media/eXeExport/' + unid + "/"  )) == 0: # If unzip-ed successfully.
	    	    #Get epub asset folder name from META-INF/container.xml
	    	    epubassetfolder = "EPUB"
	    	    if (os.system('mv ' + "\"" + appLocation + '/../UMCloudDj/media/eXeExport/' +\
	    	        unid+"/"+epubassetfolder+"\""+ " " +appLocation+'/../UMCloudDj/media/eXeExport/'+\
	    	    	    unid + "/" + name)) == 0:
	    	    	print("2. Unzipped and verified.")
	    	    	if os.system('cp ' + appLocation + '/../UMCloudDj/media/eXeExport/'\
			    + unid + '/' + name + '/ustadpkg_html5.xml ' +\
			 	"\"" + appLocation + '/../UMCloudDj/media/eXeExport/'\
			 	    + unid + '/' + name + '_ustadpkg_html5.xml' +\
			 		"\"" ) == 0: #ie if command got executed in success
	    	    	    print("3. Export process completed..")
			    print(elpepubid)
	    	    	    return "newsuccess", elpepubid
	    	    	else:
	    	    	    print("!!Couldn't copy html file xml to main directoy."+\
			        "Something went wrong in the exe export!!")
			    return "newfailcopy", None
		    else:
		    	print("!!Couldn't rename EPUB folder to Block name!!")
		    	return "newfail", None
	    else:
	    	print("!!Exe didn't run. exe_do : something went wrong in eXe!!")
	    	return "newfail", None
      
"""Currently disabled and depricated. Grunt course function was used to run the exported
unit tests and go through a couese using grunt and webkit.This would validate if all the pages 
can be loaded and would result in success for that course exproted.
Process involved getting and setting up grunt for every course exported. Resulted in big folders.
Direction of test changed to being on eXe instead of UMCloud.
""" 
"""
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
"""


###################################################################################

##################################################################################
#Courses CRUD

"""
Course Model Form that would expose name, category and description
for edits and creation forms.
"""
class CourseForm(ModelForm):
    category = forms.CharField(required = False)
    description = forms.CharField(required = False)
    class Meta:
        model = Course
        fields = ('name', 'category','description')

"""Course view to render all courses in a primeui table rendered
by course template"""
@login_required(login_url='/login/')
def course_table(request, template_name='myapp/course_table.html'):
    organisation = User_Organisations.objects.get(\
			user_userid=request.user).\
			organisation_organisationid;
    courses = Course.objects.filter(success="YES", \
				organisation=organisation)
    publisher_details=[]
    for course in courses:
	pub_details=course.publisher.username + "(" +\
		 course.organisation.organisation_name + ")"
	publisher_details.append(pub_details)
	
    data = {}
    data['object_list'] = courses
    data['object_list'] = zip(courses,publisher_details)

    courses_as_json = serializers.serialize('json',courses)
    courses_as_json = json.loads(courses_as_json)
    courses_as_json = zip(courses_as_json, publisher_details)

    return render(request, template_name, {'data':data, \
			'courses_as_json':courses_as_json})

"""
View to delete a course.
Only the course publisher can delete the course
"""
@login_required(login_url='/login/')
def course_delete(request, pk, template_name='myapp/course_confirm_delete.html'):
    course = get_object_or_404(Course, pk=pk)
    if request.method=='POST':
	if request.user == course.publisher:
            course.delete()
	else:
	    return redirect('managecourses')
        return redirect('managecourses')
    return render(request, template_name, {'object':course})

"""
View to create a new course with form elements in Course Model 
Form and render it and create the course with POST parameters.
The template also asks for block(package) assignment.
"""
@login_required(login_url="/login/")
def course_create(request, template_name='myapp/course_create.html'):
    organisation = User_Organisations.objects.get(user_userid=\
			request.user).organisation_organisationid;
    form = CourseForm(request.POST or None)
    #packages = Document.objects.all()
    packages = Document.objects.filter(publisher=request.user, success="YES")
    packages = Document.objects.filter(success="YES", publisher__in=\
		User.objects.filter(pk__in=User_Organisations.objects.filter(\
			organisation_organisationid=organisation).values_list(\
						'user_userid', flat=True)))


    teacher_role = Role.objects.get(pk=5)
    student_role = Role.objects.get(pk=6)

    students = User.objects.filter(pk__in=User_Roles.objects.filter(\
				role_roleid=student_role).values_list(\
					'user_userid', flat=True))

    students = User.objects.filter(pk__in=User_Organisations.objects.\
			filter(organisation_organisationid=organisation).\
			values_list('user_userid', flat=True)).filter(\
				pk__in=User_Roles.objects.filter(\
					role_roleid=student_role).\
					values_list('user_userid',\
							 flat=True))

    #allclasses=Allclass.objects.all()
    allclasses = Allclass.objects.filter(\
		school__in=School.objects.filter(\
					organisation=organisation));

    data = {}
    data['package_list'] = packages
    data['student_list'] = students
    data['allclass_list'] = allclasses
    if request.method == 'POST':
        post = request.POST;
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
		course_organisation = User_Organisations.objects.get(\
					user_userid=course_publisher).\
						organisation_organisationid
		course = Course(name=course_name, category=course_category,\
			     description=course_desc, publisher=course_publisher,\
				 organisation=course_organisation)
		course.save()

                print("Mapping packages with course..")

		for everypackageid in packageidspicklist:
			currentpackage = Document.objects.get(pk=everypackageid)
			course.packages.add(currentpackage)
			course.save()

		print("Mapping students with course..")
		for everystudentid in studentidspicklist:
			currentstudent=User.objects.get(pk=everystudentid)
			course.students.add(currentstudent)
			course.save()
 
   		print("Mapping allclasses with course..")
		for everyallclassid in allclassidspicklist:
			currentallclass = Allclass.objects.get(pk=everyallclassid)
			course.allclasses.add(currentallclass)
			course.save()
			

		setattr(course, 'success','YES')
		course.save()
		print("All done for course creation.")
		data['state']="Course : " + course.name + " created successfully."
		if 'submittotable' in request.POST:
			return render(request, 'myapp/confirmation.html', data)
                if 'submittonew' in request.POST:
			statesuccess=1
			data['statesuccess']=statesuccess
			return render(request, template_name, data)
                else:
			data['state']="Something went wrong"
                        return redirect ('managecourses')

                return redirect('managecourses')
        else:
                print("Course already exists")
		data['state']="A course with that name already exists.\
				 Please specify another name"
		return render(request, template_name, data)
                #Show message that the class name already exists in our database.
		#(For the current organisation)
                #return redirect('managecourses')

    return render(request, template_name, data)

"""
View to update the the course details as per course model form and template
"""
@login_required(login_url='/login/')
def course_update(request, pk, template_name='myapp/course_form.html'):
    organisation = User_Organisations.objects.get(\
		user_userid=request.user).organisation_organisationid;
    course = get_object_or_404(Course, pk=pk)
    form = CourseForm(request.POST or None, instance=course)

    #Assigned Packages mapping
    allpackages = Document.objects.all();
    allpackages = Document.objects.filter(\
			publisher=request.user, success="YES")
    allpackages = Document.objects.filter(\
			success="YES", \
			publisher__in=User.objects.filter(\
			   pk__in=User_Organisations.objects.filter(\
			      	organisation_organisationid=organisation).\
				values_list('user_userid', flat=True)))
    assignedpackages = course.packages.all();

    student_role = Role.objects.get(pk=6)
    allstudents = User.objects.filter(pk__in=User_Roles.objects.filter(\
			role_roleid=student_role).values_list(\
					'user_userid', flat=True))
    allstudents = User.objects.filter(\
			pk__in=User_Organisations.objects.filter(\
			    organisation_organisationid=organisation).\
				values_list('user_userid', flat=True)).\
				    filter(pk__in=User_Roles.objects.filter(\
					role_roleid=student_role).values_list(\
					    	'user_userid', flat=True))
    assignedstudents = course.students.all()

    assignedallclasses = course.allclasses.all()
    allallclasses = Allclass.objects.filter(school__in=School.objects.filter(\
						organisation=organisation));

    if form.is_valid():
        form.save()
        print("Going to update the assigned packages..")
        packagesidspicklist=request.POST.getlist('target')
        print(packagesidspicklist)
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
    return render(request, template_name, {'form':form, 'all_students':allstudents,\
		 'assigned_students':assignedstudents,'all_packages':allpackages,\
		'assigned_packages':assignedpackages, 'all_allclasses':allallclasses,\
		 'assigned_allclasses':assignedallclasses})


# Create your views here.
