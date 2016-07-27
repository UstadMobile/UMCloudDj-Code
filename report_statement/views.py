from django.shortcuts import render
from datetime import date, datetime, timedelta as td
import time
import json
import logging
from django.conf import settings
from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.context_processors import csrf
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.utils.decorators import decorator_from_middleware
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404

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
from uploadeXe.models import Course
from uploadeXe.models import Package as Block
from django.db.models import Q

from django import template
from django.core import serializers
import simplejson
from itertools import takewhile

from lrs import forms, models, exceptions
from lrs.util import req_validate, req_parse, req_process, \
	XAPIVersionHeaderMiddleware, accept_middleware, StatementValidator
from oauth_provider.consts import ACCEPTED, CONSUMER_STATES
from django.forms.models import model_to_dict
import os
import subprocess
import dateutil.parser
import zipfile
from xml.dom import minidom
from lxml import etree
import xml.etree.ElementTree as ET
from urlparse import urlparse
from opds.views import login_basic_auth
import xlsxwriter
from uploadeXe.models import Weekday
from uploadeXe.models import Week_Day_Time
from uploadeXe.models import DateTime

from holiday.models import Holiday
from holiday.models import Calendar

from collections import OrderedDict


# This uses the lrs logger for LRS specific information
logger = logging.getLogger(__name__)

"""
 This function will initiate and loop over the groupings 
 and assign the statements_info to groups
 It will also initiate indicators to be calculated
 By:group_em(0, root, ['School','Class'], [on,False,False]])
"""
def group_em(level, stmtGroup, grouping, indicators):
    #print("Stating grouping Level: " + str(level))
    stmtGroup.sub_group_by(grouping[level])
    print("Checking indicators..")
    if indicators[0] != False: # If Total Duration asked for..
        #print("Total Duration asked..")
	stmtGroup.get_total_duration()
	for everychild in stmtGroup.child_groups:
 	    #Indicator calculation call for total Duration
	    everychild.get_total_duration() 
    if level < len(grouping)-1:
	for child in stmtGroup.child_groups:
            group_em(level+1, child, grouping, indicators)

"""
 StatementGroupEntry is the group entry custom object
 made for the sole purpose of storing grouped statements_info
 relevant to the report query made / set.
 Groupings can be further grouped and certain indicators
 can be calculated on them like time, result, average
 Also makes rendering easier by its functions.
"""
class StatementGroupEntry():

    def __init__(self, statements_info, objectVal, level, parent, objectType):
        self.statements_info = statements_info
        self.objectVal = objectVal
        self.level = level
        self.objectType = objectType
        self.child_groups=[]
        self.total_duration=0 #in seconds
        self.average_score=0
        self.average_duration_users=[]

    def get_objectType_name(self):
        if isinstance(self.objectType, School):
            objectName=self.objectType.school_name + " School"
        elif isinstance(self.objectType, Allclass):
            objectName=self.objectType.allclass_name + " Class"
        elif isinstance(self.objectType, User):
            objectName=self.objectType.first_name + " " +\
	        self.objectType.last_name + " User"
        elif isinstance(self.objectType, Block):
            objectName=self.objectType.name + " Block"
        elif isinstance(self.objectType, Course):
            objectName=self.objectType.name + " Course"
        else:
            objectName="-"
        return objectName

    """ Returns the object in JSON
	Not Used currently
    """
    """
    def jdefault(self):
        json_objects = simplejson.dumps( [{
                           'objectName': o.get_objectType_name(),
                           'total_duration':o.total_duration\
			} for o in self.child_groups] )
        return json_objects
    """

    """ Sub Groups the Statement Group to further
	levels
    """
    def sub_group_by(self, objectType):
        applicable_stmts_info=[]
        all_statementinfo = self.statements_info

        """
        #Supposed to be a generic way to loop through any object 
	#types. Not done. Keeping this commented.
            #We first have to get all the courses from the statements
            objects = all_statementinfo.values('block').distinct()
           
            for objectdict in objects:
                for key in objectdict:
                    objectid=objectdict[key]

                object_statements=models.Statement.objects.filter(\
                    id__in=models.StatementInfo.objects.filter(\
                        statement__in=self.statements, block__id=objectid).\
                            values('statement', flat=True))
                applicable_stmts.append(object_statements)
                theobject=Block.objects.get(id=objectdict['block'])
                #subGroup=StatementGroupEntry(object_statements, self.objectVal,\
                                                 #self.level+1, self, 'Block')
                subGroup=StatementGroupEntry(object_statements, self.objectVal,\
                                                 self.level+1, self, theobject)
                self.child_groups.append(subGroup)

        """

        if isinstance(objectType, School): # True
            #We first get all the schools from the statements
            schools=all_statementinfo.values('school').distinct()
            for schooldict in schools: #Then we loop through every school
		#Added to ignore statements wihtout School assigned:
                if schooldict['school'] != None :
                	school_statements_info=all_statementinfo.filter(\
				school__id=schooldict['school'])
                        applicable_stmts_info.append(school_statements_info)
                        school=School.objects.get(id=schooldict['school'])
                        subGroup = StatementGroupEntry(school_statements_info,\
				 self.objectVal, self.level+1, self, school)
                        self.child_groups.append(subGroup)


        if isinstance(objectType, Allclass):
            #We first have to get all of the classes from the statements
            all_statementinfo = self.statements_info
            allclasses=all_statementinfo.values('allclass').distinct()
            for allclassdict in allclasses:
            	if allclassdict['allclass'] != None:
	            	allclass_statements_info = all_statementinfo.filter(\
				allclass_id=allclassdict['allclass'])
	                applicable_stmts_info.append(allclass_statements_info)
	                allclass=Allclass.objects.get(id=allclassdict['allclass'])
	                subGroup=StatementGroupEntry(allclass_statements_info,\
				 self.objectVal, self.level+1, self, allclass)
	                self.child_groups.append(subGroup)

        if isinstance(objectType, User):
            #We first have to get all the users from the statements
            users = all_statementinfo.values('user').distinct()
            for userdict in users:
            	if userdict['user'] != None:
	            	user_statements_info = all_statementinfo.filter(\
					user__id=userdict['user'])
	                applicable_stmts_info.append(user_statements_info)
	                user=User.objects.get(id=userdict['user'])
	                subGroup=StatementGroupEntry(user_statements_info,\
				 self.objectVal, self.level+1, self, user)
	                self.child_groups.append(subGroup)
	else:
	    pass

	""" Not Currently Used. Placeholder and logic kept.
        if isinstance(objectType, Course):
            courses = all_statementinfo.values('course').distinct()
            for coursedict in courses:
            	if coursedict['course'] != None:
	            	course_statements_info = all_statementinfo.filter(\
					course__id=coursedict['course'])
	                applicable_stmts_info.append(course_statements_info)
	                course=Course.objects.get(id=coursedict['course'])
	                subGroup=StatementGroupEntry(course_statements_info, self.objectVal, \
	                                                self.level+1, self, course)
	                self.child_groups.append(subGroup)

        if isinstance(objectType, Block):
            objects = all_statementinfo.values('block').distinct()
            for objectdict in objects:
            	if objectdict['block'] != None:
            		object_statements_info=all_statementinfo.filter(\
					block__id=objectdict['block'])
	                applicable_stmts_info.append(object_statements_info)
	                theobject=Block.objects.get(id=objectdict['block'])
	                subGroup=StatementGroupEntry(object_statements, self.objectVal,\
	                                                 self.level+1, self, theobject)
	                self.child_groups.append(subGroup)
	"""
        #("No object Type left/given.")

    """Logic and object method to get total Duration 
	from every statement group
    """
    def get_total_duration(self):
        total_duration=0
        #("Starting getting duratin..")
        for esi in self.statements_info:
        	duration = esi.duration
        	if duration != "-" or duration != None:
			#Note total_seconds() is only Python 2.7 and above
        		duration = int(esi.duration.total_seconds()) 
        		total_duration=total_duration+duration

        #("Finished getting duration.")
        self.total_duration=total_duration
        return total_duration


""" Report #1: All Statements from Your Organisation.
    All Statements Report from current user's 
    organisation. This method paginates it using Django 
    pagination feature.
"""
@login_required(login_url="/login/")    #Added by varuna
def pagi_statements_db_dynatable(request,\
	template_name='pagi_statements_db_02.html'):
    logger.info("User="+request.user.username+\
		" accessed /reports/pagi_allstatements/")
    organisation = User_Organisations.objects.get(\
		user_userid=request.user).organisation_organisationid;
    all_org_users= User.objects.filter(pk__in=\
	User_Organisations.objects.filter(\
	    organisation_organisationid=organisation\
		).values_list('user_userid', flat=True))
    all_statements = models.Statement.objects.filter(\
	user__in=all_org_users).order_by('-timestamp')
    # Shows 20 results per page
    paginator = Paginator(all_statements, 20) 
    page = request.GET.get('page')
    try:
        all_statements = paginator.page(page)
    except PageNotAnInteger:
        all_statements=paginator.page(1)
    except EmptyPage:
        all_statements = paginator.page(paginator.num_pages)

    data={}
    pagetitle="All statements from my organisation"
    tabletypeid="dbstatementsdynatable"
    table_headers_html=[]
    table_headers_name=[]

    table_headers_html.append("user")
    table_headers_name.append("User")
    table_headers_html.append("activity_verb")
    table_headers_name.append("Activity Verb")
    table_headers_html.append("activity_type")
    table_headers_name.append("Activity Title")
    table_headers_html.append("course_name")
    table_headers_name.append("Course")
    table_headers_html.append("block_name")
    table_headers_name.append("Block")
    table_headers_html.append("duration")
    table_headers_name.append("Duration")
    table_headers_html.append("timestamp")
    table_headers_name.append("Time")

    table_headers_html = zip(table_headers_html, table_headers_name)
    logicpopulation = "{\"user\":\"{{c.user.first_name}} \
	{{c.user.last_name}}\",\"activity_verb\":\"{{c.verb.get_display}}\
	    \",\"activity_type\":\"{{c.object_activity.get_a_name}}\",\
		\"timestamp\":\"{{c.timestamp}}\"},\
		    \"duration\":\"{{c.result_duration}}\""

    return render(request, template_name,{'object_list':all_statements,\
	 'table_headers_html':table_headers_html, 'pagetitle':pagetitle,\
	     'tabletypeid':tabletypeid, 'logicpopulation':logicpopulation} )

""" Report: All Statements From All Organisations (Super Admin)
    Super Admin's View of all statements from all 
    organisations. Paginated by Django Pagination.
"""
@login_required(login_url="/login/")
def show_statements_from_db(request,template_name='statements_db_01.html'):
    if request.user.is_staff == False:
	return redirect('reports')
    logger.info("Super User="+request.user.username+\
		" accessed /reports/stmtdb/")
    all_statements=models.Statement.objects.all().order_by('-timestamp')
    # Shows 100 results per page
    paginator = Paginator(all_statements, 100)
    page = request.GET.get('page')
    try:
        all_statements = paginator.page(page)
    except PageNotAnInteger:
        all_statements=paginator.page(1)
    except EmptyPage:
        all_statements = paginator.page(paginator.num_pages)
    data={}
    return render(request, template_name,{'all_statements':all_statements} )

""" Report: All Statements for your organisation (no lazy load)
    All Statements Report from current user's 
    organisation. Slow.
"""
@login_required(login_url="/login/")    #Added by varuna
def statements_db_dynatable(request,template_name='statements_db_02.html'):
    logger.info("User="+request.user.username+" accessed /reports/allstatements/")
    organisation = User_Organisations.objects.get(user_userid=request.user)\
						.organisation_organisationid;
    #redirect to pagi
    return redirect('pagi_allstatements')
    
    """
    all_org_users= User.objects.filter(pk__in=User_Organisations.objects\
		    .filter(organisation_organisationid=organisation)\
			.values_list('user_userid', flat=True))
    all_statements = models.Statement.objects.filter(user__in=all_org_users)
    data={}
    pagetitle="All statements from my organisation"
    tabletypeid="dbstatementsdynatable"
    table_headers_html=[]
    table_headers_name=[]

    table_headers_html.append("user")
    table_headers_name.append("User")
    table_headers_html.append("activity_verb")
    table_headers_name.append("Activity Verb")
    table_headers_html.append("activity_type")
    table_headers_name.append("Activity Title")
    table_headers_html.append("course_name")
    table_headers_name.append("Course")
    table_headers_html.append("block_name")
    table_headers_name.append("Block")
    table_headers_html.append("duration")
    table_headers_name.append("Duration")
    table_headers_html.append("timestamp")
    table_headers_name.append("Time")

    table_headers_html = zip(table_headers_html, table_headers_name)
    logicpopulation = "{\"user\":\"{{c.user.first_name}} \
	{{c.user.last_name}}\",\"activity_verb\":\
	    \"{{c.verb.get_display}}\",\"activity_type\"\
	 	:\"{{c.object_activity.get_a_name}}\",\"timestamp\"\
		    :\"{{c.timestamp}}\"},\"duration\":\"{{c.result_duration}}\""

    return render(request, template_name,{'object_list':all_statements,\
	 'table_headers_html':table_headers_html, 'pagetitle':pagetitle,\
	     'tabletypeid':tabletypeid, 'logicpopulation':logicpopulation} )
    """

"""
Internal Fix: This is a super user feature to update statementinfo tables 
as we updated the models as of 10th December 2014. 
"""
"""
@login_required(login_url="/login/")
def update_all_statementinfo(request, template_name='check_statementinfos.html'):
    logger.info("User="+request.user.username+\
	" accessed /reports/update_all_statementinfo/")
    organisation = User_Organisations.objects.get(\
	user_userid=request.user).organisation_organisationid;
    objectList=[]

    #Code to figure out missing assignments of 
    #Course/Block/School/Class
    all_org_users= User.objects.filter(pk__in=\
	User_Organisations.objects.filter(\
	    organisation_organisationid=organisation\
		).values_list('user_userid', flat=True))
    all_statementinfo = models.StatementInfo.objects.filter(\
	user__in=all_org_users)
    print("Starting check on all statementinfos")
    cfschool = School.objects.get(school_name="Kuchi-GEC")
    cfallclass = Allclass.objects.get(allclass_name="AllStudentsClass")
    print(cfschool)
    for esi in all_statementinfo:
	if esi.allclass == None:
	    if organisation.organisation_name=="ChildFund":
	        print("Null School for esi: " + str(esi.id))
	        objectList.append(esi.id)

    result="test"
    return render(request, template_name, {'object_list':objectList, 'result':result} )
"""
"""
Internal Fix: To update all user profile to have a last activity date
"""
"""
def update_lastactivity(request, template_name='check_statementinfos.html'):
    object_list=[]

    print("Getting all users..")
    #allusers = User.objects.all()
    karmaorg = Organisation.objects.get(organisation_name="Karmasnap")
    allusers= User.objects.filter(pk__in=\
        User_Organisations.objects.filter(\
            organisation_organisationid=karmaorg\
                ).values_list('user_userid', flat=True))
    allusers=User.objects.all()
    for everyuser in allusers:
	try:
	    everyuser_laststatement = models.Statement.objects.filter(user=everyuser,\
		object_activity__activity_definition_type__icontains=\
		    "activities/module").latest("timestamp")
	    lastactivity_date = everyuser_laststatement.timestamp.isoformat()
	    everyuser_profile = UserProfile.objects.get(user=everyuser)
	    everyuser_profile.last_activity_date = lastactivity_date
	    everyuser_profile.save()
	except:
	    #print("Unable to save last assigned for user: " + everyuser.username)
	    object_list.append(everyuser.id)
    print("Done")
    result="test"
    return render(request, template_name,{'object_list':object_list, \
                                          'result':result} )

"""

