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
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from uploadeXe.models import Package as Document
from uploadeXe.models import Course
from uploadeXe.models import Ustadmobiletest
from uploadeXe.models import Invitation

from uploadeXe.models import Role
from uploadeXe.models import User_Roles
from uploadeXe.models import Categories
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
from uploadeXe.views import get_package_url
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
from os.path import basename

HOST_NAME = getattr(settings, "HOST_NAME", None)

logger = logging.getLogger(__name__)

opds_xml_header="<?xml version=\"1.0\" encoding=\"UTF-8\"?> \n\
    <feed xmlns=\"http://www.w3.org/2005/Atom\" \n\
      xmlns:dc=\"http://purl.org/dc/terms/\" \n\
      xmlns:opds=\"http://opds-spec.org/2010/catalog\">"

def get_opensearch_description():
    opensearch_desc = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n\
	<OpenSearchDescription xmlns=\"http://a9.com/-/spec/opensearch/1.1/\">\n\
	  <ShortName>Ustad Mobile Search</ShortName>\n\
	    <Description>Search Ustad Mobile's OPDS Catalog.</Description>\n\
	      <Url type=\"application/atom+xml\"\n\
	        template=\"" + HOST_NAME + "/opds/public/opensearch?q={searchTerms}&amp;author={atom:author}\"/>\n\
		  </OpenSearchDescription>\n"
    return opensearch_desc

def get_search_xml_snippet():
    search_snippet = "<link\n\
			rel=\"search\"\n\
			type=\"application/opensearchdescription+xml\"\n\
			href=\"" + HOST_NAME + "/opds/public/opensearch\"/>"
    return search_snippet

def get_public_xml_snippet(request):
    py_time_now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
    public_opds_xml_snippet = "<entry>\n\
			<title>Public Library</title> \n\
                        <link rel=\"http://opds-spec.org/sort/public\" \n\
                              href=\"/opds/public/providers/\" \n\
                              type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>\n\
			<updated>"+py_time_now+"</updated>\n\
    			<id>" + HOST_NAME + "/opds/public/</id> \n\
    			<content type=\"text\">Public courses from UMCloud</content> \n\
    			</entry>"
    return public_opds_xml_snippet

def get_author_xml_snippet(user):
    author_opds_xml_snippet = "<author>\n\
	<name>" + user.first_name + " " + user.last_name + "</name> \n\
	<uri>/user/" + str(user.id) + "</uri>\n\
	</author>"
    return author_opds_xml_snippet

def login_basic_auth(req):
    if 'HTTP_AUTHORIZATION' in req.META:
        #auth = request['headers']['Authorization'].split()
        auth = req.META['HTTP_AUTHORIZATION'].split()
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
                    return False, authresponse
		else:
		    authresponse = HttpResponse(status=200)
		    authresponse.write("Success in login." + str(uname))
		    return True, user
		    #return True, authresponse
		    
            else:
                logger.info("Something wrong with basic authentication")
                authresponse = HttpResponse(status=401)
                authresponse.write("Something wrong with basic authentication")
                return False, authresponse
        else:
            logger.info("Something wrong with getting basic authentication")
            authresponse = HttpResponse(status=401)
            authresponse.write("Something wrong with getting basic authentication")
            return False, authresponse
    else:
	logger.info("Basic Authentication not presen in request.")
	authresponse = HttpResponse(status=401)
	authresponse.write("No Http Basic Authentication found in the request. Please check the request. Your app might be faulty.")
	return False, authresponse

    logger.info("No idea, something went wrong. Couldnt even scan the request. Check the code.")
    authresponse = HttpResponse(status=500)
    authresponse.write("Something went wrong, not too sure. Check logs..")
    return False, authresponse


"""
The opds root view. 
"""
#@login_required(login_url='/login/')
@csrf_exempt
def root_view(request):
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
	py_time_now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
	xmlreturn =opds_xml_header

	xmlreturn += "  <id>" + HOST_NAME + "/opds/</id>"

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
	xmlreturn += "<title>My Assigned Courses</title>"
        xmlreturn += "<link rel=\"shelf\" href=\"/opds/assigned_courses/\" type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"
	xmlreturn += "<updated>"+py_time_now+"</updated>"
	xmlreturn += "<id>" + HOST_NAME + "/opds/assigned_courses/?userid=" + str(user.id) + "</id>"
        xmlreturn += "<content type=\"text\">All of " + user.first_name + " " + user.last_name + "'s assigned courses</content>"
	xmlreturn += "\n"
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

