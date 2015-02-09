from django.shortcuts import render
from datetime import datetime, timedelta as td
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

# Create your views here.