"""
Internal Fix: Quick fix for organisation statements for
 which statement info hasnt been generated
"""
@login_required(login_url="/login/")
def check_statementinfos(request, template_name='check_statementinfos.html'):
    logger.info("User="+request.user.username+\
        " accessed /reports/check_statementinfos/")
    cforg = Organisation.objects.get(organisation_name="UNICEF AF LUL")
    organisation = User_Organisations.objects.get(\
        user_userid=request.user).organisation_organisationid;
    organisation = cforg
    all_org_users= User.objects.filter(pk__in=\
        User_Organisations.objects.filter(\
            organisation_organisationid=organisation\
                ).values_list('user_userid', flat=True))
    nosilist=[]
    if request.user.is_staff == False:
        return redirect('reports')

    allCF106statements=models.Statement.objects.filter(user__in = all_org_users)
    #allCF106statements = models.Statement.objects.filter(user_id = 208)
    print(len(allCF106statements))
    print("-----------------------------------------------------------------")
    total_duration=0
    for es in allCF106statements:
        try:
            esi = models.StatementInfo.objects.get(statement = es)
            if esi.allclass == None or esi.allclass == "-":
                print("No class generated for " + str(esi.id) + " Generating it..")
                es.save()
            else:
                print("Already assigned class for " + str(esi.id))
            if esi.school == None or esi.school == "-":
                print("No school generated for " + str(esi.id) + " Generating it..")
                #es.save()
            else:
                print("Already assigned school for " + str(esi.id))
        except:
            print("Could not find Statement info for this statement " + str(es.id) + ". Saving it again will regenerate it.")
            es.save()
    print(len(allCF106statements))
    """
    all_statements = models.Statement.objects.filter(user__in=all_org_users)
    for a in all_statements:
        try:
            asi = models.StatementInfo.objects.get(statement=a)
        except:
            print("No SI for statement id: " + str(a.id))
            nosilist.append(a.id)
            #Saving the statement again will generate the Statement Info entry.
            a.save()
    """

    result="test"
    return render(request, template_name,{'object_list':nosilist, \
                                          'result':result} )

"""Report: Registration Report (with unicode mapping script call)
   This report will be made for registration event statements 
   that are part of the organisation. It will also try and attempt
   to fix false mappings for question name and responses as well. 
   In use specificn to a particular organisation and is to be 
   retained until App talks to the server properly.
"""
@login_required(login_url="/login/") 
def registration_statements(request,\
	template_name='group_registration_statements.html'):
    logger.info("User="+request.user.username+\
	" accessed /reports/statements_registration/")
    organisation = User_Organisations.objects.get(\
	user_userid=request.user).organisation_organisationid;
    if organisation.id != 9:
	return redirect('reports')
    all_org_users= User.objects.filter(pk__in=\
	User_Organisations.objects.filter(\
	    organisation_organisationid=organisation\
		).values_list('user_userid', flat=True))
    all_statements = models.Statement.objects.filter(user__in=all_org_users)

    #Rendering success till it fastens.
    result="success"
    return render(request, template_name,{'result':result} )


    """
    Fix for statements (new) that don't get assigned to any block. 
    """
    for every_statement in all_statements:
        statement_json=every_statement.full_statement
        blockn=models.StatementInfo.objects.get(statement=\
						every_statement).block
        try:
            blockname=blockn.name        
	    try:
		coursen=models.StatementInfo.objects.get(statement=\
						every_statement).course
		try:
		    coursename=coursen.name
		except:	
		    esi=models.StatementInfo.objects.get(\
					statement=every_statement)
		    esicourse = Course.objects.get(packages=esi.block)
		    if esi.course == None and esicourse != None:
                        esi.course = esicourse
                        esi.save()
	    except:
		print("Something went wrong in fixing statements.")
	
        except: #If no block is assigned to this statementinfo
            #("Trying for Statement: " + str(every_statement.id))
	    #("Statement id: " + str(every_statement.id))
            try:
                context_parent = statement_json[u'context'][u'registration']
                #("Reg id:" + str(context_parent))
                activity_id=statement_json[u'object']['id']
                elpid=activity_id.rsplit('/',1)[1]
		#("Statement id: " + str(every_statement.id))
                try:
                    if "um_assessment" in elpid or unicode("um_assessment") in elpid:
                        elpid=elpid[:-13]
                        block = Block.objects.get(elpid=elpid, success="YES",\
			  publisher__in=User.objects.filter(\
			    pk__in=User_Organisations.objects.filter(\
				organisation_organisationid=organisation\
				    ).values_list('user_userid', flat=True)))
                        si = models.StatementInfo.objects.get(
						statement=every_statement)
                        if si.block == None and block != None:
                            print("Statement is going to be updated and \
				assigned block: " + block.name)
                            si.block = block
                            si.save()

                            for e in all_statements:
                                fs = e.full_statement
                                try:
                                    registrationid=\
					fs[u'context'][u'registration']
                                    if str(registrationid) == \
					str(context_parent) and block != None:
                                        esi = models.StatementInfo.objects.get(\
						statement=e)
                                        if esi.block == None:
                                            esi.block = block
                                            print("Statement: " + \
						str(e.id) + \
						    " should be of block: " +\
							 block.name)
                                            esi.save()
                                except:
				    print("Unable to assign")
			else:
			    print("elp id unmatch..")
		except:
			print("Unable to fix that.")

            except:
		pass
	        print("Something went wrong in getting activity id " +\
			"and or context parent " + str(every_statement.id))

    dict_reg = dict() #This is all the registration statements grouped by red id.
    school_dict = dict() #These are all the registration ids grouped by school id.
    #Group this by registration id 
    appLocation=(os.path.dirname(os.path.realpath(__file__)))
    timestamp=time.strftime("%Y%m%d%H%M%S")
    registrationcodefile = appLocation + \
	'/../UMCloudDj/media/cfregdump/lulregids_'+timestamp+'.txt'
    sorted_registrationcodefile = appLocation + \
	'/../UMCloudDj/media/cfregdump/sorted_lulregids_'+timestamp+'.txt'
    g = open(sorted_registrationcodefile, 'w')
    now = time.strftime("%c")
    g.write("Registration Report (UNICEF AF LUL)"+'\n')
    g.write('\n'+"ID|Item|Value|User|Block|Date"+'\n');
    for every_statement in all_statements:
	statement_json=every_statement.full_statement
	blockn=models.StatementInfo.objects.get(statement=\
					every_statement).block
 	try:
	    blockname=blockn.name
	except:
	    blockname="-"
        try:
            context_parent = statement_json[u'context'][u'registration']
	    user=every_statement.user
	except:
	    context_parent = None
	    pass
	if context_parent != None:
 	    try:
	        activity_name = statement_json[u'object'][u'definition'][u'name'][u'en-US']
		activity_id= statement_json[u'object']['id']
		username = every_statement.user.username
	    except:
		activity_name = ""
	    try:
	        result = statement_json[u'result'][u'response']
	    except:
		result = ""
	    if activity_name != "":
	        if context_parent in dict_reg:
	 	    dict_reg[context_parent].append(\
			activity_name + "|" + result + "|" + activity_id +\
		        "|"+username+"|" + blockname+"|"+\
			    every_statement.timestamp.strftime(\
				"%B %d %Y %H:%M"))
		   
		    if activity_name == "Please enter school ID" or\
			 activity_name == unicode("Please enter the school ID"):
			school_id=result
			if result in school_dict:
			    school_dict[result].append(context_parent)
		 	else:
			    school_dict[result]=[context_parent]
	        else:
		    dict_reg[context_parent] = [activity_name + "|" + \
			result + "|" + activity_id +"|"+username+"|" + \
			    blockname+"|"+every_statement.timestamp.strftime(\
				"%B %d, %Y %H:%M")]

		    if activity_name == "Please enter school ID" or\
			activity_name == unicode("Please enter the school ID"):
                        school_id=result
                        if result in school_dict:
                            school_dict[result].append(context_parent)
                        else:
                            school_dict[result]=[context_parent]

    all_reg_ids=dict_reg.keys()
    regidsalldone=[]
    regidsdone=[]
    #(school_dict)
    for schoolid, regids in school_dict.iteritems():
	#regidsdone=[] Commented to fix issue #10
	if schoolid.encode('utf8') == "":
	    schoolid="(Blank)"
	g.write('\n'+"School ID:"+schoolid.encode('utf8')+""+'\n')
	for regid in regids:
	    if regid not in regidsdone:
	        statements = dict_reg.get(regid.encode('utf8'))
		temp_statement=dict_reg.get(regid)[0]
		temp_statement_split=temp_statement.split('|');
		user_time=temp_statement_split[3]+ "|"+\
			temp_statement_split[4]+"|"+\
			temp_statement_split[5]
	        g.write("New Registration|("+regid+")|" + user_time +\
			 ""+'\n')
	        for s in statements:
	            g.write(s.encode('utf8').replace('\n', '')+'\n')
	        g.write('\n')
 	        regidsdone.append(regid)
		regidsalldone.append(regid)
		

    #Code to append missed registrations.
    unassigned_reg_ids=list(set(all_reg_ids) - set(regidsdone))
    g.write('\n'+"Registrations without School IDs:"+'\n'+ '\n')
    #(unassigned_reg_ids)
    for regid in unassigned_reg_ids:
	statements = dict_reg.get(regid.encode('utf8'))
        temp_statement=dict_reg.get(regid)[0]
        temp_statement_split=temp_statement.split('|');
        user_time=temp_statement_split[3]+ "|"+\
	    	temp_statement_split[4]+"|"+ \
			temp_statement_split[5]
	g.write("New Registration|("+regid+")|" + user_time + "" +'\n')
	for s in statements:
	    g.write(s.encode('utf8').replace('\n', '')+'\n')
	g.write('\n')


    g.close()
    script=appLocation+'/../UMCloudDj/media/cfregdump/run.sh'
    scriptruncommand=script+' '+ sorted_registrationcodefile
    if os.system(scriptruncommand) == 0:
	print("A Success")
	result="success"
	return render(request, template_name,{'object_list':dict_reg,\
 	    'result':result} )
    else:
	result="fail"
	print("FAIL")
	return render(request, template_name,{'object_list':dict_reg,\
	    'result':result} )
    result="fail"
    return render(request, template_name,{'object_list':dict_reg, \
	'result':result} )

""" Report: My Statements Report
This report just shows the current logged in user's statements
"""
@login_required(login_url="/login/")    #Added by varuna
def my_statements_db_dynatable(request,template_name='user_statements_report_04.html'):
    user=request.user
    all_statements=models.Statement.objects.filter(user=user)
    data={}
    pagetitle="UstadMobile Statements from DB Test 02 Dynatable"
    tabletypeid="dbstatementsdynatable"
    table_headers_html=[]
    table_headers_name=[]

    table_headers_html.append("user")
    table_headers_name.append("User")
    table_headers_html.append("activity_verb")
    table_headers_name.append("Activity Verb")
    #table_headers_html.append('activity_id')
    #table_headers_name.append('Activity ID')
    table_headers_html.append("activity_type")
    table_headers_name.append("Activity Title")
    table_headers_html.append("duration")
    table_headers_name.append("Duration")
    table_headers_html.append("timestamp")
    table_headers_name.append("Time")

    table_headers_html = zip(table_headers_html, table_headers_name)
    logicpopulation = "{\"user\":\"{{c.user.first_name}} {{c.user.last_name}}\
		\",\"activity_verb\":\"{{c.verb.get_display}}\",\"activity_type\":\
		    \"{{c.object_activity.get_a_name}}\",\"timestamp\":\"{{c.timestamp}}\
			\"},\"duration\":\"{{c.result_duration}}\""

    return render(request, template_name,{'object_list':all_statements, \
	'table_headers_html':table_headers_html, 'pagetitle':pagetitle, \
	    'tabletypeid':tabletypeid, 'logicpopulation':logicpopulation} )


""" Report: Other User's Statement Report
This report shows and renders any other user's report based on the
userid given to the get parameter.
Org admins cannot make statement requests for users that belong to 
other organisations (duh)
"""
@login_required(login_url="/login/")
def user_statements_table(request, userid, template_name=\
			    'user_statements_report_04.html'):
    #, date_since, date_until):
    requestuser=request.user
    organisation = User_Organisations.objects.get(\
	user_userid=request.user).organisation_organisationid;
    users= User.objects.filter(pk__in=User_Organisations.objects.filter(\
	organisation_organisationid=organisation).values_list(\
	    'user_userid', flat=True))
    try:
        user=User.objects.get(id=userid)
    except:
	logger.info("User="+request.user.username+\
	    " tried to access a false user's statements")
	return redirect('reports')
    if user not in users:
	logger.info("User=" + rquest.user.username+ \
	    "tried to access another organisation's user statements. We blocked this.")
	return redirect('reports')
    logger.info("User="+request.user.username+" accessed " +user.username+\
	 " statements at /reports/durationreport/getstatements/"+str(user.id)+"/")
    all_statements=models.Statement.objects.filter(user=user)
    data={}
    pagetitle="UstadMobile User Statements"
    tabletypeid="userstatementasrequesteddyna"
    table_headers_html=[]
    table_headers_name=[]

    table_headers_html.append("user")
    table_headers_name.append("User")
    table_headers_html.append("activity_verb")
    table_headers_name.append("Activity Verb")
    table_headers_html.append('activity_id')
    table_headers_name.append('Activity ID')
    table_headers_html.append("activity_type")
    table_headers_name.append("Activity Title")
    table_headers_html.append("duration")
    table_headers_name.append("Duration")
    table_headers_html.append("timestamp")
    table_headers_name.append("Time")

    table_headers_html = zip(table_headers_html, table_headers_name)
    logicpopulation = "{\"user\":\"{{c.user.first_name}}\
	 {{c.user.last_name}}\",\"activity_verb\":\"{{c.verb.get_display}}\"\
	    ,\"activity_type\":\"{{c.object_activity.get_a_name}}\"\
		,\"timestamp\":\"{{c.timestamp}}\"},\
		    \"duration\":\"{{c.result_duration}}\""
    return render(request, template_name,{'object_list':all_statements,\
	 'table_headers_html':table_headers_html, 'pagetitle':pagetitle,\
	     'tabletypeid':tabletypeid, 'logicpopulation':logicpopulation} )

""" Fetch: Get all Students from the Class ID Given.
Cannot fake a class id from another org (aha!)
"""
@login_required(login_url="/login/")
def allclasse_students(request, allclassid):
    organisation = User_Organisations.objects.get(\
	user_userid=request.user).organisation_organisationid
    allclasses=Allclass.objects.filter(school__in=\
	School.objects.filter(organisation=organisation));
    allclass_class = Allclass.objects.get(id=allclassid)
    if allclass_class in allclasses:
        student_list =allclass_class.students.all()
	#Not sending complete user object to avoid someone \
	#hacking and getting user information like encrypted\
	# password, roles and all other information like Uber did.\
	# This only returns id and first and last name which is \
	# checked by request.user's logged in account anyway.
	json_students = simplejson.dumps( [{'id': o.id,
                           'first_name': o.first_name,	
			    'last_name':o.last_name} for o in student_list] )
        return HttpResponse(json_students, mimetype="application/json")
    else:
        logger.info("Class requested not part of request user's organisation."+ \
		" Something is fishy")
        return HttpResponse(None)