#@login_required(login_url='/opds/')
@csrf_exempt
def assigned_courses(request):
    state, authresponse = login_basic_auth(request)
    if state == False:
	return authresponse
    if state == True:
	request.user = authresponse
    try:
        user=request.user
    except:
	authresponse = HttpResponse(status=401)
        authresponse.write("Not logged in or unknown user.")
	return authresponse
    else:
        if user is not None:
	    username=user.username

	    xmlreturn = opds_xml_header

	    xmlreturn += "<id>" + HOST_NAME + "/opds/assigned_course/?userid="+str(request.user.id)+"</id>"

	    xmlreturn += "<link rel=\"start\"\n\
                href=\"/opds/\"\n\
                type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>\n"

	    xmlreturn += "<link rel=\"self\"\n\
		href=\"/opds/assigned_courses/\"\n\
		type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

  	    xmlreturn += "<title>" + user.first_name + " " + user.last_name + "'s (" + user.username + ") assigned courses</title>"
	    py_time_now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
   	    xmlreturn += "<updated>" + py_time_now + "</updated>"
	    xmlreturn += "\n"
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
	    #Remove duplicates:
	    matchedcourses = list(set(matchedcourses))
            if matchedcourses:      #If there are matched courses
                for everycourse in matchedcourses:
		    xmlreturn += "\n"
                    xmlreturn += "<entry>"
		    xmlreturn += "<title>"+everycourse.name+"</title>"

		    xmlreturn += "<link rel=\"subsection\"\n\
			href=\"/opds/course/?id=" + str(everycourse.tincanid) +'/'+ str(everycourse.id) + "\" \n\
			type=\"application/atom+xml;profile=opds-catalog;kind=acquisition\"/>"

		    xmlreturn += "<id>" + str(everycourse.tincanid) + "/" + str(everycourse.id) + "</id>"
		    xmlreturn += "<updated>" + str(everycourse.upd_date.strftime('%Y-%m-%dT%H:%M:%SZ')) + "</updated>"
		    xmlreturn += get_author_xml_snippet(everycourse.publisher)
		    xmlreturn += "<content type=\"text\">" + everycourse.description + "</content>"
		    if everycourse.cover:
			appLocation = (os.path.dirname(os.path.realpath(__file__)))
                        serverlocation=appLocation+'/../'
                        mainappstring = "UMCloudDj/"
			cover_file = serverlocation + mainappstring + "/media/" + str(everycourse.cover)
			cover_href = "/media/" + str(everycourse.cover)
			#Can use the above to verify that the file image exists..
			#xmlreturn += "<link rel=\"http://opds-spec.org/image/thumbnail\" "
			xmlreturn += "<link rel=\"http://www.ustadmobile.com/catalog/image/background\" "
			xmlreturn += "href=\"" + cover_href + "\" "
			xmlreturn += "type=\"image/png\" />"
		    xmlreturn += "\n"
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
	    

