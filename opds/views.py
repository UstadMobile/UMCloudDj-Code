import base64
from functools import wraps
from django.conf import settings
from django.contrib.auth import authenticate

from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib import auth
from django.template import RequestContext
from uploadeXe.models import Package as Document
from uploadeXe.models import Course
from uploadeXe.models import Ustadmobiletest
from uploadeXe.models import Invitation

from uploadeXe.models import Role
from uploadeXe.models import User_Roles
from django.forms import ModelForm
from organisation.models import Organisation
from organisation.models import UMCloud_Package
from organisation.models import User_Organisations
from organisation.models import Organisation_Code
from users.models import UserProfile
from allclass.models import Allclass
from school.models import School
from django import forms
from uploadeXe.views import ustadmobile_export
#from uploadeXe.views import grunt_course

from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
import datetime
import time
import os
import urllib
import urllib2, base64, json
import glob #For file ^VS 130420141454
from uploadeXe.models import Ustadmobiletest
import simplejson
from django.conf import settings
from django.db.models import Q
import random
import commands #Added for getting current location 24092014
from xml.dom import minidom
from lxml import etree
import xml.etree.ElementTree as ET
import hashlib
import zipfile
from django.core.mail import send_mail
import socket
import logging
from django.utils.datastructures import MultiValueDictKeyError
from random import randrange

logger = logging.getLogger(__name__)

opds_xml_header="<?xml version=\"1.0\" encoding=\"UTF-8\"?> \n\
    <feed xmlns=\"http://www.w3.org/2005/Atom\" \n\
      xmlns:dc=\"http://purl.org/dc/terms/\" \n\
      xmlns:opds=\"http://opds-spec.org/2010/catalog\">"

def get_public_xml_snippet(request):
    py_time_now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
    public_opds_xml_snippet = "<entry>\n\
			<title>Public Library</title> \n\
                        <link rel=\"http://opds-spec.org/sort/public\" \n\
                              href=\"/opds/public/\" \n\
                              type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>\n\
			<updated>"+py_time_now+"</updated>\n\
    			<id>http://umcloud1.ustadmobile.com/opds/public/</id> \n\
    			<content type=\"text\">Public courses from UMCloud</content> \n\
    			</entry>"
    return public_opds_xml_snippet

def get_author_xml_snippet(user):
    author_opds_xml_snippet = "<author>\n\
	<name>" + user.first_name + " " + user.last_name + "</name> \n\
	<uri>/user/" + str(user.id) + "</uri>\n\
	</author>"
    return author_opds_xml_snippet

"""
The opds root view. 
"""
#@login_required(login_url='/login/')
@csrf_exempt
def root_view(request):
    print("Hello there")
    #if request['headers'].has_key('Authorization'):
    if 'HTTP_AUTHORIZATION' in request.META:
        #auth = request['headers']['Authorization'].split()
	auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            if auth[0].lower() == 'basic':
                # Currently, only basic http auth is used.
                uname, passwd = base64.b64decode(auth[1]).split(':')
                user = authenticate(username=uname, password=passwd)
		logger.info('OPDS Login request coming from outside ()')
        	logger.info("Username;")
        	logger.info(uname)

		if user is None:
		    authresponse = HttpResponse(status=401)
            	    authresponse.write("Authentication failed for user: " + str(uname))
            	    return authresponse
	    else:
		logger.info("Something wrong with basic authentication")
		authresponse = HttpResponse(status=401)
		authresponse.write("Something wrong with basic authentication")
		return authresponse
	else:
	    logger.info("Something wrong with getting basic authentication")
            authresponse = HttpResponse(status=401)
            authresponse.write("Something wrong with getting basic authentication")
            return authresponse

	
	login(request, user)
        print("Successful login")
	py_time_now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
	xmlreturn =opds_xml_header

	xmlreturn += "  <id>http://umcloud1.ustadmobile.com/opds/</id>"

  	xmlreturn += "  <link rel=\"self\""
	xmlreturn += "        href=\"/opds/\""
	xmlreturn += "        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

	xmlreturn += "  <link rel=\"start\""
        xmlreturn += "        href=\"/opds/\""
        xmlreturn += "        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

	xmlreturn += "<title>OPDS Catalog Root</title>"
	xmlreturn += "<updated>"+py_time_now+"</updated>"
	xmlreturn += "<author><name></name><uri></uri></author>"

	xmlreturn += "<entry>"
	xmlreturn += "<title>" + user.first_name + " " + user.last_name + "'s Assigned Courses</title>"
        xmlreturn += "<link rel=\"shelf\" href=\"/opds/assigned_courses/\" type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"
	xmlreturn += "<updated>"+py_time_now+"</updated>"
	xmlreturn += "<id>http://umcloud1.ustadmobile.com/opds/assigned_courses/?userid=" + str(user.id) + "</id>"
        xmlreturn += "<content type=\"text\">All of " + user.first_name + " " + user.last_name + "'s assigned courses</content>"
	xmlreturn += "</entry>"

	xmlreturn += get_public_xml_snippet(request)
	
	xmlreturn += "</feed>"
	authresponse = HttpResponse(status=200)
        authresponse.write(xmlreturn)
        return authresponse
    else:
	logger.info("No authentication given")
	authresponse = HttpResponse(status=401)
	authresponse.write("Basic Authentication not present in request.")
	return authresponse