""" Fetch: All Blocks from Course ID given in GET request.
Cannot fake other organisations' id.
"""
@login_required(login_url='/login/')
def allcourses_blocks(request):
    try:
	allcourseid=request.GET.get('id')
    	organisation = User_Organisations.objects.get(\
	    	user_userid=request.user).organisation_organisationid
    	allcourse_course = get_object_or_404(Course, pk=allcourseid)
	allcourses_organisation = Course.objects.filter(\
					organisation=organisation)
	if allcourse_course not in allcourses_organisation\
	 and allcourse_course.name != "Afghan-Literacy":
		return HttpResponse("That course does not exist in your organisation")
    	course_blocks = allcourse_course.packages.all()
    	json_blocks =simplejson.dumps([ {'id': b.id,
			'icon':'/media/images/package.small.png',
			'type':'block',
			'text': b.name} for b in course_blocks])
    	return HttpResponse(json_blocks, mimetype="application/json")
    except:
	logger.info("Something went wrong in fetching blocks")
	return HttpResponse(None)

"""Fetch: All Students from a Class ID given as param
Cannnot fake other org ids.
"""
@login_required(login_url='/login/')
def allclass_students(request):
    try:
	allclassid = request.GET.get('allclassid')
	organisation = User_Organisations.objects.get(\
		user_userid=request.user).organisation_organisationid
	allclass = get_object_or_404(Allclass, pk=allclassid)
	allclasses=Allclass.objects.filter(school__in=School.objects.filter\
						(organisation=organisation));
	students=allclass.students.all()
	if allclass not in allclasses:
		logger.info("That class isn't in your organisation")
		return HttpResponse("That class isn't in your organisation")
	json_students = simplejson.dumps([{'id':s.id,'text':s.first_name+" "\
				+s.last_name}for s in students])
	return HttpResponse(json_students, mimetype="application/json")
    except:
	logger.info("Something went wrong.")
	return HttpResponse(None)

"""Fetch: All classes from the School ID given in GET param.
Cannot fake other org's ids.
"""
@login_required(login_url='/login/')
def school_allclasses(request):
    try:
	schoolid=request.GET.get('id')
	organisation = User_Organisations.objects.get(\
		user_userid=request.user).organisation_organisationid
	school = get_object_or_404(School, pk=schoolid)
	if school.organisation != organisation:
		logger.info("That school does not exist in your organisation")
  		return HttpResponse(\
		    "That school does not exist in your organisation")
	allclasses = Allclass.objects.filter(school=school)
	json_allclasses = simplejson.dumps([ {'id':c.id, 'text':c.allclass_name,
				'icon':'/media/images/class.small.png',
				'type':'allclass',
				'children':[{'id':s.id,'text':s.first_name+" "+s.last_name,\
					'type':'user',\
					'icon':'/media/images/users.small.png'}\
				 for s in c.students.all()]} for c in allclasses ])
	return HttpResponse(json_allclasses, mimetype="application/json")
    except:
	logger.info("Something went wrong in fetching classes from schools..")
	logger.info("An Error really.")
	return HttpResponse("Something went wrong.")
	    
"""Fetch: Get all courses from request's user  organisation
"""
@login_required(login_url='/login/')
def allcourses(request):
    try:
     	organisation = User_Organisations.objects.get(user_userid=request.user)\
		.organisation_organisationid
	if organisation.organisation_name == "ChildFund":
	    afghancourse = Course.objects.get(name="Afghan-Literacy")
	    allorgcourses = Course.objects.filter(\
		Q(organisation=organisation)|Q(name="Afghan-Literacy"))
	else:
	    allorgcourses = Course.objects.filter(organisation=organisation)

   	json_courses = simplejson.dumps([ {'id': c.id, 'text':c.name,
				'type':'course',
				'icon':'/media/images/course.small.png',
				 'children':True} for c in allorgcourses ])
	json_courses=json_courses[:1] + '{"text":"All Courses",\
				"icon":"/media/images/course.small.png",\
				"type":"course",\
				"id":"allcourses","children":[' +\
				  json_courses[1:] + "}]"
    	return HttpResponse(json_courses,mimetype="application/json")
    except:
	logger.info("Something went wrong in fetcvhing all courses.")
	logger.info("You shouldn't even be seeing this, the login required \
		function should take you to the login page. Either \
		something wrong in this code or login redirect.")
	return HttpResponse(None)

"""Fetch: All Schools in request user's organisation
"""
@login_required(login_url='/login/')
def allschools(request):
    try:
	organisation = User_Organisations.objects.get(user_userid=request.user)\
		.organisation_organisationid
	allorgschools = School.objects.filter(organisation=organisation)
	json_schools = simplejson.dumps([{'id':s.id, 'text':s.school_name, 
				'icon':'/media/images/school.small.png',
				'type':'school',
				'children':True} for s in allorgschools ])
	json_schools=json_schools[:1] + '{"text":"All Schools","id":"allschools",\
				"type":"school", "icon":"/media/images/school.small.png",\
				"children":[' +  json_schools[1:] + "}]"
	return HttpResponse(json_schools, mimetype="application/json")
    except:
	logger.info("Something went wrong in fetching all schools")
	logger.info("Error really..")
	return HttpResponse(None)

"""Report: Last Activity Report
This report shows the last activity for every user in current org.
Only useful for org admins and functionality limited to org admins only
"""
@login_required(login_url='/login/')
def last_activity_selection(request):
    user_role = User_Roles.objects.get(user_userid=request.user).role_roleid;
    organisational_admin_role = Role.objects.get(pk=2)
    if user_role != organisational_admin_role:
        authresponse = HttpResponse(status=400)
        authresponse.write("Not Org admin")
        return authresponse        
    logger.info("User="+request.user.username+\
            " accessed /reports/last_activity_selection/")
    organisation = User_Organisations.objects.get(\
            user_userid=request.user).organisation_organisationid
    current_user = request.user.username + " (" + \
            organisation.organisation_name + ")"
    current_user_role = User_Roles.objects.get(user_userid=\
                            request.user.id).role_roleid.role_name;
    current_user = "Hi, " + request.user.first_name + ". You are a " +\
            current_user_role + " in " + organisation.organisation_name +\
                " organisation."
    return render_to_response('last_activity_report_selection.html',\
        {'current_user':current_user}, context_instance = RequestContext(request))


"""Report: Last activity Report

"""
@login_required(login_url='/login/')
def last_activity(request, template_name='last_activity_report.html'):
    if request.method != 'POST':
	pass
        #return redirect('last_activity_selection')
        #Return "Not Post request";

    user_role = User_Roles.objects.get(user_userid=request.user).role_roleid;
    organisational_admin_role = Role.objects.get(pk=2)
    if user_role != organisational_admin_role:
        authresponse = HttpResponse(status=400)
        authresponse.write("Not Org admin")
        return authresponse        

    #Get current organisation 
    organisation = User_Organisations.objects.get(\
                user_userid=request.user).organisation_organisationid;

    #Get all users in the organisation
    user_selected= User.objects.filter(pk__in=\
        User_Organisations.objects.filter(\
            organisation_organisationid=organisation\
                ).values_list('user_userid', flat=True))
    users_with_statements = user_selected

    logger.info("User="+request.user.username+" accessed /reports/lastactivity/")

    if True:
        yaxis=[]
        label_legend=[]
        user_duration=0

        last_activity=[]
	all_userids=[]
	class_assigned = ""
	all_class_assigned=[]

        for user_with_statement in users_with_statements:
	    try:
	        alluserclasses = Allclass.objects.filter(students__in=[user_with_statement])
	 	first=True
		for everyclass in alluserclasses:
		    if first:
		        class_assigned = everyclass.allclass_name
			first=False
		    else:
			class_assigned = class_assigned + ", " + everyclass.allclass_name
	    except:
		class_assigned = "-";
	    all_class_assigned.append(class_assigned)
	    
	    all_userids.append(user_with_statement.id)
	    label_legend.append(user_with_statement.first_name + " " + user_with_statement.last_name)
	    try:
		b=UserProfile.objects.get(user=user_with_statement).last_activity_date.isoformat()
		#if b is None:
		#    b="-"
	    except:
		b="-"
	    last_activity.append(b)
        #yaxis=zip(label_legend, yaxis, user_by_duration, users_with_statements, last_activity)
        yaxis=zip(label_legend, all_userids, last_activity, all_class_assigned)
        data={}
        data['yaxis']=yaxis


        data['pagetitle']="UstadMobile Last Activity Report"
        data['tabletypeid']="lastactivitydynatable"

        table_headers_html=[]
        table_headers_name=[]
        table_headers_html.append("user")
        table_headers_name.append("User")
        table_headers_html.append("last_activity")
        table_headers_name.append("Last activity")
        table_headers_html = zip(table_headers_html, table_headers_name)

        data['table_headers_html']=table_headers_html

    return render(request, template_name, data)

"""Report: Last activity Report - Inactive for x days

"""
@login_required(login_url='/login/')
def last_activity_inactive(request, template_name='last_activity_report.html'):
    days_inactive = request.GET.get('daysinactive')
    if days_inactive == None or days_inactive == "":
        print("No days specified")
        return redirect('last_activity')
    try:
	days_inactive = int(days_inactive)
    except:
	print("Unable to cast int.")
        return redirect('last_activity')
    if days_inactive == None or days_inactive == "" or days_inactive == 0:
	print("Un workable days inactive")
	return redirect('last_activity')


    print("Checking for days: " + str(days_inactive))
    user_role = User_Roles.objects.get(user_userid=request.user).role_roleid;
    organisational_admin_role = Role.objects.get(pk=2)
    if user_role != organisational_admin_role:
        authresponse = HttpResponse(status=400)
        authresponse.write("Not Org admin")
        return authresponse

    #Get current organisation 
    organisation = User_Organisations.objects.get(\
                user_userid=request.user).organisation_organisationid;

    #Get all users in the organisation
    user_selected= User.objects.filter(pk__in=\
        User_Organisations.objects.filter(\
            organisation_organisationid=organisation\
                ).values_list('user_userid', flat=True))
    users_with_statements = user_selected

    logger.info("User="+request.user.username+" accessed /reports/lastactivity/")

    if True:
        yaxis=[]
        label_legend=[]
        user_duration=0

        last_activity=[]
        all_userids=[]

        users_with_statement_profile = UserProfile.objects.filter(user__in=users_with_statements).filter(last_activity_date__lte=datetime.now() - td(days=days_inactive))

	for userprofile in users_with_statement_profile:
	    all_userids.append(userprofile.user.id)
	    label_legend.append(userprofile.user.first_name + " " + userprofile.user.last_name)
	    try:
		b = userprofile.last_activity_date.isoformat()
	    except:
		b="-"
	    last_activity.append(b)
        #yaxis=zip(label_legend, yaxis, user_by_duration, users_with_statements, last_activity)
        yaxis=zip(label_legend, all_userids, last_activity)
        data={}
        data['yaxis']=yaxis


        data['pagetitle']="UstadMobile Last Activity Report"
        data['tabletypeid']="lastactivitydynatable"

        table_headers_html=[]
        table_headers_name=[]
        table_headers_html.append("user")
        table_headers_name.append("User")
        table_headers_html.append("last_activity")
        table_headers_name.append("Last activity")
        table_headers_html = zip(table_headers_html, table_headers_name)

        data['table_headers_html']=table_headers_html
	data['inactivefor']=days_inactive

    return render(request, template_name, data)


"""Report: Attendance Report Selection
"""
@login_required(login_url='/login/')
def attendance_selection(request):
        logger.info("User="+request.user.username+\
                " accessed /reports/attendance_selection/")
        organisation = User_Organisations.objects.get(\
                user_userid=request.user).organisation_organisationid
        current_user = request.user.username + " (" + \
                organisation.organisation_name + ")"
        current_user_role = User_Roles.objects.get(user_userid=\
                                request.user.id).role_roleid.role_name;
        current_user = "Hi, " + request.user.first_name + ". You are a " +\
                current_user_role + " in " + organisation.organisation_name +\
                    " organisation."
	
	teacher_role = Role.objects.get(role_name="Teacher")
	user_role = User_Roles.objects.get(user_userid=request.user).role_roleid
	if (user_role == teacher_role):
	    #Get only the classes the teacher has access to. Duh.
	    allteachers=[]
            allteachers.append(user)
            allclass_list=Allclass.objects.filter(teachers__in=allteachers);
	else:
	    #Get all classes in that organisation
	    allclass_list=Allclass.objects.filter(school__in=School.objects.filter(organisation=organisation));
	template_name="attendance_report_selection.html"
	data={}
	data['current_user'] = current_user
	data['allclass_list'] = allclass_list
	return render(request, template_name, data)
        #return render_to_response('attendance_report_selection.html',\
        #    {'current_user':current_user}, context_instance = RequestContext(request))

"""Report: Attendance Get Registration for selection
"""
@login_required(login_url='/login/')
def attendance_get_registration(request, template_name='attendance_all_registration.html'):
    if request.method != 'POST':
        return redirect('attendance_selection')
    try:
        date_since = request.POST['since_1_alt']
        date_until = request.POST['until_1_alt'] 
	allclass_id = request.POST['allclass']
        allclass = Allclass.objects.get(pk=allclass_id)
        if allclass is not None:
        
            #Get all registrations unique for that class 
            #allclass_statements = models.Statement.objects.filter(\
            #    , timestamp__range=[date_since, date_until])
            attended_activity_string = "http://www.ustadmobile.com/activities/attended-class/"
            activity_id_string = attended_activity_string + allclass_id
            all_activity_id_string = []
            activity_id_string2 = activity_id_string + "/"
            all_activity_id_string.append(activity_id_string)
            all_activity_id_string.append(activity_id_string2)
            all_hosted_verb_id = []
            hosted_verb_id = "http://activitystrea.ms/schema/1.0/host"
            hosted_verb_id2 = "http://activitystrea.ms/schema/1.0/host/"
            all_hosted_verb_id.append(hosted_verb_id)
            all_hosted_verb_id.append(hosted_verb_id2)
            hosted_verb = models.Verb.objects.filter(verb_id__in=all_hosted_verb_id)
            attendance_activity = models.Activity.objects.filter(\
                activity_id__in=all_activity_id_string)

            #Get all registrations 
	    allteachers=[]
            all_registrations = models.Statement.objects.filter(\
                timestamp__range = [date_since, date_until],\
                    object_activity__in = attendance_activity,\
                        verb__in=hosted_verb).distinct('context_registration')
	    for every_registration in all_registrations:
		print("hi")
		allteachers.append(every_registration.user)
            print("I think I got the registrations")
            print(all_registrations)
	    table_headers_html = []
	    table_headers_name = []
   	    table_headers_html.append("registration")
            table_headers_name.append("Registration ID")
            table_headers_html.append("timestamp")
            table_headers_name.append("Time")
	    table_headers_html = zip(\
		table_headers_html, table_headers_name)


	    all_registrations = zip(\
		all_registrations, allteachers)
	    data={}
	    
	    data['yaxis'] = all_registrations
	    data['pagetitle'] = "All registrations Selection"
	    data['allclass'] = allclass
	    ds = dateutil.parser.parse(date_since)
	    du = dateutil.parser.parse(date_until)
	    data['date_since'] = date_since
	    data['date_until'] = date_until
	    data['date_since']=ds
	    data['date_until']=du
	    data['tabletypeid'] = "attendanceregistration"
	    data['table_headers_html'] = table_headers_html
	    
	    return render(request, template_name, data)
	    
	else:
            authresponse = HttpResponse(status=400)
            authresponse.write("Invalid class selected. Something went wrong.")
            return authresponse
    except Exception as e:
        print(e)
        authresponse = HttpResponse(status=500)
        authresponse.write("Reporting exception: " + e.message + " Please check!")
        return authresponse

	