#@login_required(login_url='/opds/')
def get_course(request):
    state, authresponse = login_basic_auth(request)
    if state == False:
        return authresponse
    if state == True:
        request.user = authresponse

    try:
        user=request.user
    except:
        logger.info("Not loggedn in or unknown user")
        authresponse = HttpResponse(status=401)
        authresponse.write("Not logged in or unknown user.")
        return authresponse
    else:
        if user is not None:
	    try:
                courseid = request.GET.get('id', False)
                coursetincanprefix=courseid.rsplit('/',1)[0]
                coursepk=courseid.rsplit('/',1)[1]
            except:
                authresponse=HttpResponse(status=500)
                authresponse.write("The course ID is either not given or improper. It should be like: http:/a.b.c/d/e/42")
                return authresponse

            username=user.username

            xmlreturn = opds_xml_header

            xmlreturn += "<id>"+str(courseid)+"</id>"

            xmlreturn += "<link rel=\"start\"\n\
                href=\"/opds/\"\n\
                type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>\n"

            xmlreturn += "<link rel=\"self\"\n\
                href=\"/opds/course/?id="+str(courseid)+"\"\n\
                type=\"application/atom+xml;profile=opds-catalog;kind=acquisition\"/>"


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
		    xmlreturn += "<updated>" + str(course.upd_date.strftime('%Y-%m-%dT%H:%M:%SZ')) + "</updated>"
		    xmlreturn += get_author_xml_snippet(course.publisher)
		    xmlreturn += "\n"

            except:
                authresponse=HttpResponse(status=500)
                authresponse.write("Course id does not exist (Is your tincanprefix and pk right?) or does not belong to your organisation")
                return authresponse
            else:
                all_blocks_in_course=course.packages.all()
		for o in all_blocks_in_course:
		    entry = o;
		    xmlreturn += "<entry>\n"
                    xmlreturn += "<title>" + o.name +"</title>\n"
                    #xmlreturn += "<id>"+o.tincanid+'/'+o.elpid+"</id>\n" #Changed 16th MArch 2017
		    xmlreturn += "<id>"+o.elpid+"</id>\n"
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

		    try:
		        for acquisition_link in entry.acquisitionlink.all().filter(active=True):
			    print("In Acquisition Link : " + str(acquisition_link.id))
			    print("url is : " + str(acquisition_link.exefile))
			    url = str(acquisition_link.exefile)
			    url = url.replace('&', '&amp;')
			    xmlreturn += "<link rel=\"http://opds-spec.org/acquisition\"\n \
                                href=\"" + "/media/" + url + "\"\n\
                                    type=\"" + acquisition_link.mimetype + "\"/>\n"

			    print("Figuring out preview_path")
			    preview_path = acquisition_link.preview_path
			    print(preview_path)
			    preview_path = preview_path.replace('&','&amp;')
	
			    micro_edition_url = ""
			    

			    appLocation = (os.path.dirname(os.path.realpath(__file__)))
    			    serverlocation=appLocation+'/../'
    			    mainappstring = "UMCloudDj/"

		            if str(acquisition_link.exefile).lower().endswith('.epub') and o.micro_edition:
			        dst=os.path.splitext(basename(url))[0]
                                if dst.strip():
                                    print("Exists!")
                                    micro_edition_url = os.path.dirname(url) + "/" +  dst + "_micro.epub"
				    print(micro_edition_url)
				#Check if micro_edition_url file exists:
			        micro_edition_url = micro_edition_url.replace('&','&amp;')
				
				micro_file = serverlocation + mainappstring + "/media/" + micro_edition_url
				print("Checking file: " + micro_file)
				if os.path.isfile(micro_file):
					print("FIle Exists!")
					print('/media/'+micro_edition_url);
				 	xmlreturn += "<link rel=\"http://opds-spec.org/acquisition\"\n \
                                    		href=\"" + micro_edition_url + "\"\n\
                                    			type=\"application/epub+zip;x-umprofile=micro\"/>\n"
				else:
					print("File Not exists!");

			    if str(acquisition_link.exefile).lower().endswith('.epub') or \
				str(acquisition_link.exefile).lower().endswith('.epub'):
				if preview_path != None and preview_path != "":
                                    xmlreturn += "<link rel=\"http://ustadmobile.com/epubrunner\"\n\
                                       href=\"" + preview_path + "\" \n\
                                        type=\"text/html;profile=opds-catalog;kind=acquisition\"/>"	
			thumbnail_href = None
                    	if o.thumbnail:
                            appLocation = (os.path.dirname(os.path.realpath(__file__)))
                            serverlocation=appLocation+'/../'
                            mainappstring = "UMCloudDj/"
                            thumbnail_file = serverlocation + mainappstring + "/media/" + str(o.thumbnail)
                            #Can use the above to verify that the file exists..

                            thumbnail_href = "/media/" + str(o.thumbnail)
                            xmlreturn += "<link rel=\"http://opds-spec.org/image/thumbnail\" "
                            xmlreturn += "href=\"" + thumbnail_href + "\" "
                            xmlreturn += "type=\"image/png\" />"

		    except Exception, e:
			print("Error in Acquiring links.")
			print(str(e))
		    xmlreturn += "\n"
		    xmlreturn += "</entry>\n"

	    xmlreturn += "</feed>"

            authresponse = HttpResponse(status=200)
            authresponse.write(xmlreturn)
            return authresponse



