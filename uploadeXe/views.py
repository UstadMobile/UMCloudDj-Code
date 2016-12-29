from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect, get_object_or_404 

import os 
from uploadeXe.models import Package as Entry
from uploadeXe.models import AcquisitionLink
from uploadeXe.forms import ExeUploadForm, ThumbnailUploadForm
from uploadeXe.models import Course
from uploadeXe.models import Categories
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
import simplejson
from epubresizer import EPUBResizer
from os.path import basename
from urlparse import urlparse


######################################################################
#Internal Migration
@login_required(login_url='/login/')
def blockToAcquisitionLink(request):
    print("Hey there!")
    if request.user.is_staff == True:
	all_blocks = Entry.objects.filter(success="YES")
	a=len(all_blocks)
	appLocation = (os.path.dirname(os.path.realpath(__file__)))
	serverlocation=appLocation+'/../'
        mainappstring = "UMCloudDj/"
	fails = []
	for every_block in all_blocks:
	    path = str(every_block.exefile)
	    try:
	        size = os.path.getsize(serverlocation + mainappstring \
		    + settings.MEDIA_URL + str(every_block.exefile))
	    except:
		size = 0
	 	print("size zero for " + str(every_block.id))
	
	    if (every_block.elphash is not None and every_block.elphash != "-" \
		and every_block.elphash != ""):
		md5hash = every_block.elphash
	    else:
                md5hash = str(hashlib.md5(open(serverlocation + mainappstring \
                    + settings.MEDIA_URL + path ).read()).hexdigest())
	    
	    """
	    hashlist = AcquisitionLink.objects.values_list('md5', flat=True)
	    print(hashlist)
	    if str(md5hash) in hashlist:
		print("Already uploaded and recorded. Putting it in anyway. " \
			+ "Force new might have been selected")
	    """
	    
	    if (path.lower().endswith('.epub')):
	        mimetype="application/epub+zip"
	    elif (path.lower().endswith('.elp')):
	       mimetype="application/elp+zip"
	    else:
	        mimetype=""
	    title = every_block.name
	    preview_path = get_package_url(every_block)
	    if preview_path == "" or preview_path ==None:
		preview_path = every_block.url
	    try:
	        acquisition_link = AcquisitionLink(exefile=every_block.exefile,\
	        mimetype=mimetype, length=size, title=title, md5=md5hash,\
	            preview_path=preview_path)
	        #acquisition_link.save()
		#Assigning Entry to Link
		acquisition_link.entry = every_block;
	 	acquisition_link.save()
		all_acquisition_links = every_block.acquisitionlink.all()
		print("All acquisition links for block " + str(every_block.id) + " is " + str(all_acquisition_links))

		
	    except:
	        print("Unable to make for block " + str(every_block.id))
	  	fails.append(every_block.id)
	    
		
        authresponse = HttpResponse(status=200)
        authresponse.write("Welcome Super Admin. No. of blocks failed: " + str(fails))
        return authresponse
    else:
	return redirect('home')

######################################################################
#Package CRUD

"""
Entry is Package which is a Block. This is the form for the block. 
"""
class EntryForm(ModelForm):
    class Meta:
        model = Entry
	fields = ('name',)
	
"""
The view to render delete a particular block. 
"""
@login_required(login_url='/login/')
def delete(request, pk, template_name='myapp/package_confirm_delete.html'):
    document = get_object_or_404(Entry, pk=pk)
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
    documents = Entry.objects.filter(publisher=request.user,\
					 success="YES")
    current_user = request.user.username
    courses_as_json = serializers.serialize('json', documents)
    courses_as_json = json.loads(courses_as_json)

    return render(request, template_name, {'courses_as_json':\
					    courses_as_json})