class Student(object):
    name = ""
    verb = "" 
    fingerprinted = ""
    gender=""

    # The class "constructor" - It's actually an initializer 
    def __init__(self, name, verb, fingerprinted):
        self.name = name
        self.verb = verb
        self.fingerprinted = fingerprinted
    #Anlther one
    def __init__(self, name, verb, fingerprinted, gender):
        self.name = name
        self.verb = verb
        self.fingerprinted = fingerprinted
        self.gender = gender


"""Report: Student Attendance Report by Registration ID
"""
@login_required(login_url='/login/')
def attendance_registration_students(request, registration_id, template_name='attendance_registration_students.html'):
    #if request.method != 'POST':
    #    return redirect('attendance_selection')
    try:
	
	attended_activity_string = "http://www.ustadmobile.com/activities/attended-class/"
        all_hosted_verb_id = []
        hosted_verb_id = "http://activitystrea.ms/schema/1.0/host"
        hosted_verb_id2 = "http://activitystrea.ms/schema/1.0/host/"
        all_hosted_verb_id.append(hosted_verb_id)
        all_hosted_verb_id.append(hosted_verb_id2)
        hosted_verb = models.Verb.objects.filter(verb_id__in=all_hosted_verb_id)

	allstudents_statements_per_registration = models.Statement.objects.filter(\
                    context_registration = registration_id).exclude(\
                        verb__in = hosted_verb)
	timestamp = ""
	try:
	    #Get class
	    a = allstudents_statements_per_registration[0].object_activity.activity_id.strip()
	    timestamp = allstudents_statements_per_registration[0].timestamp
	    pos = a.find(attended_activity_string)
	    pos = pos + len(attended_activity_string)
	    allclass_id = a[pos:].strip()
	    if (allclass_id.endswith('/')):
	         allclass_id = allclass_id[:-1]
	    allclass = Allclass.objects.get(pk=allclass_id)
	    if allclass is None:
	        allclass = ""
	except Exception as e:
	    print("Unable to get class from activity id")
	    print(str(e.message));
	    allclass = ""

        print("All student statements for Registration : " + str(registration_id))
        print(allstudents_statements_per_registration)
	all_students_attendance = []
        for every_statement in allstudents_statements_per_registration:
	    actor_name = every_statement.actor.get_a_name()
            verb = every_statement.verb.get_display()
            context_extensions = every_statement.context_extensions
            #context_extensions_json = json.loads(context_extensions)
	    fingerprinted = ""
	    try:
                fingerprinted = context_extensions[u'http://www.ustadmobile.com/fingerprinted']
	    except:
		fingerprinted = ""
            if not fingerprinted:
		all_students_attendance.append(Student(actor_name, verb, "",""))
                print("For student: " + actor_name + "->" + verb +  " " )
            else:
		all_students_attendance.append(Student(actor_name, verb, fingerprinted, ""))
                print("For student: " + actor_name + " -> " + verb + " -> fingerprinted: " + fingerprinted +  " " )


        table_headers_html = []
        table_headers_name = []
        table_headers_html.append("student")
        table_headers_name.append("Student")
        table_headers_html.append("verb")
        table_headers_name.append("Status")
  	table_headers_html.append("fingerprinted")
        table_headers_name.append("Fingerprinted")
        table_headers_html = zip(\
        table_headers_html, table_headers_name)

        data={}

        data['yaxis'] = allstudents_statements_per_registration
	data['yaxis'] = all_students_attendance
        data['pagetitle'] = "All Students Attendance by Registration"
        data['allclass'] = allclass
        data['tabletypeid'] = "attendanceregistrationstudents"
        data['table_headers_html'] = table_headers_html
	data['registration_id'] = registration_id
	data['timestamp'] = timestamp

        return render(request, template_name, data)

	"""
        else:
            authresponse = HttpResponse(status=400)
            authresponse.write("Invalid class selected. Something went wrong.")
            return authresponse
	"""
    except Exception as e:
        print(e)
        authresponse = HttpResponse(status=500)
        authresponse.write("Reporting exception: " + str(e.message) + " Please check!")
        return authresponse




"""Report: Public Attendance Report"""
@login_required(login_url='/login/')
def attendance_process(request):
	authresponse = HttpResponse(status=500)
	authresponse.write("Nothing to show here..");
	return authresponse



"""Report: Attendance Report
"""
@csrf_exempt
def attendance_api(request):
	#Keeping it at POST because of BASIC Auth being present 
	if request.method != 'POST':
		#authresponse = HttpResponse(status=401)
        	#authresponse.write("Not a post request");
		#return authresponse
		json_response = simplejson.dumps( {
                           'error': "Not a post request"}  )
        	return HttpResponse(json_response, mimetype="application/json")
	try:
		#Get the date param filter
		date_since = request.POST['since_1_alt']
		date_until = request.POST['until_1_alt']
	except:
		#Default dates for a month before today.
		date_since = date.today() - td(days=31)
		date_until = datetime.now().date()

	#If User is not in request (not from Django)
	if request.user is None or request.user.is_anonymous():
		#Authenticate from Basic Authentication
		state, authresponse = login_basic_auth(request)
		if state == False:
			#Must be authenticated. This isn't public API
			logger.info("Didn't get user.")
			return authresponse
		if state == True:
			#set the user in request..
			request.user = authresponse
			logger.info("Got user!")
		else:
			logger.info("Umm. tia")
	
	try:
		#If organisation is explicitly declared. 
		organisation_id = request.POST['organisation_id']
		organisation = Organisation.objects.get(pk=organisation_id)
	except:

		#If org id not given, get logged in users org
		try:
			organisation = User_Organisations.objects.get(\
                       	user_userid=request.user).organisation_organisationid
		except Exception as orgex:
			logger.info(str(orgex))
			json_response = simplejson.dumps({ \
                           'error': "No organisation selected or not logged in."})
			return HttpResponse(json_response, mimetype="application/json")
		
        try:
	    	#If Classes are explicitly given
            	allclass_ids = request.POST['allclass_ids']
	except: 
		#The class ids are not given..
		#Get all classes in the organisation:
		logger.info("Getting all classes in the organisation..")
		allclass_list=Allclass.objects.filter(school__in=\
			School.objects.filter(organisation=organisation));
			
		if allclass_list is None:
			json_response = simplejson.dumps( {\
				'error': "No classes in organisation"}  )
			return HttpResponse(json_response, mimetype="application/json")
			
		allclass_ids=[]
		for everyclass in allclass_list:
			allclass_ids.append(everyclass.id);
			
		#ToDo: remove Class duplicates (if any)

	alldays_in_daterange=[]
	time_delta = (date_until - date_since)
	for i in range(time_delta.days + 1):
		this_date = date_since + td(days=i)
		alldays_in_daterange.append(this_date)
	logger.info(alldays_in_daterange)
		
				
	logger.info("Getting attendance for classes..")
	attendance_dict = {}
	try:	
            for every_class in allclass_list:
		allclass_id = str(every_class.id)
		allclass_dict = {}
		logger.info("In class: " + str(every_class.allclass_name))
				

		teacher = every_class.teachers.all().order_by('-id')[0]
		logger.info(teacher)

            	#Get all registrations unique for that class
            	#allclass_statements = models.Statement.objects.filter(\
            	#    , timestamp__range=[date_since, date_until])
            	attended_activity_string = \
				"http://www.ustadmobile.com/activities/attended-class/"
  	        activity_id_string = attended_activity_string + allclass_id
                all_activity_id_string = []
                activity_id_string2 = activity_id_string + "/"
                all_activity_id_string.append(activity_id_string)
                all_activity_id_string.append(activity_id_string2)
                all_hosted_verb_id = []
                hosted_verb_id = "http://activitystrea.ms/schema/1.0/host"
                hosted_verb_id2 = "http://activitystrea.ms/schema/1.0/host/"
                all_hosted_verb_id.append(hosted_verb_id)
                all_hosted_verb_id.append(hosted_verb_id2)
                hosted_verb = \
			models.Verb.objects.filter(verb_id__in=all_hosted_verb_id)
            	attendance_activity = models.Activity.objects.filter(\
                    activity_id__in=all_activity_id_string)

            	#Get all registrations
            	all_registrations = models.Statement.objects.filter(\
                  timestamp__range = [date_since, date_until],\
                    object_activity__in = attendance_activity,\
                        verb__in=hosted_verb).values_list(\
                                'context_registration', flat=True).distinct()


		day_stuff_dict={}
		#Lets loop through every single day in that date range..
		for each_day in alldays_in_daterange:
			logger.info("For day:" + str(each_day));
			all_registrations_thatday = models.Statement.objects.filter(\
			  timestamp__contains=each_day,\
				object_activity__in = attendance_activity,\
					verb__in=hosted_verb).values_list(\
						'context_registration', flat=True).distinct()
			if all_registrations_thatday:
				logger.info(all_registrations_thatday)


            	#print("I think I got the registrations")
            	#print(all_registrations)
		registration_dict = {}
            	for every_registration in all_registrations:
		    #registration_dict = {}
		    #allclass_dict[every_registration]
                    allclass_statements_per_registration = models.Statement.objects.filter(\
                      timestamp__range = [date_since, date_until],\
                        object_activity__in = attendance_activity,\
                            context_registration = every_registration).exclude(\
                                verb__in = hosted_verb)
            	    logger.info("In Registration : " + \
				str(every_registration))
     	    	    #logger.info(allclass_statements_per_registration)
		    allclass_registration_students_attendance = []
                    for every_statement in allclass_statements_per_registration:
			#allclass_registration_students_attendance = []
                        actor = every_statement.actor
                        actor_name = actor.name
                        if not actor_name:
                            actor_name = actor.account_name
                        verb = every_statement.verb.get_display()
                        context_extensions = every_statement.context_extensions
                        #context_extensions_json = json.loads(context_extensions)
			try:
                            fingerprinted = context_extensions[u'http://www.ustadmobile.com/fingerprinted']
			except:
			    fingerprinted = None
	
                    	if not fingerprinted:
			    studentAttendance =  Student(actor_name, verb, "")
			    studentAttendanceData = json.dumps(studentAttendance.__dict__)
			    allclass_registration_students_attendance.append(studentAttendanceData)
	
			    #allclass_registration_students_attendance.append(\
			    #	Student(actor_name, verb, "") )
                    	else:
			    studentAttendance = Student(actor_name, verb, fingerprinted)
			    studentAttendanceData = json.dumps(studentAttendance.__dict)
			    allclass_registration_students_attendance.append(studentAttendanceData)

			    #allclass_registration_students_attendance.append(\
			    #	Student(actor_name, verb, fingerprinted) )

							
		    registration_dict[every_registration] = \
			    allclass_registration_students_attendance
				
		attendance_dict[allclass_id] = registration_dict
							
		#Not sure why this is here..
		"""
            	allclass_statements = models.Statement.objects.filter(\
               	timestamp__range = [date_since, date_until],\
                object_activity__in = attendance_activity).exclude(\
                      verb__in=hosted_verb)
            	print("Got all statements too")
            	print(allclass_statements)
		"""
			
	    #logger.info(str(attendance_dict))


	    json_response = json.dumps(attendance_dict)
	    return HttpResponse(json_response, mimetype="application/json")
	    authresponse = HttpResponse(status=200)
	    authresponse.write("Yay")
	    return authresponse
        
        except Exception as e:
            print(e)
	    logger.info(str(e))
            authresponse = HttpResponse(status=500)
            authresponse.write("Reporting exception: " + e.message + " Please check!")
            return authresponse


"""Report: Attendance Report 
"""
"""
@login_required(login_url='/login/')
def attendance_process(request):
    print(request.POST)
    date_since = request.POST['since_1_alt']
    date_until = request.POST['until_1_alt']
    try:
	allclass_id = request.POST['allclass']
	allclass = Allclass.objects.get(pk=allclass_id)
	if allclass is not None:
	
	    #Get all registrations unique for that class 
	    #allclass_statements = models.Statement.objects.filter(\
            #    , timestamp__range=[date_since, date_until])
	    attended_activity_string = "http://www.ustadmobile.com/activities/attended-class/"
	    activity_id_string = attended_activity_string + allclass_id
	    all_activity_id_string = []
	    activity_id_string2 = activity_id_string + "/"
	    all_activity_id_string.append(activity_id_string)
	    all_activity_id_string.append(activity_id_string2)
	    all_hosted_verb_id = []
	    hosted_verb_id = "http://activitystrea.ms/schema/1.0/host"
	    hosted_verb_id2 = "http://activitystrea.ms/schema/1.0/host/"
	    all_hosted_verb_id.append(hosted_verb_id)
	    all_hosted_verb_id.append(hosted_verb_id2)
	    hosted_verb = models.Verb.objects.filter(verb_id__in=all_hosted_verb_id)
	    print("all hosted verbs:")
	    print(hosted_verb)
	    print("here we go..")
	    attendance_activity = models.Activity.objects.filter(\
		activity_id__in=all_activity_id_string)
	    print("Got it")
	    print(attendance_activity)

	    #Get all registrations 
	    all_registrations = models.Statement.objects.filter(\
		timestamp__range = [date_since, date_until],\
		    object_activity__in = attendance_activity,\
			verb__in=hosted_verb).values_list(\
				'context_registration', flat=True).distinct()
	    print("I think I got the registrations")
	    print(all_registrations)

	    for every_registration in all_registrations:
		allclass_statements_per_registration = models.Statement.objects.filter(\
		    timestamp__range = [date_since, date_until],\
			object_activity__in = attendance_activity,\
			    context_registration = every_registration).exclude(\
				verb__in = hosted_verb)
		print("All student statements for Registration : " + str(every_registration))
		print(allclass_statements_per_registration)
		for every_statement in allclass_statements_per_registration:
		    actor = every_statement.actor
		    actor_name = actor.name
		    if not actor_name:
			actor_name = actor.account_name
		    verb = every_statement.verb.get_display()
		    context_extensions = every_statement.context_extensions
		    #context_extensions_json = json.loads(context_extensions)
		    fingerprinted = context_extensions[u'http://www.ustadmobile.com/fingerprinted']
		    if not fingerprinted:
		        print("For student: " + actor_name + "->" + verb +  " " )
		    else:
			print("For student: " + actor_name + " -> " + verb + " -> fingerprinted: " + fingerprinted +  " " )
		

	    allclass_statements = models.Statement.objects.filter(\
		timestamp__range = [date_since, date_until],\
		    object_activity__in = attendance_activity).exclude(\
			verb__in=hosted_verb)
	    print("Got all statements too")
	    print(allclass_statements)

	    authresponse = HttpResponse(status=200)
    	    authresponse.write("Yay")
    	    return authresponse
	else:
	    authresponse = HttpResponse(status=200)
            authresponse.write("Invalid class selected. Something went wrong.")
            return authresponse
    except Exception as e: 
	print(e)
	authresponse = HttpResponse(status=200)
        authresponse.write("Reporting exception: " + e.message + " Please check!")
        return authresponse
"""


	
"""Report: Duration Report
This report shows the range and parameter selection page for 
rendering the duration report
"""
@login_required(login_url='/login/')
def durationreport_selection(request):
	logger.info("User="+request.user.username+\
	    	" accessed /reports/durationreport_selection/")
	organisation = User_Organisations.objects.get(\
		user_userid=request.user).organisation_organisationid
	current_user = request.user.username + " (" + \
	    	organisation.organisation_name + ")"
	current_user_role = User_Roles.objects.get(user_userid=\
				request.user.id).role_roleid.role_name;
	current_user = "Hi, " + request.user.first_name + ". You are a " +\
		current_user_role + " in " + organisation.organisation_name +\
		    " organisation."
	return render_to_response('duration_report_05_selection.html',\
	    {'current_user':current_user}, context_instance = RequestContext(request))