@csrf_exempt
def public_view(request):
    if True:
        py_time_now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
        xmlreturn =opds_xml_header

        xmlreturn += "  <id>" + HOST_NAME + "/opds/public</id>"

        xmlreturn += "  <link rel=\"self\""
        xmlreturn += "        href=\"/opds/public/\""
        xmlreturn += "        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

        xmlreturn += "  <link rel=\"start\""
        xmlreturn += "        href=\"/opds/public/\""
        xmlreturn += "        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

	xmlreturn += get_search_xml_snippet()

        xmlreturn += "<title>Ustad Mobile Public OPDS Catalog</title>"
        #Should be replaced by actual update time not current.
        xmlreturn += "<updated>"+py_time_now+"</updated>"
        xmlreturn += "<author><name>Ustad Mobile Public</name><uri>http://www.ustadmobile.com</uri></author>"

        xmlreturn += "<entry>"
        xmlreturn += "<title>Recent Courses</title>"
        xmlreturn += "<link href=\"/opds/public/recent\" type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"
        xmlreturn += "<updated>"+py_time_now+"</updated>"
        xmlreturn += "<id></id>"
        xmlreturn += "<content type=\"text\">The most recent courses from Ustad Mobile in the last month</content>"
	xmlreturn += "\n"
        xmlreturn += "</entry>"

        xmlreturn += "<entry>"
        xmlreturn += "<title>Featured Courses</title>"
        xmlreturn += "<link href=\"/opds/public/featured\" type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"
        xmlreturn += "<updated>"+py_time_now+"</updated>"
        xmlreturn += "<id></id>"
        xmlreturn += "<content type=\"text\">Our top featured Ustad Mobile courses picked by our Editors</content>"
	xmlreturn +="\n"
        xmlreturn += "</entry>"

        xmlreturn += "<entry>"
        xmlreturn += "<title>Courses by Categories</title>"
        xmlreturn += "<link href=\"/opds/public/categories\" type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"
        xmlreturn += "<updated>"+py_time_now+"</updated>"
        xmlreturn += "<id></id>"
        xmlreturn += "<content type=\"text\">Courses by categories.</content>"
	xmlreturn += "\n"
        xmlreturn += "</entry>"

        xmlreturn += "<entry>"
        xmlreturn += "<title>Courses in Aplhabetical order</title>"
        xmlreturn += "<link href=\"/opds/public/alphabetical\" type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"
        xmlreturn += "<updated>"+py_time_now+"</updated>"
        xmlreturn += "<id></id>"
        xmlreturn += "<content type=\"text\">Courses by categories.</content>"
	xmlreturn += "\n"
        xmlreturn += "</entry>"

        xmlreturn += "</feed>"
        authresponse = HttpResponse(status=200)
        authresponse.write(xmlreturn)
        return authresponse
    else:
        logger.info("No authentication given")
        authresponse = HttpResponse(status=401)
        authresponse.write("Basic Authentication not present in request.")
        return authresponse

@csrf_exempt
def public_providers(request):
    py_time_now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
    xmlreturn =opds_xml_header
    xmlreturn += "  <id>" + HOST_NAME + "/opds/public/providers</id>"

    xmlreturn += "  <link rel=\"self\""
    xmlreturn += "        href=\"/opds/public/providers/\""
    xmlreturn += "        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

    xmlreturn += "  <link rel=\"start\""
    xmlreturn += "        href=\"/opds/\""
    xmlreturn += "        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

    xmlreturn += get_search_xml_snippet()

    xmlreturn += "<title>All Public Providers</title>"
    #Should be replaced by actual update time not current. Actually IS current time of request.
    xmlreturn += "<updated>"+py_time_now+"</updated>"
    xmlreturn += "<author><name>Ustad Mobile Public</name><uri>http://www.ustadmobile.com</uri></author>"

    all_public_providers = Organisation.objects.filter(public = True);
    for provider in all_public_providers:
        xmlreturn += "<entry>"
        xmlreturn += "<title>" + provider.organisation_name + "</title>"
        xmlreturn += "<link href=\"/opds/public/providers/" + str(provider.id) + "\" type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"
        xmlreturn += "<updated>"+py_time_now+"</updated>"
        xmlreturn += "<id></id>"
        xmlreturn += "<content type=\"text\">Categories part of " + provider.organisation_name + " provider .</content>"
	xmlreturn += "\n"
        xmlreturn += "</entry>"

    xmlreturn += "</feed>"
    authresponse = HttpResponse(status=200)
    authresponse.write(xmlreturn)
    return authresponse

@csrf_exempt
def public_providers_nocategories(request, pk):
    return public_providers_categories(request, pk, None)