@login_required(login_url='/opds/')
def assigned_courses(request):
    try:
        user=request.user
    except:
	print("Not loggedn in or unknown user")
	authresponse = HttpResponse(status=401)
        authresponse.write("Not logged in or unknown user.")
	return authresponse
    else:
        if user is not None:
	    username=user.username

	    xmlreturn = opds_xml_header

	    xmlreturn += "<id>http://umcloud1.ustadmobile.com/opds/assigned_course/?userid="+str(request.user.id)+"</id>"

	    xmlreturn += "<link rel=\"start\"\n\
                href=\"/opds/\"\n\
                type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>\n"

	    xmlreturn += "<link rel=\"self\"\n\
		href=\"/opds/assigned_courses/\"\n\
		type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

  	    xmlreturn += "<title>" + user.first_name + " " + user.last_name + "'s (" + user.username + ") assigned courses</title>"
	    py_time_now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
   	    xmlreturn += "<updated>" + py_time_now + "</updated>"
	    xmlreturn += get_author_xml_snippet(request.user)


            #xmlreturn+="<getassignedcourseids><username>"+username+"</username>"
            organisation = User_Organisations.objects.get(user_userid=user).organisation_organisationid;
            #Check and get list of courses..
            #we first get all courses from the user's organisation
            allorgcourses = Course.objects.filter(organisation=organisation)
            alluserclasses = Allclass.objects.filter(students__in=[user])
            matchedcourses=Course.objects.filter(Q(organisation=organisation, students__in=[user]) | Q(organisation=organisation, allclasses__in=alluserclasses))
            assigned_course_ids=[]
            assigned_course_packages=[]
            assigned_course_packageids=[]
            if matchedcourses:      #If there are matched courses
                for everycourse in matchedcourses:
		    xmlreturn += "\n"
                    xmlreturn += "<entry>"
		    xmlreturn += "<title>"+everycourse.name+"</title>"

		    xmlreturn += "<link rel=\"http://opds-spec.org/acquisition\"\n\
			href=\"/opds/course/?id=" + str(everycourse.tincanid) +'/'+ str(everycourse.id) + "\" \n\
			type=\"application/atom+xml;profile=opds-catalog;kind=acquisition\"/>"

		    xmlreturn += "<id>" + str(everycourse.tincanid) + "/" + str(everycourse.id) + "</id>"
		    xmlreturn += "<updated>" + str(everycourse.upd_date.strftime('%Y-%m-%dT%H:%M:%SZ')) + "</updated>"
		    xmlreturn += get_author_xml_snippet(everycourse.publisher)
		    xmlreturn += "<content type=\"text\">" + everycourse.description + "</content>"
		    xmlreturn += "</entry>"

                xmlreturn+="</feed>"

                authresponse = HttpResponse(status=200)
                authresponse.write(xmlreturn)
                return authresponse
            else:
		xmlreturn += "</feed>"
		authresponse = HttpResponse(status=200)
		authresponse.write(xmlreturn)
		return authresponse
		
                #authresponse = HttpResponse(status=404)
                #authresponse.write("No courses found for username: " + username)
	    

@csrf_exempt
def get_course_blocks(request):
        if request.method == "POST":
            logger.info("Course list request coming from \
                        outside (UstadMobile?)")
            username = request.POST.get('username', False)
            password = request.POST.get('password', False)
            try:
                courseid = request.POST.get('courseid', False)
                coursetincanprefix=courseid.rsplit('/',1)[0]
                coursepk=courseid.rsplit('/',1)[1]
            except:
                authresponse=HttpResponse(status=500)
                authresponse.write("The course ID is either not given or improper. It should be like: http:/a.b.c/d/e/42")
                return authresponse

            logger.info("For user: " + username)
            #Authenticate the user
            user = authenticate(username=\
                        request.POST['username'],\
                 password=request.POST['password'])
            if user is None:
                authresponse=HttpResponse(status=401)
                authresponse.write("Unable to authorise user: " + str(username))
                return authresponse


            if user is not None:
                organisation = User_Organisations.objects.get(\
                                user_userid=user)\
                                .organisation_organisationid;
                allorgcourses = Course.objects.filter(organisation=organisation)
                alluserclasses = Allclass.objects.filter(students__in=[user])
                matched_courses=Course.objects.filter(Q(organisation=\
                        organisation, students__in=[user]) | \
                            Q(organisation=organisation, \
                                allclasses__in=alluserclasses))
                try:
                    course=Course.objects.get(id=coursepk, organisation=organisation, tincanid=coursetincanprefix)
                except:
                    authresponse=HttpResponse(status=500)
                    authresponse.write("Course id does not exist (Is your tincanprefix and pk right?) or does not belong to your organisation")
                    return authresponse
                else:
                    all_blocks_in_course=course.packages.all()
                    json_blocks = simplejson.dumps([
                        {
                          o.id:{
                            'title':o.name
                              }
                        }for o in all_blocks_in_course])
                    json_blocks = simplejson.dumps({
                        "title":course.name,
                        "description":course.description,
                        "id":str(course.tincanid)+'/'+str(course.id),
                        "blocks":[
                        {
                          "id":o.tincanid+'/'+o.elpid,
                          "title":o.name
                        }for o in all_blocks_in_course]})

                    return HttpResponse(json_blocks, mimetype="application/json")

        else:
            authresponse = HttpResponse(status=500)
            authresponse.write("Not a POST request. Assigned Block retrival for course failed.")
            return authresponse