"""Mockup Report: 
Not used anymore
"""
#@login_required(login_url='/login/')
def response_report_selection(request):
	try:
	    organisation = \
		User_Organisations.objects.get(user_userid=request.user).organisation_organisationid
            current_user = \
		request.user.username + " (" + organisation.organisation_name + ")"
            current_user_role = \
		 User_Roles.objects.get(user_userid=request.user.id).role_roleid.role_name;
            current_user = "Hi, " + request.user.first_name + ". You are a " + current_user_role \
		 + " in " + organisation.organisation_name + " organisation."
	except:
	    current_user = "Hello Guest!"
	    return render(request, 'mockup_report_07_selection.html', {'current_user':current_user})
        return render_to_response('mockup_report_07_selection.html', {'current_user':current_user},
                                context_instance = RequestContext(request))

"""Report: Duration Report
This report will give a 2 level (School to Class) 
breakdown of everything from the begenning of time
to the present in terms of duration added up in 
seconds. The new Usage report is currently used and does 
a better job at it, however this is taken directly from 
the statements and it can offer a good comparison and 
check.
"""
@login_required(login_url='/login/') 
def durationreport(request, template_name='duration_report_05.html'):
    if request.method != 'POST':
	return redirect('durationreport_selection')

    date_since = request.POST['since_1_alt']
    date_until = request.POST['until_1_alt']
    user_selected = request.POST.getlist('model')

    logger.info("User="+request.user.username+" accessed /reports/durationreport/")
    if True:
        date_since = datetime.strptime(date_since[:10], '%Y-%m-%d')
        date_until = datetime.strptime(date_until[:10], '%Y-%m-%d')
        #"new datetime dates converted from unicode to datetime"
        delta=(date_until - date_since)
        xaxis=[]
        yaxis=[]
        label_legend=[]
        user_by_duration=[]
        user_duration=0
        if "ALL" in user_selected:
                allclassid=request.POST['brand']
                allclassid=int(allclassid)
                allclass_class = Allclass.objects.get(id=allclassid)
                users_with_statements = allclass_class.students.all().values_list('id', flat=True)
        else:
                users_with_statements = user_selected #Just assuming so. Should re work naming convention

	last_activity=[]
        for i in range(delta.days +1):
                current_date=date_since + td(days=i)
                xaxis.append(str(current_date.strftime('%b %d, %Y')))
        for user_id_with_statement in users_with_statements:
		user_duration=0
                user_with_statement=User.objects.get(id=user_id_with_statement)
                label_legend.append(user_with_statement.first_name + " " + user_with_statement.last_name)
                useryaxis=[]
                for i in range(delta.days +1):
                        current_date=date_since + td(days=i)
                        all_statements_current_date = models.Statement.objects.filter(\
				user=user_with_statement, timestamp__year=current_date.year,\
				    timestamp__month=current_date.month, timestamp__day=current_date.day)
                        current_duration=0
                        for every_statement_current_date in all_statements_current_date:
				try:
                                	current_duration=current_duration + \
					    int(every_statement_current_date.get_r_duration().seconds)
				except:
					current_duration=current_duration + 0
                        if current_duration == 0 :
                                current_duration=0
                        useryaxis.append(current_duration)
                        user_duration=user_duration+current_duration
                user_by_duration.append(td(seconds=user_duration))
                yaxis.append(useryaxis)
		try:
			a=models.Statement.objects.filter(user=user_with_statement,\
				 object_activity__activity_definition_type__icontains=\
				     "activities/module").latest("timestamp")
			b=a.object_activity.get_a_id() + " - " + \
				a.object_activity.get_a_name() + \
				    " : " + str(a.timestamp.strftime('%b %d, %Y'))
		except:
			b="-"
		last_activity.append(b)
        #Reduction by help of a fellow stack overflow use: 
        #http://stackoverflow.com/questions/25656550/
	#remove-occuring-elements-from-multiple-lists-shorten-multiple-lists-by-value/25656674#25656674
        num_zeroes = len(list(takewhile(lambda p: p == 0, max(yaxis))))-1
        yaxis=[li[num_zeroes:] for li in yaxis]
        xaxis=xaxis[num_zeroes:]
        yaxis=zip(label_legend, yaxis, user_by_duration, users_with_statements, last_activity)
        data={}
        data['xaxis']=xaxis;
        data['yaxis']=yaxis
        data['date_since']=date_since
        data['date_until']=date_until


	data['pagetitle']="UstadMobile Usage Report Statements"
    	data['tabletypeid']="durationreportdynatable"
    	table_headers_html=[]
    	table_headers_name=[]

    	table_headers_html.append("user")
    	table_headers_name.append("User")
    	table_headers_html.append("duration")
   	table_headers_name.append("Duration")
 	table_headers_html.append("last_activity")
	table_headers_name.append("Last activity")

    	table_headers_html = zip(table_headers_html, table_headers_name)
	data['table_headers_html']=table_headers_html

    return render(request, template_name, data)

"""Common Method: To Get All Students in current user's org
"""
@login_required(login_url="/login/")
def get_all_students_in_this_organisation(request):
    organisation = User_Organisations.objects.get(\
                user_userid=request.user).organisation_organisationid
    try:
	users=[]
	allschools=School.objects.filter(organisation=organisation)
        for everyschool in allschools:
            allclassesfromthisschool=Allclass.objects.filter(\
                                     school=everyschool)
            for allclass in allclassesfromthisschool:
                allstudentsinthisallclass=allclass.students.all()
                for s in allstudentsinthisallclass:
                    if s not in users:
                        users.append(s)
	return users
    except:
	logger.info("Something went wrong get getting all students in this organisation")
	return None

"""Common Method: Get all Blocks in current user's Org
"""
@login_required(login_url="/login/")
def get_all_blocks_in_this_organisation(request):
    organisation = User_Organisations.objects.get(\
                user_userid=request.user).organisation_organisationid
    try:
	if organisation.organisation_name=="ChildFund":
		blo = Block.objects.filter(success="YES", \
		    publisher__in=User.objects.filter(pk__in=\
			User_Organisations.objects.filter(\
			    organisation_organisationid=organisation\
				).values_list('user_userid', flat=True)))
		blocks=[]
		#print(Course.objects.get(name="Afghan-Literacy").packages.all())
		ab=Course.objects.get(name="Afghan-Literacy").packages.all()
		for b in blo:
		    blocks.append(b)
		for a in ab:
		    blocks.append(a)
	else:
		blocks = Block.objects.filter(success="YES", \
		    publisher__in=User.objects.filter(pk__in=\
			User_Organisations.objects.filter(\
			    organisation_organisationid=organisation\
				).values_list('user_userid', flat=True)))
        return blocks 
    except:
        logger.info("Something went wrong in"+\
	    " getting all blocks in this organisation")
        return None

"""Common Method: Calculates statment based on indicators:
   users, blocks and date range
To Do: Update duration return to account for blocks and test statement 
To Do: Delete duplicate statements in relevant_statements
"""
def calculate_statements(students, date_since, date_until, blocks):
    delta=(date_until - date_since)
    total_duration=0
    user_by_duration=[]
    all_statements=[]
    all_statements_blocked=[]

    print("Blocks (length):")
    print(len(blocks))

    all_statements=[]
    all_statements_blocked=[]

    """
    all_statements=models.Statement.objects.filter(\
	user__in=students, timestamp__range=[date_since, date_until])
    print("All statement length without block filter:")
    print(len(all_statements))
    all_statementsinfo = models.StatementInfo.objects.filter(\
	statement__in=all_statements, block__in=blocks)
    """
    all_statementsinfo=models.StatementInfo.objects.filter(\
	user__in=students, timestamp__range=[date_since, date_until], block__in=blocks)
    print("New statemtns length with block filter:")
    print(len(all_statementsinfo))

    """
    for asi in all_statementsinfo:
        all_statements_blocked.append(asi.statement)
    """


    """
    for each_statement in all_statements:
	try:
	    q=models.StatementInfo.objects.get(statement=each_statement).block
	    if q in blocks:
		rel_statement.append(each_statement)
    """
    """
    for student in students:
	student_statements=[]
	for i in range(delta.days +1):
            current_date=date_since + td(days=i)
	    student_statements_timeframe = models.Statement.objects.filter(\
		user=student, timestamp__year=current_date.year, \
		timestamp__month=current_date.month, \
		timestamp__day=current_date.day)
	    for everystatement in student_statements_timeframe:
	    	if everystatement:
			student_statements.append(everystatement)
	if student_statements:
	    for ss in student_statements:
		if ss not in all_statements:
		    all_statements.append(ss)
	for stall in all_statements:
	    #try:
	    if True:
		a=None
		try:
			a=models.StatementInfo.objects.get(statement=stall).block
		except:
			a=None
		if a in blocks:
			if stall not in all_statements_blocked:
			    all_statements_blocked.append(stall)
	
	    	#if models.StatementInfo.objects.get(statement=stall, block__in=blocks):
		#    all_statements_blocked.append(ss)
	    #except:
	    else:
		pass

    """
	
    #To calculate the duration in all of these statements per user
    """
        current_duration=0
        for every_statement in student_statements:
                try:
                        current_duration=current_duration + int(\
			    every_statement.get_r_duration().seconds)
                except:
                        current_duration=current_duration + 0
        user_duration=current_duration
        user_by_duration.append(td(seconds=user_duration))
        total_duration=total_duration+user_duration
    """
    user_by_duration=None
    #return all_statements_blocked, user_by_duration
    return all_statementsinfo, user_by_duration

"""Common Method: Gets Blocks and Coures by users given
"""
"""
def get_blocks_courses_by_user(users):
    #try:
    if True:
	blocks_by_user=[]
	courses_by_user=[]
	#This does not work properly. Check.
	for user in users:
	    user_blocks=[]
	    allclasses_by_user=Allclass.objects.filter(students=user)
	    uc=Course.objects.filter(allclasses__in=allclasses_by_user)
	
	    for course in uc:
		allblocks=course.packages.all()
		for allblock in allblocks:
		    user_blocks.append(allblock)
	    #Ignoringn 
	    #uc=Course.objects.filter(students=user)
	    blocks_by_user.append(user_blocks)
 	    courses_by_user.append(uc)
    	return blocks_by_user, courses_by_user
    #except:
    else:
	return None
"""

"""Common Method: Get Statement Group Entry Object Details
"""
def get_sge_details(obj):
    json_objects = [{'objectName': o.get_objectType_name(),
                           'total_duration':str(td(seconds=o.total_duration)),
			   'children': get_sge_details(o)}\
				for o in obj.child_groups]
    return json_objects

"""Report: Usage Report Selection Render
 This is the function that is called when the user
 asks for a usage reports
"""
@login_required(login_url="/login/")
def test_usage_report(request):
    logger.info("User="+request.user.username+" accessed /reports/usage_report/")
    organisation = User_Organisations.objects.get(\
		user_userid=request.user).organisation_organisationid
    current_user_role = User_Roles.objects.get(\
		user_userid=request.user.id).role_roleid.role_name;
    current_user = "Hi, " + request.user.first_name + ". You are a "\
		 	+ current_user_role + " in " + \
			organisation.organisation_name \
		        + " organisation."
	
    return render_to_response('usage_report_06.html', {'current_user':current_user},
                                context_instance = RequestContext(request))

"""Common Method: Used by duration report to calculate duration for a list of
users by looking at the statements themseleves. This wil be depricated once statements
and users are assigned to courses and blocks in statement info to full full 
the statement generator object for reporting.
"""
def calculate_duration_nodate(students):
        total_duration=0
	user_by_duration=[]
        for student in students:
                user_duration=0
                all_statements = models.Statement.objects.filter(user=student)
                current_duration=0
                for every_statement in all_statements:
                        try:
                                current_duration=current_duration + int(every_statement.get_r_duration().seconds)
                        except:
                                current_duration=current_duration + 0
                user_duration=current_duration
                user_by_duration.append(td(seconds=user_duration))
                total_duration=total_duration+user_duration
	return user_by_duration, total_duration

    
"""Report: BreakDown Report Logic
Used to render a breakdown report that is old style and doesnt need
course and blocks to search. Generates a breakdown tree table report
directly looking at the satatmenets for users in the organisation 
and the duration. This will be depricated once statements and users 
are assigned to courses and blocks to full fill the statement generator
object. 
"""
@login_required(login_url="/login/")
def test_heather_report(request, template_name='breakdown_report_08.html'):
    organisation = User_Organisations.objects.get(\
				user_userid=request.user\
				).organisation_organisationid
    current_user_role = User_Roles.objects.get(\
			user_userid=request.user.id\
			).role_roleid.role_name;
    current_user = "Hi, " + request.user.first_name + ". You are a " \
		+ current_user_role + " in " + organisation.organisation_name \
		+ " organisation."
    allschools=School.objects.filter(organisation=organisation)
    school_by_duration=[]
    allclasses_by_duration=[]
    school_allclasses=[]
    data={}
    for school in allschools:
	allstudents=[]
	user_by_duration=[]
	allclasses = Allclass.objects.filter(school=school)
        school_allclasses.append(allclasses)
	allclass_by_duration=[]
	user_allclass_by_duration=[]
	for allclass in allclasses:
	    students=allclass.students.all()

	    #Adding everything for school calculation
	    for student in students:
	    	allstudents.append(student)

	    user_allclass_by_duration, allclass_duration = \
					calculate_duration_nodate(students)
            allclass_by_duration.append(allclass_duration)

 	allclasses_by_duration.append(allclass_by_duration)
	#Calculating total duration for all students in the school
	user_by_duration, school_duration = calculate_duration_nodate(allstudents)
	school_by_duration.append(school_duration)
    allclasses_details=zip(school_allclasses, allclasses_by_duration)
    trial=[]
    for x,y in allclasses_details:
	z=zip(x,y)
	trial.append(z)
    data['current_user']=current_user;
    data['school_details']=zip(allschools, school_by_duration,trial)

    return render(request, template_name, data)