@csrf_exempt
def public_providers_categories(request, pk, ct):
    if pk != "" and pk != None and ct == None or ct == "":

        py_time_now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
        xmlreturn =opds_xml_header
        provider = Organisation.objects.get(pk=pk);

        xmlreturn += "  <id>" + HOST_NAME + "/opds/public/providers/"+pk+"</id>"

        xmlreturn += "  <link rel=\"self\""
        xmlreturn += "        href=\"/opds/public/providers/"+pk+"\""
        xmlreturn += "        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

        xmlreturn += "  <link rel=\"start\""
        xmlreturn += "        href=\"/opds/public/\""
        xmlreturn += "        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

        xmlreturn += get_search_xml_snippet()

        xmlreturn += "<title>Categories of Provider: " + provider.organisation_name + " </title>"
        xmlreturn += "<updated>"+py_time_now+"</updated>"
        xmlreturn += "<author><name>Ustad Mobile Public</name><uri>http://www.ustadmobile.com</uri></author>"

        all_provider_courses = Course.objects.filter(
            success="YES", publisher__in=User.objects.filter(
                pk__in=User_Organisations.objects.filter(
                    organisation_organisationid=provider
                ).values_list('user_userid', flat=True)
            )
        )
        all_provider_categories = []
        for every_provider_course in all_provider_courses:
            every_provider_course_categories = every_provider_course.cat.all()
            for every_category in every_provider_course_categories:
		if every_category not in all_provider_categories:
                    all_provider_categories.append(every_category)
            
        
        for category in all_provider_categories:
            xmlreturn += "<entry>"
            xmlreturn += "<title>" + category.name + "</title>"
            xmlreturn += "<link href=\"/opds/public/providers/" + str(pk) + "/" + str(category.id) + "\" type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"
            xmlreturn += "<updated>"+py_time_now+"</updated>"
            xmlreturn += "<id></id>"
            xmlreturn += "<content type=\"text\">Courses part of " + category.name + " category. </content>"
	    xmlreturn += "\n"
            xmlreturn += "</entry>"

        
        xmlreturn += "</feed>"
        authresponse = HttpResponse(status=200)
        authresponse.write(xmlreturn)
        return authresponse
    elif (pk != "" and pk != None and ct != "" and ct != None):
        py_time_now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
        xmlreturn =opds_xml_header
        provider = Organisation.objects.get(pk=pk);
        category = Categories.objects.get(pk=ct);

        xmlreturn += "  <id>" + HOST_NAME + "/opds/public/providers/" + pk + "/" + ct + "</id>"

        xmlreturn += "  <link rel=\"self\""
        xmlreturn += "        href=\"/opds/public/providers/"+pk+"\""
        xmlreturn += "        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

        xmlreturn += "  <link rel=\"start\""
        xmlreturn += "        href=\"/opds/public/\""
        xmlreturn += "        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

        xmlreturn += get_search_xml_snippet()

        xmlreturn += "<title>Categories of Provider: " + provider.organisation_name + " </title>"
        xmlreturn += "<updated>"+py_time_now+"</updated>"
        xmlreturn += "<author><name>Ustad Mobile Public</name><uri>http://www.ustadmobile.com</uri></author>"


        all_provider_courses = Course.objects.filter(
            success="YES", publisher__in=User.objects.filter(
                pk__in=User_Organisations.objects.filter(
                    organisation_organisationid=provider
                ).values_list('user_userid', flat=True)
            )
        )
        all_provider_category_courses = []
        for every_provider_course in all_provider_courses:
            if category in every_provider_course.cat.all():
                all_provider_category_courses.append(every_provider_course);
            


        for course in all_provider_category_courses:
            xmlreturn += "<entry>"
            xmlreturn += "<title>" + course.name + "</title>"
            xmlreturn += "<link href=\"/opds/public/course/?id=" + str(course.tincanid) +'/'+ str(course.id) + "\" \n\
                             type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"
            xmlreturn += "<id>" + str(course.tincanid) + "/" + str(course.id) + "</id>"
            xmlreturn += "<updated>" + str(course.upd_date.strftime('%Y-%m-%dT%H:%M:%SZ')) + "</updated>"
            xmlreturn += get_author_xml_snippet(course.publisher)
            xmlreturn += "<content type=\"text\">" + course.description + "</content>"
	    xmlreturn += "\n"
            xmlreturn += "</entry>"

	xmlreturn += "</feed>"
	authresponse = HttpResponse(status=200)
        authresponse.write(xmlreturn)
        return authresponse
    else:
        logger.info("pk is invalid")
        authresponse = HttpResponse(status=401)
        authresponse.write("Invalid ID given.")
        return authresponse