@login_required(login_url='/opds/')
def get_course(request):
    try:
        user=request.user
    except:
        print("Not loggedn in or unknown user")
        authresponse = HttpResponse(status=401)
        authresponse.write("Not logged in or unknown user.")
        return authresponse
    else:
        if user is not None:
	    try:
                courseid = request.GET.get('id', False)
		print("Course id given is: " + courseid)
                coursetincanprefix=courseid.rsplit('/',1)[0]
                coursepk=courseid.rsplit('/',1)[1]
		print("TinCan Prefix: " + coursetincanprefix + " pk: " + coursepk)
            except:
		print("The course id: " + str(request.GET.get('id', False)) + " was invalid")
                authresponse=HttpResponse(status=500)
                authresponse.write("The course ID is either not given or improper. It should be like: http:/a.b.c/d/e/42")
                return authresponse

            username=user.username

            xmlreturn = opds_xml_header

            xmlreturn += "<id>http://umcloud1.ustadmobile.com/opds/course/?id="+str(courseid)+"</id>"

            xmlreturn += "<link rel=\"start\"\n\
                href=\"/opds/\"\n\
                type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>\n"

            xmlreturn += "<link rel=\"self\"\n\
                href=\"/opds/assigned_courses/\"\n\
                type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"
	    
	    xmlreturn += "<link rel=\"http://umcloud1.ustadmobile.com/opds/\"\n\
                href=\"/course/?id="+str(courseid)+"\"\n\
                type=\"application/atom+xml;profile=opds-catalog;kind=acquisition\"/>"

	    """
	    Course details 
	    """
	    organisation = User_Organisations.objects.get(\
                                user_userid=user)\
                                .organisation_organisationid;
            allorgcourses = Course.objects.filter(organisation=organisation)
            alluserclasses = Allclass.objects.filter(students__in=[user])
            matched_courses=Course.objects.filter(Q(organisation=\
                        organisation, students__in=[user]) | \
                            Q(organisation=organisation, \
                                allclasses__in=alluserclasses))
            try:
                course=Course.objects.get(id=coursepk, organisation=organisation, tincanid=coursetincanprefix)
		if course is not None:
		    xmlreturn += "\n<title>" + course.name + "</title>\n"
		    xmlreturn += "<updated></updated>"
		    xmlreturn += get_author_xml_snippet(course.publisher)
		    xmlreturn += "\n"
            except:
                authresponse=HttpResponse(status=500)
                authresponse.write("Course id does not exist (Is your tincanprefix and pk right?) or does not belong to your organisation")
                return authresponse
            else:
                all_blocks_in_course=course.packages.all()
		for o in all_blocks_in_course:
		    url = o.url;
		    if url.endswith(".html"):
			exefilepath = str(o.exefile)
			print(exefilepath)
			if exefilepath.endswith(".epub") or exefilepath.endswith(".elp"):
			    epubname = exefilepath.rsplit(".",2)[1]
			    url = url.rsplit("/",1)[0] + "/" + epubname + ".epub"
			    url = url.rsplit("/",1)[0] + ".epub"
		    xmlreturn += "<entry>\n"
		    xmlreturn += "<title>" + o.name +"</title>\n"
		    xmlreturn += "<id>"+o.tincanid+'/'+o.elpid+"</id>\n"
		    xmlreturn += "<updated>"+str(o.upd_date.strftime('%Y-%m-%dT%H:%M:%SZ'))+"</updated>\n"
		    xmlreturn += get_author_xml_snippet(o.publisher)
		    xmlreturn += "\n"
		    xmlreturn += "<dc:language>en</dc:language>"
		    xmlreturn += "<dc:issued></dc:issued>\n"

		    xmlreturn += "<category\n\
				scheme=\"http://www.bisg.org/standards/bisac_subject/index.html\"\
              			term=\"TESTING\"\
              			label=\"TESTING\"/>\n"
		    xmlreturn += "<summary>" + o.name + "'s description" + "</summary>\n"
		    xmlreturn += "<link rel=\"http://opds-spec.org/acquisition\"\n \
			href=\"" + url + "\"\n\
          		type=\"application/epub+zip\"/>\n"
		
		    xmlreturn += "</entry>\n"
		

                #return HttpResponse(json_blocks, mimetype="application/json")
		#return None



            authresponse = HttpResponse(status=200)
            authresponse.write(xmlreturn)
            return authresponse


# Create your views here.