"""Report: Usage Report Ajax Handler
This view is called when usage report submit button is clicked. This renders a JSON 
that is fetched back by the page to render the usage report within the same page.
"""
@login_required(login_url="/login/")
def usage_report_data_ajax_handler(request):
    logger.info("User="+request.user.username+" submitted a request to /reports/usagereport/")

    if request.method == 'POST':
	print("Handling POST request..")
        date_since = request.POST['since_1_alt']
        date_until = request.POST['until_1_alt']
        #Changing the time into something that statement can 
        #understand (sans time and in YYYY-MM-DD format)
        date_since = datetime.strptime(date_since[:10], '%Y-%m-%d')
        date_until = datetime.strptime(date_until[:10], '%Y-%m-%d')

        #Report type will be either table/on
        reporttype=request.POST['radiotype']
        if reporttype == "on":
            reporttype="chart"

        #Some processing on the list of users obtained.
        #We put this into an array to find and figure out where the id
        #comes from
        usersjstreefields = request.POST.getlist('usersjstreefields')
        usersjstreefields = usersjstreefields[0].split(',')

        #we do something similar for blocks.
        coursesjstreefields = request.POST.getlist('coursesjstreefields')
        coursesjstreefields = coursesjstreefields[0].split(',')

        userids =[]
        users=[]

        #Looping over users to get user list
        for userjstreefields in usersjstreefields:
                if "allschools" in userjstreefields:
                        allusersflag = True
                        users=get_all_students_in_this_organisation(request)
                        if users is None:
                                logger.info("Something went wrong. No users in school.")
                        break
                else:
                        typestring=userjstreefields.split('|')[1]
                        idstring=userjstreefields.split('|')[0]
                        if "school" in typestring:
                            schoolid=int(idstring)
                            allclassesfromthisschool=Allclass.objects.filter(\
                                                        school__id=schoolid)
                            for allclass in allclassesfromthisschool:
                                allstudentsinthisallclass=allclass.students.all()
                                for s in allstudentsinthisallclass:
                                    if s not in users:
                                        users.append(s)
                        elif "class" in typestring:
                            allclassid=int(idstring)
                            allclass=Allclass.objects.get(id=allclassid)
                            allstudentsinthisallclass=allclass.students.all()
                            for stu in allstudentsinthisallclass:
                                if stu not in users:
                                    users.append(stu);
                        elif "user" in typestring:
                            userid = int(idstring)
                            user=User.objects.get(id=userid)
                            if user not in users:
                                users.append(user)
                        else:
                            logger.info("Something went wrong, couldn't judge")

                        allusersflag = False

        blocks=[]
        for coursejstreefields in coursesjstreefields:
            if "allcourses" in coursejstreefields:
                allcoursesflag = True
                blocks=get_all_blocks_in_this_organisation(request)
		print("Selected All courses. The Blocks are:")
		print (blocks)
                if blocks is None:
                        logger.info("Something went wrong in getting blocks for org")
                break
            else:
                allcoursesflag = False
                typestring=coursejstreefields.split('|')[1]
                idstring=coursejstreefields.split('|')[0]
                if "course" in typestring:
                    courseid=int(idstring)
                    course = Course.objects.get(id=courseid)
                    course_blocks = course.packages.all()
                    for cb in course_blocks:
                        if cb not in blocks:
                            blocks.append(cb)
                elif "package" in typestring:
                    blockid=int(idstring)
                    block_block = Block.objects.get(id=blockid)
                    if block_block not in blocks:
                        blocks.append(block_block)
                else:
                    logger.info("Something went wrong. couldn't judge")

        #looping over indicators to figure out which all indicators is needed.
        #each indicator will be 'on' or False
	indicators = []
        try:
            avgscore=request.POST['avgscore']
        except:
            avgscore=False
        try:
            avgduration=request.POST['avgduration']
        except:
            avgduration = False
        try:
            totalduration=request.POST['totalduration']
        except:
            totalduration=False
        indicators.append(totalduration)
        indicators.append(avgduration)
        indicators.append(avgscore)
        
        #Now we get statements based on timestamp range, users (and in future blocks)
        #relevant_statements for all users [statement1, statement2]
        #users = [ Bob, Adonbilivit ] (User)
        #user_by_duration = [ 10, 11 ](TimeDuration)
        #blocks_by_user, courses_by_user = get_blocks_courses_by_user(users)
        relevant_statements_info=[]
	print("Calculating relevant statements..")
        relevant_statements_info, user_by_duration=calculate_statements(\
                                users, date_since, date_until, blocks)
	print("Done Calculating statements")

	print('\n')
        print(date_since)
        print(date_until)
        print(reporttype)
	print("No. of users:")
        print(len(users))
        print(len(blocks))
        print(indicators)
        print("All statements:")
        print(len(relevant_statements_info))
        #print(user_by_duration) 

	print("\n")
        #Push this to the statement Grouping
        #   (Statements, objectVal, level, parent, objectType)
	print("Starting root")
        root = StatementGroupEntry(relevant_statements_info, None, 0, None, None)
	print("Done with rooting")
        grouping = [School(), Allclass(), User()]
	print("Starting grouping..")
        group_em(0, root, grouping, indicators)
	print("Finished Grouping")

	json_object=[]
	for child in root.child_groups:
	    a=get_sge_details(child)
	    json_obj = {
			'objectName':child.get_objectType_name(),
			'total_duration':str(td(seconds=child.total_duration)),
			'children':a}
	    json_object.append(json_obj)
	json_object_json=simplejson.dumps(json_object)
	#print(json_object_json)

	return HttpResponse(json_object_json, mimetype="application/json")

    
    else:
        logger.info("Not a POST request brah, check your code.")
	return HttpResponse(False)

"""Add values to workshet row
"""
def worksheet_add_values_to_row(worksheet,values, row, format):
    i=0;
    for every_value in values:
	i=i+1;
	worksheet.write(row, i, every_value, format);
    return worksheet
    

"""Report: Survey Report Selection
"""
@login_required(login_url='/login/')
def survey_selection(request):
        logger.info("User="+request.user.username+\
                " accessed /reports/survey_selection/")
        organisation = User_Organisations.objects.get(\
                user_userid=request.user).organisation_organisationid
        current_user = request.user.username + " (" + \
                organisation.organisation_name + ")"
        current_user_role = User_Roles.objects.get(user_userid=\
                                request.user.id).role_roleid.role_name;
        current_user = "Hi, " + request.user.first_name + ". You are a " +\
                current_user_role + " in " + organisation.organisation_name +\
                    " organisation."
	blocks = Block.objects.filter(success="YES", \
    		publisher__in=User.objects.filter(pk__in=\
		User_Organisations.objects.filter(\
    		organisation_organisationid=organisation\
		).values_list('user_userid', flat=True)))
	print("Blocks: ")
	print(blocks)

	template_name="survey_report_selection.html"
	data={}
	data['current_user'] = current_user
	data['blocks'] = blocks
	return render(request, template_name, data)


"""Report: Registration Report (Survey Report)
   This report will be made for registration event statements 
   that are part of the organisation. 
"""
@login_required(login_url="/login/") 
def registration_statements_tincanxml(request,\
 	template_name='registration_statements_tincanxml.html'):
    logger.info("User="+request.user.username+\
	" accessed /reports/registrations_report_tincanxml/")
    organisation = User_Organisations.objects.get(\
	user_userid=request.user).organisation_organisationid;

    """	
	1. Get all users in this organisation
	2. Get all statements for every user
	3. Get all statements that have reqistration
	4. Get all unique registrations from the statements and group them
	5. 

    OR:
	1. Get all users and get all statements with registration id

    """

    if request.method != 'POST':
    	return redirect('survey_selection')

    date_since = request.POST['since_1_alt']
    date_until = request.POST['until_1_alt'] 
    block_id =   request.POST['blocks']
    block = Block.objects.get(pk=block_id)
    logger.info("Block selected: " + str(block.name))
    #Get all users in the current organisation
    all_org_users= User.objects.filter(pk__in=\
	User_Organisations.objects.filter(\
	    organisation_organisationid=organisation\
		).values_list('user_userid', flat=True))

    #Get all statements made by those users
    """
    Get all statements made by those users in that time range
    """
    all_statements = models.Statement.objects.filter(user__in=all_org_users, \
		timestamp__range = [date_since, date_until]).order_by('-timestamp')

    """
    Fix for statements (new) that don't get assigned to any block. 
    """
    logger.info("Fixing statements (if any)")
    for every_statement in all_statements:
        statement_json=every_statement.full_statement
        try:
	    blockn = models.StatementInfo.objects.get(statement=\
						every_statement).block
            blockname=blockn.name        
	    if blockn != block:
		continue
	    try:
		coursen=models.StatementInfo.objects.get(statement=\
						every_statement).course
		try:
		    coursename=coursen.name
		except:	
		    esi=models.StatementInfo.objects.get(\
					statement=every_statement)
		    esicourse = Course.objects.get(packages=esi.block)
		    if esi.course == None and esicourse != None:
                        esi.course = esicourse
                        esi.save()
	    except:
		try:
			#logger.info("Cant find Course assigned to statement: " + str(every_statement.id) + " , fixing..");
			esi = models.StatementInfo.objects.get(\
				statement=every_statement)
			esicourse = Course.objects.get(packages=esi.block)
			if esi.course == None and esicourse != None:
				esi.course = esicourse
				esi.save()
		except:
			logger.info("Cannot find Course for the block: " +\
				str(esi.block.id) + " for statement: " + \
					str(every_statement.id))
	
	
        except: #If no block is assigned to this statementinfo
	    logger.info("Fixing statement: " + str(every_statement.id))
            try:
                context_parent = statement_json[u'context'][u'registration']
                #("Reg id:" + str(context_parent))
                activity_id=statement_json[u'object']['id']
                elpid=activity_id.rsplit('/',1)[1]
		#("Statement id: " + str(every_statement.id))
                try:
                    if "um_assessment" in elpid or unicode("um_assessment") in elpid:
                        elpid=elpid[:-13]
                        block = Block.objects.get(elpid=elpid, success="YES", active = True, \
			  publisher__in=User.objects.filter(\
			    pk__in=User_Organisations.objects.filter(\
				organisation_organisationid=organisation\
				    ).values_list('user_userid', flat=True)))
                        si = models.StatementInfo.objects.get(
						statement=every_statement)
                        if si.block == None and block != None:
                            logger.info("Statement is going to be updated and \
				assigned block: " + block.name)
                            si.block = block
                            si.save()

                            for e in all_statements:
                                fs = e.full_statement
                                try:
                                    registrationid=\
					fs[u'context'][u'registration']
                                    if str(registrationid) == \
					str(context_parent) and block != None:
                                        esi = models.StatementInfo.objects.get(\
						statement=e)
                                        if esi.block == None:
                                            esi.block = block
                                            logger.info("Statement: " + \
						str(e.id) + \
						    " should be of block: " +\
							 block.name)
                                            esi.save()
                                except:
				    logger.info("Unable to assign")
			else:
			    logger.info("elp id unmatch..")
		except:
			logger.info("Unable to fix that.")

            except:
		pass
	        #logger.info("Something went wrong in getting activity id " +\
	        #	"and or context parent " + str(every_statement.id))

    """
    End of fix.
    """

    logger.info("On to generating the report..")

    dict_reg = dict() #This is all the registration statements grouped by red id.
    #ordered_dict_reg = OrderedDict()
    school_dict = dict() #These are all the registration ids grouped by school id.
    #Group this by registration id 
    appLocation=(os.path.dirname(os.path.realpath(__file__)))
    timestamp=time.strftime("%Y%m%d%H%M%S")

    """
    Declare the Survey report (previously known as Registration report) 's name
    """
    registration_report_file = appLocation + \
	'/../UMCloudDj/media/registration_report/registration_report_tincan_' + timestamp + '.csv'
    registration_report_xlsx_file = appLocation + \
	'/../UMCloudDj/media/registration_report/registration_report_tincan_' + timestamp + '.xlsx'
	
    registration_report_filename = 'registration_report/registration_report_tincan_' + timestamp + '.csv'
    registration_report_xlsx_filename = 'registration_report/registration_report_tincan_' + timestamp + '.xlsx'

    """
    Touch (file) the csv version - Not used. Replaced by excel version
    """
    g = open(registration_report_file, 'w')
    now = time.strftime("%c")
    g.write("Registration Report from " + str(date_since) + " to " + (date_until) + '\n')
    column_names = "ID|Item|Value|User|Block|Date"
    column_readable_names = column_names
    column_names_list = ["ID", "Item", "Value", "User", "Block", "Date"]

    """
    Touch and set the excel version of the report
    """
    workbook = xlsxwriter.Workbook(registration_report_xlsx_file)
    worksheet_report = workbook.add_worksheet("Report")
    worksheet_report.write('A1', 'Registration Report from ' + str(date_since) + " to " + str(date_until) + ".")
    worksheet_test = workbook.add_worksheet("Notes")
    bold = workbook.add_format({'bold':True})
    format = workbook.add_format()
    format.set_align('justify')
    worksheet_report.set_column('A:F', 10, format)
    worksheet_report.set_column('G:Z', 25, format)
    worksheet_report.set_row(1, 45)
    
    logger.info("Generating Registration report (based on tincan.xml)")
    sorted_keys = []

    """
    This loop will ready all relevant registration statements for this report
    and group them by registration id - by storing it in a dict

    We're basically mapping statements to their registration ids. That way we 
    are grouping the statements that were made together in that registration 
    (by id). Using dict. So its: 
	dict_reg[reg_id] = {statement1, statement2, ..}
    Note: The statement have been moved from JSON to a pip delimited string for
	better parsing
    """
    for every_statement in all_statements:

	#Get statement JSON for processing and the user
	statement_json=every_statement.full_statement
	user=every_statement.user

	#Get block name
 	try:
	    blockn=models.StatementInfo.objects.get(statement=\
					every_statement).block
	    blockname=blockn.name
	    
	    if blockn != block:
		#Skipping this statement cus it haz no block assigned to it
		continue
	except:
	    #Skipping cuz cudnt figure out block 
	    blockname="-"
	    continue
	
	#Get Context Parent
        try:
            context_parent = statement_json[u'context'][u'registration']
	except:
	    context_parent = None
	    continue #Not in this statement iteration. Go to the next one

	if context_parent == None or context_parent == "":
	    continue #Not in this statement iteration. Go to the next one

	#Get the activity Name
	try:
	    activity_name = statement_json[u'object'][u'definition'][u'name'][u'en-US']
	except:
	    activity_name = ""

	#Get the activity ID
	try:
	    activity_id= statement_json[u'object']['id']
	    username = every_statement.user.username
	except:
	    continue #No id then can't do anything. Go to the next iteration
	
	#Get the Result and Score
	try:
	    result = statement_json[u'result'][u'response']
	except:
	    result = ""
	try:
	    result_score = statement_json[u'result'][u'score'][u'raw']
	except:
	    result_score = result
	    result_score = ""


	#dict_reg is grouped by the registration id. 
	#If this is for an existing registration, we add the activity id to it.
	if context_parent in dict_reg:
	    dict_reg[context_parent].append(\
		activity_name + "|" + str(result) + "|" + str(result_score) + "|" + activity_id +\
	    	  "|"+username+"|" + str(blockn.id) + "|" + blockname+"|"+\
		    every_statement.timestamp.strftime(\
			"%B %d %Y %H:%M"))
		   
	else:
	    sorted_keys.append(context_parent)
	    dict_reg[context_parent] = [activity_name + "|" + \
		str(result) + "|" + str(result_score) + "|" + activity_id +"|"+username+"|" + \
		    str(blockn.id) + "|" + blockname+"|"+every_statement.timestamp.strftime(\
			"%B %d, %Y %H:%M")]
	    

    made_column_name_row = False
    column_name_number_mapping = {}
    activity_id_name_mapping = {}
    #Update: We want to order the added MCQ columns
    every_regid_index = 3

    """
    This loop will loop through every regsitration (by reg id) and get all
    activities from its associated epub blocks' tincan.xml and order the
    statements in that order of the tincan.xml activities for that reg id
    in order so that they look ordered. 
	1. Get Block for the reg group
	2. Get activities in that block's epub's tincan.xml and get the order
	3. Arrange the statements in the reg dict for that reg id group

    Basically order the dictionary by tincan.xml
    """
    #for every_regid in dict_reg:
    for every_regid in sorted_keys:
	every_regid_index = every_regid_index + 1
	logger.info("In reg: " + str(every_regid))
	#1
        statements = dict_reg.get(every_regid.encode('utf8'))
  	first_statement = statements[0]
	blockid = first_statement.split('|')[5]
	blockn = Block.objects.get(pk=blockid)
	this_username = first_statement.split('|')[4]
	timestamp = first_statement.split('|')[7]
	appLocation = (os.path.dirname(os.path.realpath(__file__)))
        serverlocation=appLocation+'/../'
        mainappstring = "UMCloudDj/"
	epub_file_path = serverlocation + mainappstring \
                    + settings.MEDIA_URL + str(blockn.exefile)
	logger.info("Epub file path: " + epub_file_path)
	try:
            epubfilehandle = open(epub_file_path, 'rb')
            epubasazip = zipfile.ZipFile(epubfilehandle)
    	except Exception as e:
            logger.info("!!Could Not open epub file")
	    logger.info(e)
	    result = "fail"
	    return render(request, template_name,{'object_list':dict_reg,\
                'result':result} )

	#2
	activities_inorder = []
	tincanprefix = ""
	"""
	Get activities in tincan.xml file in order and store it in an array
	"""
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
				activities_inorder.append(activityid)
				#typeid = activitieselement.attrib['type']
				typeid="test"
	
                            except:
				logger.info("exception..")
                                epubfilehandle.close()

                            else:
				
                                if activityid != "" and activityid != None and typeid != "" and typeid != None:
                                    for activityelement in activitieselement:
                                        if "description" in activityelement.tag:
					    pass
                                            #description = str(activityelement.text)
                                            #lang = str(activityelement.attrib['lang'])
					if "name" in activityelement.tag:
					    name = activityelement.text
						
					    epub_id_bit=activityid[activityid.find("epub:")+len("epub:"):activityid.find("/")]
                        		    a = activityid.find("/")
                        		    if a < 0:
                                		continue
                        		    if not epub_id_bit:
                                		continue
                          		    epub_id = "epub:" + epub_id_bit;
                        		    rel_activity_id = activityid.split(epub_id)[1]

					    if activityid in activity_id_name_mapping:
						pass
					    else:
						activity_id_name_mapping[rel_activity_id] = name
					    pass
				    if typeid=="http://adlnet.gov/expapi/activities/course":
					tincanprefix = activityid
				    
                                    if tincanprefix != "":
                                        logger.info("Found prefix!" + str(tincanprefix))
			    try:
				epubfilehandle.close()
			    except:
				logger.info("Cant close epubfilehandle")
					
	try:
	    epubfilehandler.close()
	except:
	    pass

	#logger.info("Name-Activity ID mapping: ") 
	#logger.info(activity_id_name_mapping)

	#3
	"""
	Arranging statements in order (to make it look better)
	"""
	statements_inorder=[]
	statements_activities_inorder = []
        for every_statement in statements:
	    statement_activityid = every_statement.split('|')[3]
	    try:
	    	# A very crude way of sorting.
	    	activity_index = activities_inorder.index(statement_activityid)
	    	statements_inorder.insert(activity_index, every_statement)
	    	statements_activities_inorder.insert(activity_index, statement_activityid)
	    except ValueError:
		#For somereason the activity id with page might not be in the list
		# of activities from the tincan.xml file. We ignore this
		pass

	#logger.info("For this reg_id: # of Statements|# of Statements In Order|# of Statement's Activities In Order")
	#logger.info(str(len(statements))+"|"+str(len(statements_inorder))+"|"+str(len(statements_activities_inorder)))

	"""
	Report File: Updating column name in the report 
	"""
	if made_column_name_row == False:
		logger.info("Updating column name row..")
		column_number = 7 #Cuz the first 6 populated with other info (ID, Item, Value, User, Block, Date
		for every_activity in activities_inorder:
			#Reminder: column_names = "ID|Item|Value|User|Block|Date"

			#Getting relative activity id 
			epub_id_bit=every_activity[every_activity.find("epub:")+len("epub:"):every_activity.find("/")]
			a = every_activity.find("/")
			if a < 0:
				continue
			if not epub_id_bit:
				continue
			epub_id = "epub:" + epub_id_bit;
			relative_activity_id = every_activity.split(epub_id)[1]
			
			readable_name = activity_id_name_mapping.get(relative_activity_id)
			column_names = column_names + "|" + relative_activity_id; #Not really used 

			#Make readable names for report
			if not readable_name:
				readable_name = relative_activity_id
			column_readable_names = column_readable_names + "|" + readable_name
			#column_name_number_mapping[column_number] = relative_activity_id 
			column_name_number_mapping[column_number] = every_activity #note we didnt use relative because below we search by the whole activiy id
			#CBB changing it.
			
			column_number = column_number + 1
			column_names_list.append(readable_name)

			
		#logger.info("column_readable_names: " + column_readable_names);
    		g.write('\n' + column_readable_names.encode('utf8') + '\n');
		worksheet_report = worksheet_add_values_to_row(worksheet_report, column_names_list, 1, format)
		made_column_name_row = True

	#logger.info("Column Name-Column Number mapping:")
	#logger.info(column_name_number_mapping)

	"""
	Main report logic: Process each statements (of the current registration) which are in order
	We check what kind of statements they are. We are currently looking for two types:
	1. choice (MCQ questions)
	2. fill-in (Fill in the blanks: Text Entry questions/activities)
	
	We are creating a score mapping of this registration's score/result mapped to the activity id
	We do not add cause we want unique ones 
	
	"""
	reg_activity_score_mapping = {}
 	for every_statement in statements_inorder:
	    #TODO: Add check for type of statement: MCQ or fill-in
	    result = every_statement.split('|')[1]
	    result_score = every_statement.split('|')[2]
	    activity_name = every_statement.split('|')[0]
	    activity_id = every_statement.split('|')[3]
	    exact_timestamp = every_statement.split("|")[7]
	    if activity_id.startswith(tincanprefix): #tincanprefix is prefix for this epub from the tincan.xml file
		activity_id = activity_id[len(tincanprefix):]

	    #AFAIK: Not used
	    result_on_report = ""
	    if result_score != "":
		result_on_report = result + " Score: " + result_score 
		activity_name = "MCQ " + activity_id #AFAIK not used
	    if result != "":
		result_on_report = result
		
	    if result_score != "":
		result_report = result_score
	    else:
		result_report = result

	    #logger.info("Getting sum for activity id: " + activity_id)
	    if activity_id in reg_activity_score_mapping:
		try:
		    activity_id_score = int(reg_activity_score_mapping[activity_id])
		    #reg_activity_score_mapping[activity_id] = int(reg_activity_score_mapping[activity_id]) + int(result_score)

		    #reg_activity_score_mapping[activity_id] = int(result_score) #Don't sum it up, take the latest one
		    reg_activity_score_mapping[activity_id] = result_report
		except:
		    pass
	    else:
		try:
		    #reg_activity_score_mapping[activity_id] = int(result_score)
		    reg_activity_score_mapping[activity_id] = result_report
		except:
		    pass
		

	logger.info("Registration's Activity - Score mapping")
	logger.info(reg_activity_score_mapping)

	new_registration_list = ["","New", "Registration", this_username, blockn.name, timestamp]
	column_score = ""
	column_score_list = []
	for every_column_number in column_name_number_mapping:
		#activity_id = column_name_number_mapping[every_column]
		activity_id = column_name_number_mapping.get(every_column_number)
		total_score = reg_activity_score_mapping.get(activity_id.encode('utf8'))
		#total_score = reg_activity_score_mapping[activity_id]
		if total_score != None:
			column_score = column_score + "|" + str(total_score)
			column_score_list.append(total_score)
			new_registration_list.append(total_score)
		else:
			column_score = column_score +"|" + ""
			column_score_list.append("")
			new_registration_list.append("")

		
	"""
	logger.info("New Reg List:")
	logger.info(new_registration_list)
	logger.info("Column Score List:")
	logger.info(column_score_list)
	"""

	g.write("|" + "New" + "|Registration|" + this_username + "|" + blockn.name + "|" + timestamp  + column_score + '\n' )
	g.write('\n' + '\n')
	
	#Add to index: every_regid_index
	#new_registration_list = ["","New", "Registration", this_username, blockn.name, timestamp, column_score]
	worksheet_report = worksheet_add_values_to_row(worksheet_report, new_registration_list, every_regid_index, format)
	every_regid_index = every_regid_index + 1;

	dict_reg[every_regid] = statements_inorder #Dont need this

    all_reg_ids=dict_reg.keys() #Don't need this
    regidsalldone=[] #Don't need this
    regidsdone=[] #Don't need this

    g.close()
    workbook.close()

    result="success"
    return render(request, template_name,{'object_list':dict_reg,\
    	'result':result, 'registration_report_filename':registration_report_filename,\
	'registration_report_xlsx_filename':registration_report_xlsx_filename} )