@csrf_exempt
def public_categories_view(request):
    if True:
        py_time_now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
        xmlreturn =opds_xml_header

        xmlreturn += "  <id>" + HOST_NAME + "/opds/public/categories</id>"

        xmlreturn += "  <link rel=\"self\""
        xmlreturn += "        href=\"/opds/public/categories/\""
        xmlreturn += "        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

        xmlreturn += "  <link rel=\"start\""
        xmlreturn += "        href=\"/opds/\""
        xmlreturn += "        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

	xmlreturn += get_search_xml_snippet()

        xmlreturn += "<title>Courses by Categories</title>"
        #Should be replaced by actual update time not current.
        xmlreturn += "<updated>"+py_time_now+"</updated>"
        xmlreturn += "<author><name>Ustad Mobile Public</name><uri>http://www.ustadmobile.com</uri></author>"

        all_categories = Categories.objects.filter(parent_id = 0)
        for category in all_categories:
            xmlreturn += "<entry>"
            xmlreturn += "<title>Category: " + category.name + "</title>"
            xmlreturn += "<link href=\"/opds/public/categories/" + str(category.id) + "\" type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"
            xmlreturn += "<updated>"+py_time_now+"</updated>"
            xmlreturn += "<id></id>"
            xmlreturn += "<content type=\"text\">Courses part of " + category.name + " category.</content>"
	    xmlreturn += "\n"
            xmlreturn += "</entry>"

        xmlreturn += "</feed>"
        authresponse = HttpResponse(status=200)
        authresponse.write(xmlreturn)
        return authresponse
    else:
        logger.info("No authentication given")
        authresponse = HttpResponse(status=401)
        authresponse.write("Basic Authentication not present in request.")
        return authresponse

@csrf_exempt
def public_alphabetical_view(request):
    logger.info("Getting public alphabetical view:")

    try:
        py_time_now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
        xmlreturn =opds_xml_header

        xmlreturn += "  <id>" + HOST_NAME + "/opds/public</id>"

        xmlreturn += "  <link rel=\"self\""
        xmlreturn += "        href=\"/opds/public/\""
        xmlreturn += "        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

        xmlreturn += "  <link rel=\"start\""
        xmlreturn += "        href=\"/opds/public/\""
        xmlreturn += "        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

        xmlreturn += get_search_xml_snippet()

        xmlreturn += "<title>Ustad Mobile Public OPDS Catalog</title>"
        #Should be replaced by actual update time not current.
        xmlreturn += "<updated>"+py_time_now+"</updated>"
        xmlreturn += "<author><name>Ustad Mobile Public Alphabetical</name><uri>http://www.ustadmobile.com</uri></author>"

	all_public_providers = Organisation.objects.filter(public = True)
	for every_provider in all_public_providers:
	    logger.info("This Provider is public: " + str(every_provider.id))

	try:
		all_public_courses = Course.objects.filter(public=True).order_by('name')

		# Shows 20 results per page
    		paginator = Paginator(all_public_courses, 50)
    		page = request.GET.get('page')
    		try:
        	    all_public_courses = paginator.page(page)
    		except PageNotAnInteger:
        	    all_public_courses=paginator.page(1)
    		except EmptyPage:
        	    all_public_courses = paginator.page(paginator.num_pages)


	 	for everycourse in all_public_courses:
                    xmlreturn += "\n"
                    xmlreturn += "<entry>"
                    xmlreturn += "<title>"+everycourse.name+"</title>"

                    xmlreturn += "<link rel=\"subsection\"\n\
                        href=\"/opds/course/?id=" + str(everycourse.tincanid) +'/'+ str(everycourse.id) + "\" \n\
                        type=\"application/atom+xml;profile=opds-catalog;kind=acquisition\"/>"

                    xmlreturn += "<id>" + str(everycourse.tincanid) + "/" + str(everycourse.id) + "</id>"
                    xmlreturn += "<updated>" + str(everycourse.upd_date.strftime('%Y-%m-%dT%H:%M:%SZ')) + "</updated>"
                    xmlreturn += get_author_xml_snippet(everycourse.publisher)
                    xmlreturn += "<content type=\"text\">" + everycourse.description + "</content>"
                    if everycourse.cover:
                        appLocation = (os.path.dirname(os.path.realpath(__file__)))
                        serverlocation=appLocation+'/../'
                        mainappstring = "UMCloudDj/"
                        cover_file = serverlocation + mainappstring + "/media/" + str(everycourse.cover)
                        cover_href = "/media/" + str(everycourse.cover)
                        #Can use the above to verify that the file image exists..
                        #xmlreturn += "<link rel=\"http://opds-spec.org/image/thumbnail\" "
                        xmlreturn += "<link rel=\"http://www.ustadmobile.com/catalog/image/background\" "
                        xmlreturn += "href=\"" + cover_href + "\" "
                        xmlreturn += "type=\"image/png\" />"
                    xmlreturn += "\n"
                    xmlreturn += "</entry>"

                xmlreturn+="</feed>"
	except:
		logger.info("Exception in getting courses for alphabetical view.")
		authresponse = HttpResponse(status=500)
		authresponse.write("Getting courses for alphabetical order failed.")
		return authresponse

	
	authresponse = HttpResponse(status=200)
	authresponse.write(xmlreturn)
	return authresponse
    except Exception as aof:
	logger.info("Exception in getting alphabetical view..")
	
	authresponse = HttpResponse(status=500)
	authresponse.write("Getting alphabetical order failed. " + str(aof))
	return authresponse

    authresponse = HttpResponse(status=200)
    authresponse.write("Under Construction")
    return authresponse