"""
Common function to get preview url for opds and 
portal links
"""
def get_package_url(block):
    appLocation = (os.path.dirname(os.path.realpath(__file__)))
    #hostname = request.get_host()
    serverlocation=appLocation+'/../'
    mainappstring = "UMCloudDj/"
    package_url = ""

    filename=str(block.exefile)
    if filename.lower().endswith(".epub") or filename.lower().endswith(".elp"):
        #extracted_path = block.url.rsplit("/",1)[0] + "/"
        extracted_path = block.url
        print(extracted_path)
        container_path = ""
        print("Getting container path")
        if not os.path.isfile(serverlocation + mainappstring \
            + extracted_path + "/" + "META-INF/container.xml"):
            print("Not in there 1")
            extracted_path = block.url.rsplit("/",2)[0]

            if os.path.isfile(serverlocation + mainappstring \
                + extracted_path + "/" + "META-INF/container.xml"):
                #Legacy support
                container_path = serverlocation + mainappstring \
                    + extracted_path + "/" + "META-INF/container.xml"
            else:
                print("Cant figure. Emptying")
                print("Can't figure this.");
                container_path = "";
        else:
            extracted_path = block.url
            container_path = serverlocation + mainappstring \
                + extracted_path + "/" + 'META-INF/container.xml'


        if container_path == "":
            url = ""
        else:
            tree = ET.parse(container_path)

            root = tree.getroot()
            packagepage=None
            for child in root:
                for chi in child:
                    if ".opf" in chi.attrib['full-path']:
                        packagepath=chi.attrib['full-path']
                        print("YAY")
                        print(packagepath)
                        break #We got the package file..
            splitpp = packagepath.rsplit('/',1)
            if len(splitpp) > 1:
                epubassetfolder=packagepath.rsplit('/',1)[0]
                restpath = packagepath.rsplit('/',1)[1]
                if not os.path.isfile(serverlocation + mainappstring \
                    + extracted_path + packagepath):
                    print("Container file no existo..")
                    epubassetfolder = block.name
                    packagepath = epubassetfolder + "/" + restpath
            else:
                epubassetfolder=""

            #http_prefix = "http://"
	    if not extracted_path.endswith("/"):
                extracted_path = extracted_path + "/"
            package_url = extracted_path + packagepath

            #package_url = base server + media + path to opf file.
            #url="/media/epubrunner/ustad_contentepubrunner.html?src=" + package_url + "&output=embed";
    else:
        #url = str(block.exefile)
	package_url = ""
    return package_url

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
    document = get_object_or_404(Entry, pk=pk)
    form = EntryForm(request.POST or None, instance=document)
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

    appLocation = (os.path.dirname(os.path.realpath(__file__)))
    hostname = request.get_host()
    serverlocation=appLocation+'/../'
    mainappstring = "UMCloudDj/"
    http_prefix = "http://"

    #Update in ignoring port:
    hostname = urlparse(http_prefix + hostname).hostname #Ignores the port in hostname

    package_url = get_package_url(document)
    if package_url != "":
	package_url = http_prefix + hostname + package_url
        url="/media/epubrunner/ustad_contentepubrunner.html?src=" + package_url + "&output=embed";
    else:
	url = settings.MEDIA_URL + str(document.exefile)
    
    thumbnail = None
    try:
	thumbnail = document.thumbnail
    except:
	print("No thumbnail set.")
	

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
	
	try:
	    new_thumbnail = request.FILES['new_thumbnail']
	    print("New Thumbnail: " )
	    print(new_thumbnail)
	    document.thumbnail = new_thumbnail
	    document.save()
	except:
	    print("No new thumbnail specified..")
	return redirect('manage')
    else:
	print("Something wrong with the Model Form.")

    return render(request, template_name, {'form':form, \
			'thumbnail': thumbnail,\
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

    #students = User.objects.filter(pk__in=User_Roles.objects.\
    #	filter(role_roleid=student_role).values_list(\
    #				'user_userid', flat=True))
    organisation = User_Organisations.objects.get(\
				user_userid=request.user\
				).organisation_organisationid;
    allcourses = Course.objects.filter(success="YES", \
				organisation=organisation)

    data = {}
    data['teacher_list'] = teachers
    #data['student_list'] = students
    #data['students_list'] = []
    data['all_courses'] = allcourses

    current_user = request.user.username
    # Render list page with the documents and the form
    return render_to_response(
        template_name,
        {'all_courses':data['all_courses'],\
	#'student_list':data['student_list'],\
	'current_user': current_user},
        context_instance=RequestContext(request)
    )

"""Common function to get block if and name from epub
   file
"""
def get_epub_blockid_name(epubpath):
    print("Starting epub info crawler..")
    try:
        epubfilehandle = open(epubpath, 'rb')
        epubasazip = zipfile.ZipFile(epubfilehandle)
    except:
        print("!!Could Not open epub file")
        state="Unable to upload. Unable to retrieve epub file"
        return None, None, state, None, None, None

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
                        if ".opf" in chi.attrib['full-path']:
                            packagepath=chi.attrib['full-path']
			    print("YAY")
		    	    print(packagepath)
                            break #We got the package file..
		print("package path found ????")
                packageFound=False
                if packagepath != None:
                    epubassetfolder=packagepath.rsplit('/',1)[0]
		    splitpp = packagepath.rsplit('/',1)
		    if len(splitpp) > 1:
			epubassetfolder=packagepath.rsplit('/',1)[0]
		    else:
			epubassetfolder=""
                    	#package File: pf
                    try:
                        pf=epubasazip.open(packagepath)
                    except Exception as ex:
                        packageFound=False
			print(ex)
                    else:
			print("Package found!")
                        packageFound=True
                        pfc=pf.read()
                        pfcroot=ET.fromstring(pfc)
                        title=None
                        identifier=None
			subject = None
                        for child in pfcroot:
                            for chi in child:
                                if "}title" in chi.tag:
                                    title=chi.text
                                if "}identifier" in chi.tag:
                                    identifier=chi.text
				if "}subject" in chi.tag:
				    subject = chi.text

                        if title != None and identifier != None:
                            elplomid=identifier
                            elpiname=title
			    #Get TinCan Prefix:
                            tincanprefix, description, lang=get_prefix_from_tincanxml(epubpath)
			    print("Hey, found prefix.. returning values..")
                            return elplomid, elpiname, tincanprefix, description, lang, subject

                        else:
                            elpiname=None
                            elplomid=None
                            print("!!ERROR in getting title and BlockID!!")
                            elpid="replacemewithxmldata"
                            state="Upload Failed. A valid title and ID was not found"
                            data['state']=state
                            data['statesuccess']=0
                            return None, None, state, None, None, None

                if packageFound == False:
                        print("!!ERROR in getting package file from EPUB!!")
                        state="Failed to upload block. No package file as per container xml."
                        statesuccess=0
                        data['state']=state
                        data['statesuccess']=statesuccess
                        return None, None, state, None, None, None

        if foundFlag==False:
            print("!!Unable to find the container xml file in epub!!")
            state="Failed to upload block. Not a valid epub (no container xml)"
            statesuccess=0
            data['state']=state
            data['statesuccess']=statesuccess
            return None, None, state, None, None, None
    #except:
    else:
        state="Something went wrong in file upload. Contact us."
        epubfilehandle.close();
        return None, None, state, None, None, None
    epubfilehandle.close();
    return None, None, "Something went wrong in the upload. Please contact us.", None, None, None

"""Common function: To figure out what the prefix is from the tincan.xml file.
   this tincan.xml file is generated as per export in epub.
"""
def get_prefix_from_tincanxml(epubpath):
    try:
        epubfilehandler = open(epubpath, 'rb')
        epubasazip = zipfile.ZipFile(epubfilehandler)
    except:
	print("!!Unable to open epub file for tincan xml extraction")
	return None, None, None
    try:
	print("here.....")
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
			        return None, None, None
   			    else:
			        if activityid != "" and activityid != None:
				    description = ""
				    lang = ""
				    for activityelement in activitieselement:
					if "description" in activityelement.tag:
					    description = str(activityelement.text)
					    lang = (activityelement.attrib['lang'])
			
				    tincanprefix = activityid.rsplit('/',1)[0]
			            if tincanprefix != "":
				        epubfilehandler.close()
					print("Found prefix!" + str(tincanprefix))
				
				        return tincanprefix, description, lang
				    else:
				        epubfilehandler.close()
				        return None, None, None
			        else:
				    epubfilehandler.close()
				    return None, None, None
	if foundPrefix == False or foundTinCanFile == False:
	    return None, None, None
    except:
	print("!!Something went wrong in epub tincanxml extraction!!")
        epubfilehandler.close()
    epubfilehandler.close()
    return None, None, None




"""View and method to handle block/elp file uploads.
"""
@csrf_exempt
#@login_required(login_url='/login/')
def upload(request, template_name='myapp/upload_handle.html'):
    print("Upload request coming through..")
    # Renders the Block upload and assignation form. 
    state=""
    data = {}
    form = ExeUploadForm() # A empty, unbound form
    #documents here are just existing Blocks / Packages
    
    if request.user is None or request.user.is_anonymous():
	print("No user in request")
	if 'username' not in request.POST.keys():
	    print("Invalid request")
	    return HttpResponse("Not a valid request..", status=400)
	else:
	    if request.POST['username'] == "":
	        print("Invalid request")
	        return HttpResponse("Username given is empty..", status=400)
		
	if 'password' not in request.POST.keys():
	    print("No password given.")
	    return HttpResponse("Not a valid request..", status=400)

	username = request.POST['username']
	password = request.POST['password']
	user = authenticate(username=request.POST['username'], \
               password=request.POST['password'])
        if user is not None:
	    print("Login a success")
	    request.user = user
	    print("Setted request user")
	else:
	    print("Wrong username/password combination")
	    return HttpResponse("Authentication failed", status=402)

    publisher = request.user
    documents = Entry.objects.filter(\
                 publisher=publisher, success="YES", active=True)
    documents = []
    current_user = request.user.username
    data['documents']=documents
    data['form']=form
    data['current_user']=current_user
    if request.method == 'POST':
        #If method is POST, an elp file is being uploaded. 
        post = request.POST;
        state = ""
        studentidspicklist=post.getlist('target')
	description = post.get('block_desc')

	elpiname=None
	elplomid = None

	#getting the form from the POST request      
        form = ExeUploadForm(request.POST, request.FILES)
	forceNew     = request.POST.get('forceNew')
	noAutoassign = request.POST.get('noAutoassign') 

	#getting category and other  extra elements
	try:
	    category = request.POST.get('category')
	except: 
	    category = None
	try:
	    grade_level = request.POST.get('gradeLevel')
	except:
	    grade_level = None
	try:
	    blockcourse = request.POST.get('blockCourse')
	except:
	    blockcourse = None
	try:
	    entry_id = request.POST.get('entryId').strip()
	    print("Entry: " + str(entry_id))
	    try:
		entry_selected = Entry.objects.filter(elpid=entry_id, success='YES', active=True).latest('id')
	        print("Got Entry Selected")
	    except Exception, e:
		entry_selected = None
		print("Unable to identify entry..")
		print(str(e))
	except:
	    entry_selected = None

	data['forceNew']      = forceNew
	data['noAutoassign']  = noAutoassign
	data['category']      = category
	data['gradeLevel']    = grade_level
	data['blockCourse']   = blockcourse
	data['description']   = description
	data['entrySelected'] = entry_selected
	data['publisher']     = publisher

        #verifying the form (Django style)
        #if form.is_valid():
	if True:
          #For Every file uploaded
	  for exefile in request.FILES.getlist('exefile'):
	    print("In file.." + str(exefile))
	    print("Checking thumbnail..")
	    try:
	        thumbnail = request.FILES.get('thumbnail')
		print("Got Thumbnail!:")
		print(thumbnail)
		
	    except:
		thumbnail = None
		print("No Thumbnail found. Setting to None.")
	    data['thumbnail'] = thumbnail
            #This is the new thing
            return_value, newdoc, data_updated = handle_block_upload(exefile, data)
	    print("Handle block upload done.")
            #If block failed to upload and / or validatinon failed
            if return_value == False or return_value is None:
                return render(request, template_name, data_updated)
            else:
                data = data_updated

            #Assigning students
            for everystudentid in studentidspicklist:
                #("Looping student:")
                currentstudent=User.objects.get(pk=everystudentid)
                newdoc.students.add(currentstudent)
                newdoc.save()          
            
            rete = return_value[0]
            elpepubid = return_value[1]
            uid = return_value[2]
            unid = return_value[3]
            elpiname = return_value[4]
            elplomid = return_value[5]

	    if rete == "linkaddsuccess":
		state="Your Acquisition Link has been uploaded to " + newdoc.entry.name
		statesuccess=1
		data['state']=state
		data['statesuccess']=statesuccess
		
	 	
            elif rete =="newsuccess":
		print("True, this block will be newly created.")
                setattr(newdoc, 'success', "YES")
                setattr(newdoc, 'publisher', request.user)
		#newdoc.description = description
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
                
                """
                Adding package to course
                """
                #("Going to assign the package to the selected book")
                courseidspicklist=request.POST.getlist('target2')
                for everycourseid in courseidspicklist:
                    currentcourse = Course.objects.get(pk=everycourseid)
                    currentcourse.packages.add(newdoc)
                
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
		#newdoc.description = description
                newdoc.save()
		#newdoc.delete()

	  if 'submittotable' in request.POST:
	    data['state']=state
            return render(request, template_name, data)
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
    documents = Entry.objects.filter(\
			publisher=request.user, success="YES", active=True)
    current_user = request.user.username
    # Render list page with the documents and the form
    return render_to_response(
        template_name,
        {\
	'documents': documents, 'form': form,\
	 'current_user': current_user},
        context_instance=RequestContext(request)
    )

"""
Make an Acquisition Link from the block already uploaded
"""
def make_acquisition_link(block):
    #Adding the file upload as an Acquisition Link
    print("Adding the file upload as an Acquisition Link!")
    path = str(block.exefile)
    if (path.lower().endswith('.epub')):
        mimetype="application/epub+zip"
    elif (path.lower().endswith('.elp')):
        mimetype="application/elp+zip"
    elif (path.lower().endswith('.pdf')):
        mimetype="application/pdf"
    else:
        mimetype=""
    try:
        size = os.path.getsize(serverlocation + mainappstring \
            + settings.MEDIA_URL + str(block.exefile))
    except:
        size = 0

    try:
        preview_path = get_package_url(block)
    except:
        print("Something wrong in getting preview path.")
        preview_path = None

    #This will only work for already uploaded epubs..
    if preview_path == "" or preview_path ==None:
        preview_path = block.url
    try:
        acquisition_link = AcquisitionLink(exefile=block.exefile,\
            mimetype=mimetype, length=size, title=block.name, md5=block.elphash,\
            preview_path = preview_path)
    except:
        print("Cant create AL")
    #Assigning Entry to Link
    acquisition_link.entry = block;
    acquisition_link.save()
    print("AL made!")


"""
Make New Acquisition Link From File object and master entry object
"""
def make_acquisition_link_new(blockfile, entry):
	#Adding the file upload as an Acquisition Link
	print("Adding the file upload as an Acquisition Link!")
	appLocation = (os.path.dirname(os.path.realpath(__file__)))
	serverlocation=appLocation+'/../'
        mainappstring = "UMCloudDj/"

	acquisition_link = AcquisitionLink(exefile=blockfile, \
	    mimetype="-", length = 0, title = str(blockfile), active=False, entry=entry)
	acquisition_link.save()
	uid = str(acquisition_link.exefile)
	unid = uid.split('.um.')[-2]
	unid = unid.split('/')[-1]  #Unique id here
	path = str(acquisition_link.exefile)

	path = str(acquisition_link.exefile)
	if (path.lower().endswith('.epub')):
	    mimetype="application/epub+zip"
	elif (path.lower().endswith('.elp')):
	   mimetype="application/elp+zip"
	elif (path.lower().endswith('.pdf')):
	    mimetype="application/pdf"
	else:
	    mimetype=""
	try:
	    size = os.path.getsize(serverlocation + mainappstring \
		+ settings.MEDIA_URL + str(acquisition_link.exefile))
	except:
	    size = 0

	"""
	preview_path = get_package_url(newdoc)
	if preview_path == "" or preview_path ==None:
	    preview_path = everyblock.urlnewdoc
	"""
	md5hash = str(hashlib.md5(open(serverlocation + mainappstring \
                    + settings.MEDIA_URL + path ).read()).hexdigest())

	acquisition_link.mimetype = mimetype
	acquisition_link.length = size
	acquisition_link.md5 = md5hash
	
	acquisition_link.save()

	#Assigning Entry to Link
	print("Assigning entry to acquisition link")
	acquisition_link.entry = entry;
	acquisition_link.save()

	acquisition_link.preview_path = settings.MEDIA_URL + str(acquisition_link.exefile)
	acquisition_link.save()
	
	acquisition_link.active = True;
	acquisition_link.save()
	print("Created new Acquisition Link and assigned it to an entry")
	return acquisition_link


"""
Internal common function that Handles elp/epub file upload. 
Takes in blockfile, publisher (User object), forceNew parameter, noAutoAssign parameter, data for returning to views)
Returns return_value, Block object (Package object), data for returning to views.

return_value is an array of: [rete, elpepubid, uid, unid, elpiname, elplomid]

"""

def handle_block_upload(blockfile, data):
    publisher = data['publisher']
    forceNew = data['forceNew']
    noAutoassign = data['noAutoassign']
    try:
	entry_selected = data['entrySelected']
    except:
	entry_selected = None

    print("Checking if entry is selected..")
    if entry_selected is not None:
	print("Got entry. Now making Acuisition link")
        try:
	    acquisition_link = make_acquisition_link_new(blockfile, entry_selected)
	except Exception, e:
	    print("Couldn't make Acquisition Link. Error.")
	    print(str(e))
	    return None, None, data
	
	uid = str(acquisition_link.exefile)
        unid = uid.split('.um.')[-2]
        unid = unid.split('/')[-1]  #Unique id here
        path = str(acquisition_link.exefile)

	return_values = []
        return_values.append("linkaddsuccess")
        return_values.append(None)
        return_values.append(uid)
        return_values.append(unid)
        return_values.append(str(blockfile))
        return_values.append(unid)
	print("All done?")
	return return_values, acquisition_link, data
	
    print("Handling Block upload for user:" +  str(publisher.username))
    appLocation = (os.path.dirname(os.path.realpath(__file__)))

    entryname=None
    entryid = None
    
    #Assume POST validation and Form validation is run
    print("Creating Block object..")
    newdoc = Entry(exefile=blockfile)
    if data['thumbnail'] is not None:
	newdoc.thumbnail = data['thumbnail']

    uid = str(getattr(newdoc, 'exefile'))
    
    #Temporarily create the entry for the file uploaded.
    setattr(newdoc, 'url', '-')
    setattr(newdoc, 'publisher', publisher)
    setattr(newdoc, 'elphash', '-')
    setattr(newdoc, 'tincanid', '-')
    
    newdoc.save()
    print("Created Block object.")

    #Getting block md5sum
    uid = str(getattr(newdoc, 'exefile'))
    print(uid)
    serverlocation=appLocation+'/../'
    mainappstring = "UMCloudDj/"
    elphash = hashlib.md5(open(serverlocation + mainappstring \
		+ settings.MEDIA_URL + uid ).read()).hexdigest()	
    hashlist=Entry.objects.all().values_list('elphash')
    if str(elphash) in hashlist:
	print("File already uploaded. Do we want to upload it again?")
	#Put action here for future logic for existing files.
    setattr(newdoc, 'elphash', elphash)

    #Unique Upload ID.
    unid = uid.split('.um.')[-2]
    unid = unid.split('/')[-1]  #Unique id here.
    setattr(newdoc, 'uid', unid)
    
    #EPUB/ELP is technically a ZIP file.
    elpfile=appLocation + '/../UMCloudDj/media/' + uid
    elpfilehandle = open(elpfile, 'rb')
    try:
        elpzipfile = zipfile.ZipFile(elpfilehandle)
    except:
	print("NOT A ZIP FILE!")
   
    #If it is an epub file:
    if uid.lower().endswith('.epub'):
	print("An EPUB File has been uploaded.." + uid)

	#Updated to get description and lang from the epub.
	entryid, entryname, tincanprefix, description, lang, subject = get_epub_blockid_name(elpfile)
	#print("Post get epub blockid")

	if entryid == None and entryname == None :
	    setattr(newdoc, 'success', 'NO')
	    setattr(newdoc, 'tincanid', '-')
	    if lang is not None and lang != "":
		setattr(newdoc, 'lang', lang)
	    if subject is not None and subject != "":
		print("Subject is: " + str(subject))
		setattr(newdoc, 'subject', subject)
	    newdoc.save()
	    state= tincanprefix
	    statesuccess=0
	    data['state']=state
	    data['statesuccess']=statesuccess

            return False, None, data
	    #return render(request, template_name, data)
	else:
	    setattr(newdoc, 'elpid', entryid)
	    setattr(newdoc, 'name', entryname)
	    if description is not None and description != "":
	        setattr(newdoc, 'description', description)
	    if lang is not None and lang != "":
                setattr(newdoc, 'lang', lang)
            if subject is not None and subject != "":
                print("Subject is: " + str(subject))
                setattr(newdoc, 'subject', subject)
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

		subject = None
                #using ET
                root = ET.fromstring(elpxmlfilecontents)
                for child in root:
                    foundFlag2=False # For tincan prefix
		    foundFlag3=False # For description
	 	    foundFlag4=False # For lang
                    for chi in child:
                        if foundFlag2 == True:
                            tincanprefix=chi.attrib['value']
			    foundFlag2 = False
			if "}instance" in chi.tag:
			    if "DublinCore" in chi.attrib['class']:
			        for dublindictionary in chi:
				    subjectFlag = False
				    for dublindictelements in dublindictionary:
					if subjectFlag == True:
					    subject = dublindictelements.attrib['value']
					    print("OMG Got Subject : " + str(subject))
					    subjectFlag = False
					if "}string" in dublindictelements.tag:
					    if "subject" in dublindictelements.attrib['value']:
						subjectFlag = True
					
                        if "}string" in chi.tag:
                            if "xapi_prefix" in chi.attrib['value']:
                                foundFlag2=True
			if foundFlag3 == True:
			    description=chi.attrib['value']
			    foundFlag3 = False
			if "}string" in chi.tag:
			    if "_description" in chi.attrib['value']:
				foundFlag3 = True
			if foundFlag4 == True:
			    lang=chi.attrib['value']
			    foundFlag4 = False
			if "}string" in chi.tag:
			    if "_lang" in chi.attrib['value']:
				foundFlag4 = True
		try:
		    if not description:
			description="This is a block"
		except:
		    description="This is a Block"
		setattr(newdoc, 'description', description)

		try:
		    if not lang:
			lang=""
		except:
		    lang="-"
		setattr(newdoc, 'lang', lang)
			
                try:
                    if not tincanprefix:
                        tincanprefix="-"
                except:
                    tincanprefix=""
                setattr(newdoc, 'tincanid', tincanprefix)

		try:
		    if subject is not None and subject != "":
			setattr(newdoc, "subject", subject)
			newdoc.save()
		except:
		    subject = None
		    print("Didn't get subject.")
			
                try:
                    dictionarylist=elpxml.getElementsByTagName('dictionary')
                    stringlist=elpxml.getElementsByTagName('instance')
                    lomemtry=None
                    for x in stringlist:
                        if x.getAttribute('class') == "exe.engine.lom.lomsubs.entrySub":
                            lomentry=x
                            break
                    entryidobject=lomentry.getElementsByTagName('unicode')
                    entryid=None
                    for e in entryidobject:
                        entryid=e.getAttribute('value')
                    setattr(newdoc, 'elpid', entryid)
                    if not entryid:
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
                            entryname=chi.attrib['value']
                            break
                        if "}string" in chi.tag:
                            if "_name" in chi.attrib['value']:
                                elpfoundFlag=True
                if not entryname:
                    entryname="-"

		#Save it all
		newdoc.save()
    	if foundFlag==False:
    	    print("!!Unable to find the container xml file in elp!!")
    	    setattr(newdoc, 'success', 'NO')
	    newdoc.save()
	    #return HttpResponseRedirect(reverse(\
            #            'uploadeXe.views.list'))

    else:
    	print("None EPUB/ELP file uploaded. Just saved.")	
        setattr(newdoc, 'url', str(newdoc.exefile))
	setattr(newdoc, 'publisher', publisher)
	setattr(newdoc, 'tincanid', '-')
    	setattr(newdoc, 'success', 'YES')
	setattr(newdoc, 'elpid', unid)
	file_name = str(newdoc.exefile).rsplit('/',1)[1].rsplit('.um.',1)[1]
	setattr(newdoc, 'name', file_name)

    if not noAutoassign:
        newdoc.students.add(publisher)
    if entryname == None:
        entryname="-"

    if entryid == None:
        entryid="-"

    if not uid.lower().endswith('.elp') or not uid.lower().endswith('.epub'):
        if entryname == None or entryname == "-":
	    entryname = str(uid).rsplit('/',1)[1].rsplit('.um.',1)[1]
	    entryid = str(unid)
	    print("Unable to get unique id. So taking uploaded unid as entry id.. " + entryid)

    rete, elpepubid = ustadmobile_export(uid, unid, entryname, entryid, forceNew)
    return_values = []
    return_values.append(rete)
    return_values.append(elpepubid)
    return_values.append(uid)
    return_values.append(unid)
    return_values.append(entryname)
    return_values.append(entryid)
    #print(str(rete)+"|"+str(elpepubid)+"|"+str(uid)+"|"+str(unid)+"|"+str(entryname)+"|"+str(entryid))
  
    #Time to check if block needs to become a course and make it. 
    try:
	blockcourse = None
	if rete == "newsuccess":
	    if uid.lower().endswith('.elp') or uid.lower().endswith('.epub'):
	        setattr(newdoc, "name", entryname)
	        setattr(newdoc, "publisher", publisher)
	        setattr(newdoc, "micro_edition", False) #disbaled micro
	        newdoc.save()
	    else:
		if entryname != None or entryname != "-":
		    if newdoc.name == "" or newdoc.name == "-":
			print("Setting name..")
        	        setattr(newdoc, 'name', entryname)
		    setattr(newdoc, 'publisher', publisher)
		    setattr(newdoc, 'micro_edition', False)
		    newdoc.save()
		else:
		    print("Something went wrong..")
		    setattr(newdoc, 'name', "-")
		    setattr(newdoc, 'publisher', publisher)
		    setattr(newdoc, 'micro_edition', False)

            courseURL = '/media/eXeExport' + '/' + unid + '/'
            setattr(newdoc, 'url', courseURL)
            setattr(newdoc, 'name', entryname)
            newdoc.save()

	    try:
                make_acquisition_link(newdoc)
            except:
                print("Unable to create Acquisition Link.")
                return_values =[]
                return_values[rete]="newfail"
                return return_values, None, data


	    if data['blockCourse'] is not None:
		#and data['blockCourse'] is True:
	        print("Got to make block into a course")
		try:
		    organisation = User_Organisations.objects.get(\
                        user_userid=publisher).\
                        organisation_organisationid;

		    blockcourse = Course(name = newdoc.name, description = "Block course for " + newdoc.name,\
			publisher = publisher, organisation = organisation)
		    if newdoc.lang is not None and newdoc.lang != "":
			blockcourse.lang = newdoc.lang

		    blockcourse.save()

		    if newdoc.subject is not None and newdoc.subject != "":
			print("Working with subject: " + str(newdoc.subject))
			try:
			    print("Will try getting the category")
			    categoryObject = None
			    categoryObject = Categories.objects.get(name=str(newdoc.subject))
			    print("Got existing category..")
			    if categoryObject is None:
				print("Could not get categody. Will try adding it.")
				newcategory = Categories(name=str(newdoc.subject), parent_id = 0)
                                newcategory.save()
                                print("Made new category : " + str(newcategory.name))
                                blockcourse.cat.add(newcategory)
                                setattr(blockcourse, 'category', newcategory.name)
                                blockcourse.save()

			    blockcourse.save()
			    try:
			        if categoryObject is not None:
				    print("Assigning category..")
				    blockcourse.cat.add(categoryObject)
			 	    setattr(blockcourse, 'category', categoryObject.name)
				    blockcourse.save()
			    except Exception as e:
				print("COULD NOT ASSIGN CATEGORY")
				print(e)
			except Exception as e2:
			    print("Exception in getting category. Will try adding it.")
			    print(e2)
			    newcategory = Categories(name=str(newdoc.subject), parent_id = 0)
			    newcategory.save()
			    blockcourse.save()
			    print("Made new category : " + str(newcategory.name))
			    blockcourse.cat.add(newcategory)
			    setattr(blockcourse, 'category', newcategory.name)
			    blockcourse.save()
		    blockcourse.save()
		except Exception as e3:
		    print("Unable to make block course. Check. Maybe we should update rete.")
		    print(e3)
		    rete = "newfail"
		#Assigning students to the course
		print("assigning students to course..")
                try:
                    for every_user in newdoc.students.all():
                        blockcourse.students.add(every_user)
                        blockcourse.save()
                    print("Assigning block to course..")
                    blockcourse.packages.add(newdoc);
                    setattr(blockcourse, 'success', "YES")
                    blockcourse.save()
                    print("Block course: " + blockcourse.name + " saved successfully!")
		    return_values.append(blockcourse.id)
	
		    #Adding category
		    if data['category'] is not None and data['category'] != "":
			override_category = data['category']
			blockcourse.category = override_category
			blockcourse.save()

		    #Adding grade level
  		    print("Adding gradeLevel")
		    if data['gradeLevel'] is not None and data['gradeLevel'] != "":
			print("grade Level is : " + str(data['gradeLevel']))
                        override_level = str(data['gradeLevel'])
                        blockcourse.grade_level = override_level
                        blockcourse.save()
		
		    #Adding language
		    if newdoc.lang != None and newdoc.lang != "" and newdoc.lang != "-":
			blockcourse.lang = newdoc.lang
			blockcourse.save()
                except:
                    print("Could not create course..")
                    newdoc.students.remove(all);
		    setattr(newdoc, 'success', 'NO')
		    newdoc.save()
		    rete = "newfail"
                    #newdoc.delete()
		    try:
                    	blockcourse.delete()
		    except:
			print("unable to delete failed course..")

	if rete == "updatesuccess":
	    #NOTE:
	    #elpepubid is the entry that got updated in updatesuccess's case
	    entry = elpepubid
	    print("Got to update the already course and assign it to the updated epub if not newly created.")
	    try:
		print("Un assign previous Acquisition Link (AL) entry..")
		previous_acquisition_links = AcquisitionLink.objects.filter(entry=entry)
		for every_previous_acquisition_link in previous_acquisition_links:
			every_previous_acquisition_link.active = False
			every_previous_acquisition_link.save()
		print("Making AL..")
		make_acquisition_link(entry)
		print("..done.")
		
            except:
                print("Unable to create Acquisition Link.")
                return_values =[]
                return_values[rete]="updatefail"
                return return_values, None, data

    except Exception, e:
	print("Block upload not over or something wrong in making block to course trial..")
	print(str(e))
	
    try:
	#saving
	newdoc.save()
    except:
	print("Unable to save package before block handle")

    return return_values, newdoc, data
    

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
    documents = Entry.objects.filter(\
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
	    newdoc = Entry(exefile=exefile)
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
	    hashlist=Entry.objects.all().values_list('elphash')
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
	
		#Updated to get description and lang from the epub.
		elplomid, elpiname, tincanprefix, description, lang, subject = get_epub_blockid_name(elpfile)

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
		    setattr(newdoc, 'description', description)
		    if lang is not None and lang != "":
		        setattr(newdoc, 'lang', lang)
		    if subject is not None and subject != "":
			setattr(newdox, 'subject', subject)
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
                            foundFlag2=False # For tincan prefix
			    foundFlag3=False # For description
		 	    foundFlag4=False # For lang
                            for chi in child:
                                if foundFlag2 == True:
                                    tincanprefix=chi.attrib['value']
				    foundFlag2 = False
                                if "}string" in chi.tag:
                                    if "xapi_prefix" in chi.attrib['value']:
                                        foundFlag2=True
				if foundFlag3 == True:
				    description=chi.attrib['value']
				    foundFlag3 = False
				if "}string" in chi.tag:
				    if "_description" in chi.attrib['value']:
					foundFlag3 = True
				if foundFlag4 == True:
				    lang=chi.attrib['value']
				    foundFlag4 = False
				if "}string" in chi.tag:
				    if "_lang" in chi.attrib['value']:
					foundFlag4 = True
			try:
			    if not description:
				description="This is a block"
			except:
			    description="This is a Block"
			setattr(newdoc, 'description', description)

			try:
			    if not lang:
				lang=""
			except:
			    lang="-"
			setattr(newdoc, 'lang', lang)
				
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
		courseURL = '/media/eXeExport' + '/' + unid + '/'
		appLocation = (os.path.dirname(os.path.realpath(__file__)))
                hostname = request.get_host()
                serverlocation=appLocation+'/../'
                mainappstring = "UMCloudDj/"
                tree = ET.parse(serverlocation + mainappstring \
                    + '/media/eXeExport' + '/' + unid + '/'+ 'META-INF/container.xml')
                root = tree.getroot()
                packagepage=None
                for child in root:
                    for chi in child:
                        if ".opf" in chi.attrib['full-path']:
                            packagepath=chi.attrib['full-path']
                            print(packagepath)
                            break #We got the package file..
		if packagepath != None:
                    assetfolder=packagepath.rsplit('/',1)[0]
                    splitpp = packagepath.rsplit('/',1)
                    if len(splitpp) > 1:
                        assetfolder=packagepath.rsplit('/',1)[0] + "/"
                    else:
                        assetfolder=""

                courseURL = '/media/eXeExport' + '/' + unid + '/'

                setattr(newdoc, 'success', "YES")
                setattr(newdoc, 'url', courseURL)
                setattr(newdoc, 'name', elpiname)
                setattr(newdoc, 'publisher', request.user)
		setattr(newdoc, 'micro_edition', False) #Disabled Micro
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


		"""
		
		#Maybe create an Acquisition Link
		old_entry = Entry.objects.filter(elpid=elplomid, success="YES").latest('id')
		old_acquisition_link = AcquisitionLink.objects.get(entry=entry).latest('id')
		old_acquisition_link.active = False
		if (entry.exefile.lower().endswith('.epub')):
                	mimetype="application/epub+zip"
            	elif (entry.exefile.lower().endswith('.elp')):
               		mimetype="application/elp+zip"
            	else:
                	mimetype=""
		new_acquisition_link = AcquisitionLink(exefile=newdoc.exefile,\
			mimetype=mimetype, .....)

		#acquisition_link = AcquisitionLink(exefile=every_block.exefile,\
                #mimetype=mimetype, length=size, title=title, md5=md5hash,\
                #    preview_path=preview_path)
		new_acquisition_link.entry = old_entry
		new_acquisition_link.save()
		"""



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
    documents = Entry.objects.filter(\
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
    found=Entry.objects.filter(elpid=elplomid, success="YES", active=True)
    elplomidDB = elplomid
    elplomid=None
    if found and not forceNew:
        print("Block ID already exists in the system." + \
        	"This export is going to be an update.")
        #To get the folder of previous export:
        folder_url=found[0].url.rsplit('/',2)[0]
	
	#Here goes the logic for epub
	print("*************************")
	print("uurl: " + uurl)
	print("unid: " + unid)
	print("name: " + name)
	print("elplomid: " + str(elplomidDB))
	print("forceNew: " + str(forceNew))
	print("folder_url: " + folder_url)
	print("**************************")

	if uurl.lower().endswith(".epub"):
		print("we have an epub over here to update..")


		#Move previous epub to old directory..
		entry = Entry.objects.filter(elpid=elplomidDB, success="YES").latest('id')
		entry_id = entry.id
		print("Entry id: " + str(entry_id))
		acquisition_link = AcquisitionLink.objects.filter(entry=entry).latest('id') #Only getting by latest.
		preview_path = acquisition_link.preview_path
		#OR you could have just used entry.url

		print("preview path: ")
		print(preview_path)
		print("Moving previous export. Command is:")
		if preview_path == None or preview_path == "":
			return "updatefail", None 
			
		if not preview_path.startswith('/'):
			preview_path = "/" + preview_path

		export_folder = '/' + preview_path.split('/')[1] + '/'+ preview_path.split('/')[2] +\
			'/' + preview_path.split('/')[3] + ''

		if os.system('mv ' + appLocation + '/../UMCloudDj' +\
			export_folder + ' ' + appLocation + '/../UMCloudDj' +\
			   export_folder  + '_old'):
			print("Moved successfully to: " + appLocation + '/../UMCloudDj' +\
			    export_folder + '_old')
		else:
			print("Error moving in command: ")
			print('mv ' + appLocation + '/../UMCloudDj' +\
			   export_folder + ' ' + appLocation + '/../UMCloudDj' +\
				export_folder + '_old')

		#Start the unzip..
		print("Going to export an EPUB file..")
            	print("Possible command:")
            	print('unzip -q ' + "\"" + appLocation + '/../UMCloudDj/media/' + uurl + "\"" + " -d " +\
                	"\"" + appLocation + '/../UMCloudDj/media/eXeExport/' +\
                        	  unid + "/" + "\"")

		if os.system('unzip -q ' + "\"" + appLocation + '/../UMCloudDj/media/' + uurl + "\"" + " -d " +\
                	"\"" + appLocation + '/../UMCloudDj/media/eXeExport/' +\
                        	 unid + "/" + "\"") == 0:

                	try:
                    		epubfile=appLocation + '/../UMCloudDj/media/' + uurl
                    		epubfilehandle = open(epubfile, 'rb')
                    		epubzipfile = zipfile.ZipFile(epubfilehandle)
                	except:
                    		print("!!Unable to open the epub file for getting block info!!")
                    		return "updatefail", None

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
                                			if ".opf" in chi.attrib['full-path']:
                                    				packagepath=chi.attrib['full-path']
                                    				break #We got the package file..

                	print("1. Exported to folder.")
                	#Get Folder name  from : META-INF/container.xml

                	if packagepath != None or packagepath != "":
				print("new package path: " + packagepath)
                    		epubassetfolder=packagepath.rsplit('/',1)[0]
                    		splitpp = packagepath.rsplit('/',1)
                    		if len(splitpp) > 1:
                        		epubassetfolder=packagepath.rsplit('/',1)[0]
                    		else:
                        		epubassetfolder=""
                	else:
                  		return "newfail", None
		
			"""
                	if epubassetfolder == "":
                    		return "newsuccess", None
                	else:
                    		print("Not in root. Skipping move and copy anyway..")
                    		return "newsuccess", None
			"""


			new_export_folder = "/media/eXeExport/" + unid + "/"
			new_opf_url = packagepath
			new_preview_path = new_export_folder + new_opf_url
			print("new preview path: " + new_preview_path)
			
			print("Already existing entry's url: " + entry.url)
			#Update existing block entry with new preview path and exefile
			#If not creating new Acquisition Link, update entry of existing one
			entry.url = new_export_folder
                        entry.exefile = uurl
                        entry.save()
			print("Already existing entry's url: " + entry.url)
			print(" Updating al's entry..")	
			acquisition_link.entry=entry
			
			#return "updatesuccess", None
			return "updatesuccess", entry

			try:
				print("Starting old EPUB update..")

			except:
				print("!!Updating old EPUB on update failed.!!")
				return "updatefail", None
			
		else:
                	print("!!EPUB failed to extract.!!")
                	return "updatefail", None
		
		    

	print("Moving previous export. Command is:")
	print('mv ' + appLocation + '/../UMCloudDj' +\
                    folder_url + ' ' + appLocation + '/../UMCloudDj' +\
                        folder_url + '_old')
	"""
	Disabling this because it messes up with new way of export. 
	ToDO: Update EPUBS
        if os.system('mv ' + appLocation + '/../UMCloudDj' +\
           	    folder_url + ' ' + appLocation + '/../UMCloudDj' +\
			folder_url + '_old'):
	    print("moved successfuilly to: " + appLocation + '/../UMCloudDj' +\
			folder_url+'_old')
	else:
	    print("Error in moving " + appLocation + '/../UMCloudDj' +\
                    folder_url + " to " + appLocation + '/../UMCloudDj' +\
                        folder_url + '_old')
	"""
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
		#return "updatesuccess", None
		return "updatesuccess", found[0]

		""" 
		#Update logic commented till bug is updated.
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

	print("URL is : " + uurl)
        #1. Check if it is an .elp file or .epub file that is being uploaded. 
        #2. Export to epub
        #3. Unzip it, get details

        if uurl.lower().endswith('.epub'):
            print("Going to export an EPUB file..")
	    print("Possible command:")
	    print('unzip -q ' + "\"" + appLocation + '/../UMCloudDj/media/' + uurl + "\"" + " -d " +\
                "\"" + appLocation + '/../UMCloudDj/media/eXeExport/' +\
                          unid + "/" + "\"")
	
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
                                if ".opf" in chi.attrib['full-path']:
                                    packagepath=chi.attrib['full-path']
                                    break #We got the package file..

                print("1. Exported to folder.")
                #Get Folder name  from : META-INF/container.xml

		if packagepath != None:
                    epubassetfolder=packagepath.rsplit('/',1)[0]
		    splitpp = packagepath.rsplit('/',1)
                    if len(splitpp) > 1:
                        epubassetfolder=packagepath.rsplit('/',1)[0]
                    else:
                        epubassetfolder=""
		else:
		  return "newfail", None
		
		if epubassetfolder == "":
		    return "newsuccess", None
	   	else:
		    print("Not in root. Skipping move and copy anyway..")
		    return "newsuccess", None

		#Disabled micro version bit
		if False:
		    print("possible move command: " + 'mv ' + "\"" + appLocation + '/../UMCloudDj/media/eXeExport/' +\
                        unid+"/"+epubassetfolder+"\"" + " " +  "\"" + appLocation+'/../UMCloudDj/media/eXeExport/'+\
                            unid + "/" + name + "\"")
            	    if (os.system('mv ' + "\"" + appLocation + '/../UMCloudDj/media/eXeExport/' +\
	    	        unid+"/" + epubassetfolder + "\"" + " " + "\"" + appLocation+'/../UMCloudDj/media/eXeExport/'+\
	    	    	    unid + "/" + name + "\"")) == 0:
            	        print("2. Unzipped and verified.")
		        print("Possible copy command:" + 'cp ' + "\"" + appLocation + '/../UMCloudDj/media/eXeExport/'\
                            + unid + '/' + name + '/ustadpkg_html5.xml' +"\"" + " " +\
                                "\"" + appLocation + '/../UMCloudDj/media/eXeExport/'\
                                    + unid + '/' + name + '_ustadpkg_html5.xml' +\
                                        "\"" )
            	        if os.system('cp ' + "\"" + appLocation + '/../UMCloudDj/media/eXeExport/'\
			    + unid + '/' + name + '/ustadpkg_html5.xml' + "\"" + " "  +\
			 	"\"" + appLocation + '/../UMCloudDj/media/eXeExport/'\
			 	    + unid + '/' + name + '_ustadpkg_html5.xml' +\
			 		"\"" ) == 0: #ie if command got executed in success
	    	    	    print("3. Export process completed.")

			    """
			    Here you can add the epub resizing micro version code.
			    """
			    width=240
			    height=320
			    try:
			        dst=os.path.splitext(basename(epubfile))[0]
			        if dst.strip():
				    print("Exists!")
				    dst = os.path.dirname(epubfile) + "/" +  dst + "_micro.epub"
				    print("destination is: " + dst)
			        else:
				    print("Unable to get destination")
				    return "newfailcopy", None

			        resizer = EPUBResizer(epubfile)
			        resizer.resize(dst, max_width = width, max_height = height)
			    except:
			        print("Unable to resize.")
			        return "newfailcopy", None
		        
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
			    splitpp = packagepath.rsplit('/',1)
                    	    if len(splitpp) > 1:
                        	epubassetfolder=packagepath.rsplit('/',1)[0]
                      	    else:
                        	epubassetfolder=""
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

		"""
		else: #eXe didnt export well.
		    print("eXe did not export well.");
		    return "newfail", None
		"""

                if foundFlag==False:
                    print("!!Unable to find the package.opf file in epub!!")
		    return "newfail", None
		
		if name == "":
		    name=elpepubname


	    	if (os.system('unzip -q ' + "\"" + appLocation + '/../UMCloudDj/media/eXeExport/' +\
	    	    	unid + "/" + name + ".epub" + "\"" + " -d " + appLocation + \
			    '/../UMCloudDj/media/eXeExport/' + unid + "/"  )) == 0: # If unzip-ed successfully.
		    print("Unzipped Successfully (epub)")
	    	    #Get epub asset folder name from META-INF/container.xml
	    	    #epubassetfolder = "EPUB"

                    if epubassetfolder == "":
                        return "newsuccess", elpepubid
                    else:
			print("Assets not in root. Skipping move and Copy ayway..")
			return "newsuccess", elpepubid

		    if False:
	    	        if (os.system('mv ' + "\"" + appLocation + '/../UMCloudDj/media/eXeExport/' +\
	    	            unid+"/"+epubassetfolder+"\""+ " " + "\"" + appLocation+'/../UMCloudDj/media/eXeExport/'+\
	    	    	        unid + "/" + name + "\"")) == 0:
	    	    	    print("2. Unzipped and verified.")
	    	    	    if os.system('cp ' + "\"" + appLocation + '/../UMCloudDj/media/eXeExport/'\
			        + unid + '/' + name + '/ustadpkg_html5.xml' + "\"" + " " +\
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
	else:
	    print("Hey there")
	    print("Unable to determine zip or epub or elp. Skipping as other version..")
	    return "newsuccess", None
      
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
        fields = ('name', 'category','description', 'grade_level', 'cover')

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
    categories=[]
    for course in courses:
	pub_details=course.publisher.username + "(" +\
		 course.organisation.organisation_name + ")"
	publisher_details.append(pub_details)
        try:
	    category = course.cat.all()[0]
	    allcategories = course.cat.all()
	    categories_all=""
	    for category in allcategories:
		categories_all = categories_all + category.name + ", "
	
	    if categories_all:
	        categories.append(categories_all[:-2])
	    else:
		categories.append(None)
	except:
	    categories.append(None)
	
    data = {}
    data['object_list'] = courses
    data['object_list'] = zip(courses,publisher_details)

    courses_as_json = serializers.serialize('json',courses)
    courses_as_json = json.loads(courses_as_json)
    courses_as_json = zip(courses_as_json, publisher_details, categories)

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
    #packages = Entry.objects.all()
    packages = Entry.objects.filter(publisher=request.user, success="YES")
    packages = Entry.objects.filter(success="YES", publisher__in=\
		User.objects.filter(pk__in=User_Organisations.objects.filter(\
			organisation_organisationid=organisation).values_list(\
						'user_userid', flat=True)))


    teacher_role = Role.objects.get(pk=5)
    student_role = Role.objects.get(pk=6)

    students = User.objects.filter(pk__in=User_Organisations.objects.\
			filter(organisation_organisationid=organisation).\
			values_list('user_userid', flat=True)).filter(\
				pk__in=User_Roles.objects.filter(\
					role_roleid=student_role).\
					values_list('user_userid',\
							 flat=True))

    students = User.objects.filter(pk__in=User_Organisations.objects.\
                        filter(organisation_organisationid=organisation).\
                        values_list('user_userid', flat=True))

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
	categoryids=post.getlist('brand')
    	course_count = Course.objects.filter(name=course_name).count()
        if course_count == 0:
                print("Creating the Course..")
                course_name=post['course_name']
                course_desc=post['course_desc']
		#course_category=post['course_category']
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
		course = Course(name=course_name,\
			     description=course_desc, publisher=course_publisher,\
				 organisation=course_organisation)
		cover = request.FILES.get('cover')
		print("cover:")
		print(cover)
		if cover:
		    course.cover = cover
		course.save()
	
		for categoryid in categoryids:
		    category = Categories.objects.get(id=categoryid)
		    course.cat.add(category)

		course.save()

                print("Mapping packages with course..")

		for everypackageid in packageidspicklist:
			currentpackage = Entry.objects.get(pk=everypackageid)
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
    allpackages = Entry.objects.filter(\
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
    if request.method == 'POST':
        post = request.POST;
        print("Going to update the assigned packages..")
        packagesidspicklist=request.POST.getlist('target')
        print(packagesidspicklist)
        if packagesidspicklist:
		print("There is something selected for packages")
		course.packages.clear()
		assignedclear = course.packages.all();
		for everypackageid in packagesidspicklist:
			currentpackage = Entry.objects.get(pk=everypackageid)
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

   	print("Going to all the categories")
	categoryids = request.POST.getlist('brand')
        for categoryid in categoryids:
	    category = Categories.objects.get(id=categoryid)
	    if category not in course.cat.all():
	        course.cat.add(category)
	        course.save()

	try:
	    new_cover = request.FILES['cover']
	    print("New Cover: " )
	    print(new_cover)
	    course.cover = new_cover
	    course.save()
	except:
	    print("No new cover specified.")
	
	    
        return redirect('managecourses')
    return render(request, template_name, {'form':form, 'all_students':allstudents,\
		 'assigned_students':assignedstudents,'all_packages':allpackages,\
		'assigned_packages':assignedpackages, 'all_allclasses':allallclasses,\
		 'assigned_allclasses':assignedallclasses})

def allsubcategories(request, pk):
    print(pk)
    try:
        all_categories = Categories.objects.filter(parent_id = pk)
        json_allcategories = simplejson.dumps( [{'id': o.id,
                           'name': o.name,
                            } for o in all_categories] )
        return HttpResponse(json_allcategories, mimetype="application/json")
    except:
        return HttpResponse(None)

def allrootcategories(request):
    try:
        all_categories = Categories.objects.filter(parent_id = 0)
        json_allcategories = simplejson.dumps( [{'id': o.id,
                           'name': o.name,
                            } for o in all_categories] )
        return HttpResponse(json_allcategories, mimetype="application/json")
    except:
        return HttpResponse(None)

"""
f delete(request, pk, template_name='myapp/package_confirm_delete.html'):
    document = get_object_or_404(Entry, pk=pk)
    if request.method=='POST':
        if request.user == document.publisher:
            document.delete()
        else:
            print("Only the publisher can delete the block")
            return redirect('manage')
        return redirect('manage')
    return render(request, template_name, {'object':document})
"""

# Create your views here.