# Create your views here.

		
		
class AttendanceRepresentation(object):
	students_male = 0;
	students_female = 0;
	teachers_male = 0;
	teachers_female = 0;
	
	days_attended_teachers_male = 0;
	days_absent_teachers_male = 0;
	days_attended_teachers_female = 0;
	days_absent_teachers_female = 0;
	
	days_attended_students_male = 0;
	days_absent_students_male = 0;
	days_attended_students_female = 0;
	days_absent_students_female = 0;
	
	def __init__(self, sm, sf, tm, tf, datm, dabtm, datf, dabtf, dasm, dabsm, dasf, dabsf):
		self.students_male = sm;
		self.students_female = sf;
		self.teachers_male = tm;
		self.teachers_female = tf;
		
		self.days_attended_teachers_male = datm;
		self.days_absent_teachers_male = dabtm;
		self.days_attended_teachers_female = datf;
		self.days_absent_teachers_female = dabtf;
		
		self.days_attended_students_male = dasm;
		self.days_absent_students_male = dabsm;
		self.days_attended_students_female = dasf;
		self.days_absent_students_female = dabsf;

	

"""Report: Attendance Public API Report
	OUTPUT JSON:
		{
		   "schools":[
			  {
				 "name":"Pluto School",
				 "gps":"latlong",
				 "attendance":[
					{
					   "date":"yyyy-mm-dd",
					   "teachers":{
						  "male":{
							 "days_attended":50,
							 "days_absent":10
						  },
						  "female":{
							 "days_attended":50,
							 "days_absent":10
						  }
					   },
					   "students":{
						  "male":{
							 "days_attended":50,
							 "days_absent":10
						  },
						  "female":{
							 "days_attended":50,
							 "days_absent":10
						  }
					   }
					}
				 ]
			  }
		   ]
		}
"""
@csrf_exempt
def attendance_public_api(request):
	logger.info("Public Attendance API request..")
        #Keeping it at POST because of BASIC Auth being present
        if request.method != 'POST':
                json_response = simplejson.dumps( {
                           'error': "Not a post request"}  )
		#Skipping for now
                return HttpResponse(json_response, mimetype="application/json")
        try:
                #Get the date param filter
                date_since = request.POST['since_1_alt']
                date_until = request.POST['until_1_alt']
		logger.info("Dates got:")
		logger.info(date_since)
		logger.info(date_until)
		logger.info(type(date_since))
		logger.info("To Date converstion: ")
		date_since = datetime.strptime(date_since[:10], '%Y-%m-%d').date()
        	date_until = datetime.strptime(date_until[:10], '%Y-%m-%d').date()
		logger.info(date_since)
		logger.info(date_until)
		logger.info(type(date_since))
        except:
		logger.info("Getting date exception. Taking default one month..")
                #Default dates for a month before today.
                date_since = date.today() - td(days=31)
                date_until = datetime.now().date();

		
		#Disabling for public api - Data open to public
		#Checks basic auth and authenticates it.
        #If User is not in request (not from Django)
        if request.user is None or request.user.is_anonymous():
                #Authenticate from Basic Authentication
                state, authresponse = login_basic_auth(request)
                if state == False:
                        #Must be authenticated.
						#If no user, basic auth in request then org id should be there.
                        logger.info("Didn't get user. Organisation id must be specified")

                if state == True:
                        #set the user in request..
                        request.user = authresponse
                        logger.info("Got user!")
                else:
                        logger.info("Umm. tia")
		

		#Get organisation if explicitly declared in POST param
		# else get logged in user's organisation
        try:
                #If organisation is explicitly declared.
                organisation_id = request.POST['organisation_id']
                organisation = Organisation.objects.get(pk=organisation_id)
        except:
                #If org id not given, get logged in users org 
				#Will always go here in Public API
                try:
						#This will fail in public API: We need a  organisation ID
                        organisation = User_Organisations.objects.get(\
                        user_userid=request.user).organisation_organisationid
                except Exception as orgex:
                        logger.info(str(orgex))
                        json_response = simplejson.dumps({ \
                           'error': "No organisation selected or not logged in."})
                        return HttpResponse(json_response, mimetype="application/json")

		#In the future we have to group by schools.
		#TODO: Group by School
		#This may have been done below.
		
		#Group by Class:
		#Get classes if classes are explicitly declared in POST param
        try:
                #If Classes are explicitly given
                allclass_ids = request.POST['allclass_ids']
        except:
                #The class ids are not given..
                #Get all classes in the organisation:
                logger.info("Getting all classes in the organisation..")
                allclass_list=Allclass.objects.filter(school__in=\
                        School.objects.filter(organisation=organisation));

                if allclass_list is None:
                        json_response = simplejson.dumps( {\
                                'error': "No classes in organisation"}  )
                        return HttpResponse(json_response, mimetype="application/json")

                allclass_ids=[]
                for everyclass in allclass_list:
                        allclass_ids.append(everyclass.id);
        	#TODO: remove Class duplicates (if any) from the list 
			
		#Group by School:
		#Get all schools if schools are explicitly declared in POST param
		try:
			removed = False
			logger.info("Getting school ids in POST request..");
                	#If Schools are explicitly given
                	school_ids = request.POST.getlist('school_ids[]')
			logger.info("School IDs Given:")
			logger.info(school_ids)
			for every_id in school_ids:
				try:
					this_school = School.objects.get(pk=every_id)
					#Optional (in future for non public to check if authorized.
				except:
					logger.info("Couldn't find that school. Skipping.")
					if every_id == 'Z':
						raise Exception("All Schools selected.");
					school_ids.remove(every_id)
					removed = True
			if not school_ids:
				logger.info("School list is empty. Throwing exception")
				raise Exception("School list is empty, Not valid ids or unauthorized access.");
			if removed:
				logger.info("Some Schools were removed becuase they were not valid schools.")
			
				
        	except Exception as school_ex:
                	#The school ids are not given..
                	#Get all schools in the organisation:
			logger.info("Can't get school ids in POST:");
			logger.info(str(school_ex))
                	logger.info("Getting all schools in the organisation..")
                	school_list=School.objects.filter(organisation=organisation);
			#school_list = School.objects.filter(organisation=organisation);
			if not school_list:
				json_response = simplejson.dumps( {\
					'error': "No schools in organisation"}  )
				return HttpResponse(json_response, mimetype="application/json")
				
                	if school_list is None:
                        	json_response = simplejson.dumps( {\
                                	'error': "No schools in organisation"}  )
                        	return HttpResponse(json_response, mimetype="application/json")

                	school_ids=[]
                	for everyschool in school_list:
                        	school_ids.append(everyschool.id);
				
		#ToDo: remove School duplicates (if any) from the list
				

		#Get attendance by school
		
		#For every day between the two dates
		#ToDo: excluding weekends ?
		
		alldays_in_daterange=[]
        	time_delta = (date_until - date_since)
        	for i in range(time_delta.days + 1):
                	this_date = date_since + td(days=i)
                	alldays_in_daterange.append(this_date)
		
		for each_day in alldays_in_daterange:
			print("For day:" + str(each_day));
			#yeah we know this works. Delete this.
		
		#Start here..
		
		#Get the attendance by School
		try:
			school_dict={}
			for every_school_id in school_ids:
				try:
					every_school = School.objects.get(pk=every_school_id)
					logger.info("In School: " + str(every_school.school_name))
				except Exception as e:
					print(e)
					logger.info(str(e))
					authresponse = HttpResponse(status=500)
					authresponse.write("Invalid school id:" + \
						str(every_school_id) + " given: " + e.message + " Please check!")
					return authresponse
				
				every_schools_allclass_list = Allclass.objects.filter(school=every_school)
				if not every_schools_allclass_list: #No classes in school
					#logger.info("School: " + str(every_school_id) + " has no classes in it. Skipping")
					continue #..to next for every school loop 
					

				school_holidays = Holiday.objects.filter(holiday_calendar_holiday=every_school.holidays.all()).values_list('date', flat=True)
				if not school_holidays:
					try:
						school_holidays = organisation.calendar.holidays.all().values_list('date', flat=True)
					except:
						school_holidays = []
				
				date_dict = {}
				#date_dict[date] = Attendance data 
				#Lets loop through every single day in that date range..
				for each_day in alldays_in_daterange:
					weekends = every_school.weekends.all()
					each_day_dayid = date.weekday(each_day) + 1
					each_day_day = Weekday.objects.get(pk=each_day_dayid)
					if each_day_day in weekends:
						#logger.info("Weekend!")
						continue

					"""Disabling because the holiday check is at class level.
					It goes from class check -> school check - > Org check
					if each_day_day in school_holidays:
						continue
					"""

					every_school_each_day_students_male = 0;
					every_school_each_day_students_female = 0;
					every_school_each_day_teachers_male = 0;
					every_school_each_day_teachers_female = 0;
					
					every_school_each_day_students_present_male = 0;
					every_school_each_day_students_present_female = 0;
					every_school_each_day_teachers_present_male = 0;
					every_school_each_day_teachers_present_female = 0;
					
					every_school_each_day_students_absent_male = 0;
					every_school_each_day_students_absent_female = 0;
					every_school_each_day_teachers_absent_male=0;
					every_school_each_day_teachers_absent_female=0;
					
					every_school_each_day_attendance = AttendanceRepresentation(\
							every_school_each_day_students_male, every_school_each_day_students_female,\
							every_school_each_day_teachers_male, every_school_each_day_teachers_female,\
							every_school_each_day_teachers_present_male, every_school_each_day_teachers_absent_male,\
							every_school_each_day_teachers_present_female, every_school_each_day_teachers_absent_female,\
							every_school_each_day_students_present_male, every_school_each_day_students_absent_male,\
							every_school_each_day_students_present_female, every_school_each_day_students_absent_female);
					#every_school_each_day = AttendanceRepresentation(0,0,0,0,0,0,0,0,0,0,0,0);
					each_day_dict={}
					
					#Loop through all classes in the school (for every day as this is in everyday loop)
					for every_class in every_schools_allclass_list:
						#logger.info("In Class: " + every_class.allclass_name);
						days = every_class.days.all()
						days_week_days =[]
						allclass_holidays = Holiday.objects.filter(\
							holiday_calendar_holiday=\
								every_class.holidays.all()).values_list('date', flat=True)

						if not allclass_holidays:
							allclass_holidays = school_holidays

						for each_day_time in days: 
							days_week_days.append(each_day_time.day)
						if each_day_day not in days_week_days:
							#logger.info("Class not supposed to be active today.")
							#logger.info(days_weeek_days)
							continue
						if each_day_day in allclass_holidays:
							continue

						#That starts with a date group by object:
						every_class_attendance_data_by_date = {}
							
						every_class_students_male = 0;
						every_class_students_female = 0;
						every_class_teachers_male = 0;
						every_class_teachers_female = 0;
						
						every_class_students_present_male = 0;
						every_class_students_present_female = 0;
						every_class_teachers_present_male = 0;
						every_class_teachers_present_female = 0;
						
						every_class_students_absent_male = 0;
						every_class_students_absent_female = 0;
						every_class_teachers_absent_male=0;
						every_class_teachers_absent_female=0;
						
						"""
						every_class_each_day_attendance = AttendanceRepresentation(\
							every_class_students_male, every_class_students_female,\
							every_class_teachers_male, every_class_teachers_female,\
							every_class_teachers_present_male, every_class_teachers_absent_male,\
							every_class_teachers_present_female, every_class_teachers_absent_female,\
							every_class_students_present_male, every_class_students_absent_male,\
							every_class_students_present_female, every_class_students_absent_female);
						every_class_each_day_attendance = AttendanceRepresentation(0,0,0,0,0,0,0,0,0,0,0,0);
						"""
						
						allclass_id = str(every_class.id)
						allclass_dict = {}

						#Get the objects needed for class attendance data:
						attended_activity_string = \
										"http://www.ustadmobile.com/activities/attended-class/"
						activity_id_string = attended_activity_string + allclass_id
						all_activity_id_string = []
						activity_id_string2 = activity_id_string + "/"
						all_activity_id_string.append(activity_id_string)
						all_activity_id_string.append(activity_id_string2)
						all_hosted_verb_id = []
						hosted_verb_id = "http://activitystrea.ms/schema/1.0/host"
						hosted_verb_id2 = "http://activitystrea.ms/schema/1.0/host/"
						all_hosted_verb_id.append(hosted_verb_id)
						all_hosted_verb_id.append(hosted_verb_id2)
						hosted_verb = \
								models.Verb.objects.filter(verb_id__in=all_hosted_verb_id)

						attendance_activity = models.Activity.objects.filter(\
							activity_id__in=all_activity_id_string)
							
						#Get all registrations made
						all_registrations_thatday = models.Statement.objects.filter(\
						  timestamp__contains=each_day,\
								object_activity__in = attendance_activity,\
										verb__in=hosted_verb).values_list(\
												'context_registration', flat=True).distinct()
						if all_registrations_thatday:
							#logger.info(all_registrations_thatday)
							pass
						if not all_registrations_thatday:
							#Teacher didn't do it. So he/she is absent 
							#TODO: Account for holidays and weekend!
							#okay thinking here. what if there are more than one teacher assigned to the same class.
							# In that case who is the one who is absent ? Are all teachers everyday or not ?
							
							#Solution: Just assume one teacher per class for now. 
							teachers_in_class = every_class.teachers.all()
							teacher_in_class = teachers_in_class[0]
							teacher_in_class_gender = UserProfile.objects.get(user=teacher_in_class).gender
							if teacher_in_class_gender == "M":
								#every_class_each_day_attendance.days_absent_teachers_male = \
								#	every_class_each_day_attendance.days_absent_teachers_male + 1;
								#TODO: replace others (not required)..

								every_class_teachers_absent_male = every_class_teachers_absent_male + 1;


								#Also mark all students absent
							elif teacher_in_class_gender == "F" :
								#every_class_each_day_attendance.days_absent_teachers_female = \
								#	every_class_each_day_attendance.days_absent_teachers_female + 1;
	
								every_class_teachers_absent_female = every_class_teachers_absent_female + 1;
							
								#Also mark all students absent

							#We have to make students as absent. This is because the way we calculate attendance
							# is based on the absent and present difference. In this case the teacher is absent
							# So while we dont have absent/present info data about the students, we must assume
							# that the students are absent since no attendance was taken, no teacher attended,
							# and hence no students were attended. 
						
							#Get student list for this class
							# Loop through every student, get its gender
							# Assign a +1 for male, female
							all_students_in_this_class = every_class.students.all();
							for every_student in all_students_in_this_class:
								every_student_gender = UserProfile.objects.get(user=every_student).gender;
								if every_student_gender == "M":
									every_class_students_male = every_class_students_male + 1;
									every_class_students_absent_male   = every_class_students_absent_male   + 1;
								if every_student_gender == "F":
									every_class_students_female = every_class_students_female + 1;
									every_class_students_absent_female = every_class_students_absent_female + 1;
							
						registration_dict = {}
						
						for every_registration in all_registrations_thatday:
							allclass_statements_per_registration = models.Statement.objects.filter(\
							  #timestamp__contains = each_day,\ #Why limit . maybe rest of the stms came later
								object_activity__in = attendance_activity,\
									context_registration = every_registration).exclude(\
										verb__in = hosted_verb)
							#logger.info("In Registration : " + \
							#	str(every_registration))
							allclass_registration_students_attendance = []
							
							for every_statement in allclass_statements_per_registration:
								actor = every_statement.actor
								actor_name = actor.name
								if not actor_name:
									actor_name = actor.account_name
								verb = every_statement.verb.get_display()
								context_extensions = every_statement.context_extensions
								student_username = every_statement.actor.account_name
								try:
									student_user = User.objects.get(username=student_username)
									student_gender = UserProfile.objects.get(user=student_user).gender;
								except:
									student_gender = "M";
								
								if student_gender == "M":
									every_class_students_male = every_class_students_male + 1;
									#every_class_each_day_attendance.students_male = \
									#	every_class_each_day_attendance.students_male + 1;
									if verb == "Skipped":
										every_class_students_absent_male = every_class_students_absent_male + 1;
									elif verb == "Attended":
										every_class_students_present_male = every_class_students_present_male + 1;
									
								elif student_gender == "F":
									every_class_students_female = every_class_students_female + 1;
									if verb == "Skipped":
										every_class_students_absent_female = every_class_students_absent_female + 1;
									elif verb == "Attended":
										every_class_students_present_female = every_class_students_present_female + 1;
								
								teacher = every_statement.user
								teacher_gender = UserProfile.objects.get(user=teacher).gender
								if teacher_gender == "M":
									every_class_teachers_male = every_class_teachers_male + 1;
									every_class_teachers_present_male = every_class_teachers_present_male + 1;
								elif teacher_gender == "F":
									every_class_teachers_female = every_class_teachers_female +1;
									every_class_teachers_present_female = every_class_teachers_present_female + 1;
								
								#Quesiton is how to mark teachers as absent ?
									
								#context_extensions_json = json.loads(context_extensions)
								try:
									fingerprinted = context_extensions[u'http://www.ustadmobile.com/fingerprinted']
								except:
									fingerprinted = None

								if not fingerprinted:
									studentAttendance =  Student(actor_name, verb, "", student_gender)
									studentAttendanceData = json.dumps(studentAttendance.__dict__)
									allclass_registration_students_attendance.append(studentAttendanceData)

									#allclass_registration_students_attendance.append(\
									#   Student(actor_name, verb, "") )
								else:
									studentAttendance = Student(actor_name, verb, fingerprinted, student_gender)
									studentAttendanceData = json.dumps(studentAttendance.__dict)
									allclass_registration_students_attendance.append(studentAttendanceData)

									#allclass_registration_students_attendance.append(\
									#   Student(actor_name, verb, fingerprinted) )
								# We have studentAttendance object

								#TODO: What about the students that are assigned to this class but are not
								# in the attendance statments list. We have to scan through them and mark 
								# them as absent. The sheet could only be giving the first few students attendance
								# And we dont then account for the remaining. Although if students are not part of 
								# the class anymore then we should make sure the teachers remove them from the class.
							
						#Add an attendance by date
						"""
						every_class_each_day_attendance = AttendanceRepresentation(\
							every_class_students_male, every_class_students_female,\
							every_class_teachers_male, every_class_teachers_female,\
							every_class_teachers_present_male, every_class_teachers_absent_male,\
							every_class_teachers_present_female, every_class_teachers_absent_female,\
							every_class_students_present_male, every_class_students_absent_male,\
							every_class_students_present_female, every_class_students_absent_female);
						"""
						
						
						every_school_each_day_students_male = \
							every_school_each_day_students_male + every_class_students_male;
						every_school_each_day_students_female = \
							every_school_each_day_students_female + every_class_students_female;
						every_school_each_day_teachers_male = \
							every_school_each_day_teachers_male + every_class_teachers_male ;
						every_school_each_day_teachers_female = \
							every_school_each_day_teachers_female + every_class_teachers_female;

						every_school_each_day_students_present_male = \
							every_school_each_day_students_present_male + every_class_students_present_male;
						every_school_each_day_students_present_female = \
							every_school_each_day_students_present_female + every_class_students_present_female ;
							
						every_school_each_day_teachers_present_male =\
							every_school_each_day_teachers_present_male + every_class_teachers_present_male;
						every_school_each_day_teachers_present_female = \
							every_school_each_day_teachers_present_female + every_class_teachers_present_female;

						every_school_each_day_students_absent_male = \
							every_school_each_day_students_absent_male + every_class_students_absent_male;
						every_school_each_day_students_absent_female = \
							every_school_each_day_students_absent_female + every_class_students_absent_female;
						every_school_each_day_teachers_absent_male = \
							every_school_each_day_teachers_absent_male + every_class_teachers_absent_male;
						every_school_each_day_teachers_absent_female = \
							every_school_each_day_teachers_absent_female + every_class_teachers_absent_female;
					
	
					every_school_each_day_attendance = AttendanceRepresentation(\
							every_school_each_day_students_male, every_school_each_day_students_female,\
							every_school_each_day_teachers_male, every_school_each_day_teachers_female,\
							every_school_each_day_teachers_present_male, every_school_each_day_teachers_absent_male,\
							every_school_each_day_teachers_present_female, every_school_each_day_teachers_absent_female,\
							every_school_each_day_students_present_male, every_school_each_day_students_absent_male,\
							every_school_each_day_students_present_female, every_school_each_day_students_absent_female);
					

					#studentAttendanceData = json.dumps(studentAttendance.__dict__) 
					every_school_each_day_attendance_data = \
						json.dumps(every_school_each_day_attendance.__dict__)
					
					#This as a whole object:
					#date_dict[each_day] = every_school_each_day_attendance
					#This as string:
					date_dict[str(each_day)] = json.loads(every_school_each_day_attendance_data)
				#We have date_dict completely filled.
				
				school_dict[str(every_school_id)] = date_dict
			authresponse = HttpResponse(status=200)
			authresponse.write("Reporting calc done. This should go..")
			authresponse.write("\n")
			authresponse.write(school_dict)
			#return authresponse
			json_response = json.dumps(school_dict)
			return HttpResponse(json_response, mimetype="application/json")
					
		
		except Exception as e:
            		print(e)
            		logger.info(str(e))
            		authresponse = HttpResponse(status=500)
            		authresponse.write("Reporting exception: " + e.message + " Please check!")
            		return authresponse
	
		