@csrf_exempt
def public_category_view(request, pk):
    if pk != "" and pk != None:

        py_time_now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
        xmlreturn =opds_xml_header

        xmlreturn += "  <id>" + HOST_NAME + "/opds/public/categories/"+pk+"</id>"

        xmlreturn += "  <link rel=\"self\""
        xmlreturn += "        href=\"/opds/public/categories/"+pk+"\""
        xmlreturn += "        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

        xmlreturn += "  <link rel=\"start\""
        xmlreturn += "        href=\"/opds/public/\""
        xmlreturn += "        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"

 	xmlreturn += get_search_xml_snippet()

        xmlreturn += "<title>Courses by Categories</title>"
        #Should be replaced by actual update time not current.
        xmlreturn += "<updated>"+py_time_now+"</updated>"
        xmlreturn += "<author><name>Ustad Mobile Public</name><uri>http://www.ustadmobile.com</uri></author>"

        this_category = Categories.objects.filter(id=pk)
        all_sub_categories = Categories.objects.filter(parent_id = pk)
        for category in all_sub_categories:
            xmlreturn += "<entry>"
            xmlreturn += "<title>Category: " + category.name + "</title>"
            xmlreturn += "<link href=\"/opds/public/categories/" + category.id + "\" type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>"
            xmlreturn += "<updated>"+py_time_now+"</updated>"
            xmlreturn += "<id></id>"
            xmlreturn += "<content type=\"text\">Courses part of " + category.name + " sub-category. (" + this_category.name + " > " + category.name + ")</content>"
	    xmlreturn += "\n"
            xmlreturn += "</entry>"

        all_courses_in_this_category = Course.objects.filter(cat__id=pk, public=True)
        for everycourse in all_courses_in_this_category:
            xmlreturn += "\n"
            xmlreturn += "<entry>"
            xmlreturn += "<title>"+everycourse.name+"</title>"

            xmlreturn += "<link\n\
                href=\"/opds/public/course/?id=" + str(everycourse.tincanid) +'/'+ str(everycourse.id) + "\" \n\
                type=\"applicati/atom+xml;profile=opds-catalog;kind=acquisition\"/>"

            xmlreturn += "<id>" + str(everycourse.tincanid) + "/" + str(everycourse.id) + "</id>"
            xmlreturn += "<updated>" + str(everycourse.upd_date.strftime('%Y-%m-%dT%H:%M:%SZ')) + "</updated>"
            xmlreturn += get_author_xml_snippet(everycourse.publisher)
            xmlreturn += "<content type=\"text\">" + everycourse.description + "</content>"
	    xmlreturn +="\n"
            xmlreturn += "</entry>"

        xmlreturn += "</feed>"
        authresponse = HttpResponse(status=200)
        authresponse.write(xmlreturn)
        return authresponse
    else:
        logger.info("pk is invalid")
        authresponse = HttpResponse(status=401)
        authresponse.write("Invalid ID given.")
        return authresponse


#@login_required(login_url='/opds/')
def get_public_course(request):
    try:
        courseid = request.GET.get('id', False)
        coursetincanprefix=courseid.rsplit('/',1)[0]
        coursepk=courseid.rsplit('/',1)[1]
    except:
        authresponse=HttpResponse(status=500)
        authresponse.write("The course ID is either not given or improper. It should be like: http:/a.b.c/d/e/42")
        return authresponse

    xmlreturn = opds_xml_header

    xmlreturn += "<id>"+str(courseid)+"</id>"

    xmlreturn += "<link rel=\"start\"\n\
        href=\"/opds/\"\n\
        type=\"application/atom+xml;profile=opds-catalog;kind=navigation\"/>\n"

    xmlreturn += "<link rel=\"self\"\n\
        href=\"/opds/course/?id="+str(courseid)+"\"\n\
        type=\"application/atom+xml;profile=opds-catalog;kind=acquisition\"/>"
   
    xmlreturn += get_search_xml_snippet()

    """
    Course details 
    """

    try:
	py_time_now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
        course=Course.objects.get(id=coursepk, tincanid=coursetincanprefix)
        if course is not None:
            xmlreturn += "\n<title>" + course.name + "</title>\n"
            xmlreturn += "<updated>" + py_time_now + "</updated>"
            xmlreturn += get_author_xml_snippet(course.publisher)
            xmlreturn += "\n"
    except:
        authresponse=HttpResponse(status=500)
        authresponse.write("Course id does not exist (Is your tincanprefix and pk right?)")
        return authresponse
    else:
	all_blocks_in_course=course.packages.all()
        for o in all_blocks_in_course:
            entry = o;
            xmlreturn += "<entry>\n"
            xmlreturn += "<title>" + o.name +"</title>\n"
            #xmlreturn += "<id>"+o.tincanid+'/'+o.elpid+"</id>\n" #Changed on 16 March 2017
	    xmlreturn += "<id>"+o.elpid+"</id>\n"
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

	    try:
                for acquisition_link in entry.acquisitionlink.all():
                    print("In Acquisition Link : " + str(acquisition_link.id))
                    print("url is : " + str(acquisition_link.exefile))
                    url = str(acquisition_link.exefile)
                    url = url.replace('&', '&amp;')
                    xmlreturn += "<link rel=\"http://opds-spec.org/acquisition\"\n \
                        href=\"" + "/media/" + url + "\"\n\
                            type=\"" + acquisition_link.mimetype + "\"/>\n"

                    print("Figuring out preview_path")
                    preview_path = acquisition_link.preview_path
                    print(preview_path)
                    preview_path = preview_path.replace('&','&amp;')

                    micro_edition_url = ""

                    if str(acquisition_link.exefile).lower().endswith('.epub') and o.micro_edition:
                        dst=os.path.splitext(basename(url))[0]
                        if dst.strip():
                            print("Exists!")
                            micro_edition_url = os.path.dirname(url) + "/" +  dst + "_micro.epub"
                        micro_edition_url = micro_edition_url.replace('&','&amp;')
                        xmlreturn += "<link rel=\"http://opds-spec.org/acquisition\"\n \
                            href=\"" + micro_edition_url + "\"\n\
                            type=\"application/epub+zip;x-umprofile=micro\"/>\n"

                    if str(acquisition_link.exefile).lower().endswith('.epub') or \
                        str(acquisition_link.exefile).lower().endswith('.epub'):
                        if preview_path != None and preview_path != "":
                            xmlreturn += "<link rel=\"http://ustadmobile.com/epubrunner\"\n\
                               href=\"" + preview_path + "\" \n\
                                type=\"text/html;profile=opds-catalog;kind=acquisition\"/>"
            except Exception, e:
                print("Error in Acquiring links.")
                print(str(e))


            xmlreturn += "\n"
            xmlreturn += "</entry>\n"

	xmlreturn += "</feed>"

    authresponse = HttpResponse(status=200)
    authresponse.write(xmlreturn)
    return authresponse

@csrf_exempt
def public_opensearch_description(request):
    py_time_now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
    xmlreturn = get_opensearch_description()
    authresponse = HttpResponse(status=200)
    authresponse.write(xmlreturn)
    return authresponse


# Create your views here.