class SchoolNumbers(object):
	total_students = 0;
	total_teachers = 0;
	total_classes = 0;
	def __init__(self, ts, tt, tc):
		self.total_students = ts
		self.total_teachers = tt
		self.total_classes = tc


"""Report: Usage Report Selection Render
"""
#@login_required(login_url="/login/")
def public_attendance_report(request):
    logger.info(" A User="+" accessed /reports/public_attendance_report/")
    try:
        org_id = request.GET.get('orgid')
	organisation = Organisation.objects.get(pk=org_id)
	school_list = School.objects.filter(organisation = organisation)
	school_deets = {}
	#Calculate number of students
	for every_school in school_list:

		allclasses = Allclass.objects.filter(school=every_school)
		student_count = 0
		teacher_count = 0
		allclass_count = 0
		for every_class in allclasses:
			student_list = every_class.students.all()
			student_count = student_count + len(student_list)
			teacher_list = every_class.teachers.all()
			teacher_count = teacher_count + len(teacher_list)
		allclass_count = len(allclasses)
		every_school_number = SchoolNumbers(student_count, teacher_count, allclass_count)
		school_deets[str(every_school.id)] = every_school_number
	
	#calculate number of Teachers
    except:
	#No org id specified
	school_list = None
	organisation = None
	school_deets = None
	return redirect('home')

    return render_to_response('public_attendance_report.html', {'school_list' : school_list, 'organisation':organisation, 'school_number' : school_deets},
                                context_instance = RequestContext(request))

