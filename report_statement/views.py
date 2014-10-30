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

from django import template
from django.core import serializers
import simplejson
from itertools import takewhile

from lrs import forms, models, exceptions
from lrs.util import req_validate, req_parse, req_process, XAPIVersionHeaderMiddleware, accept_middleware, StatementValidator
from oauth_provider.consts import ACCEPTED, CONSUMER_STATES
from django.forms.models import model_to_dict

# This uses the lrs logger for LRS specific information
logger = logging.getLogger(__name__)

### This function will initiate and loop over the groupings 
### and assign the statements to groups
### It will also initiate indicators to be calculated
### By:group_em(0, root, ['School','Class'], [on,False,False]])
def group_em(level, stmtGroup, grouping, indicators):
    #print("Stating grouping Level: " + str(level))
    stmtGroup.sub_group_by(grouping[level])
    if indicators[0] != False:
	stmtGroup.get_total_duration()
	for everychild in stmtGroup.child_groups:
 	    #Indicator calculation call for total Duration
	    everychild.get_total_duration() 
    if level < len(grouping)-1:
        for child in stmtGroup.child_groups:
            group_em(level+1, child, grouping, indicators)

### StatementGroupEntry is the group entry custom object
### made for the sole purpose of storing grouped statements
### relevant to the report query made / set.
### Groupings can be further grouped and certain indicators
### can be calculated on them like time, result, average
### Also makes rendering easier by its functions.
class StatementGroupEntry():  
    
    def __init__(self, statements, objectVal, level, parent, objectType):
        self.statements = statements 
        self.objectVal = objectVal
        self.level = level
	self.objectType = objectType
	self.child_groups=[]
	self.total_duration=0 #in seconds
	self.average_score=0 #
	self.average_duration_users=[]
  
    def get_objectType_name(self):
	if isinstance(self.objectType, School):
            objectName=self.objectType.school_name + " School"
        elif isinstance(self.objectType, Allclass):
            objectName=self.objectType.allclass_name + " Class"
        elif isinstance(self.objectType, User):
            objectName=self.objectType.first_name + " " + self.objectType.last_name + " User"
        elif isinstance(self.objectType, Block):
            objectName=self.objectType.name + " Block"
        elif isinstance(self.objectType, Course):
            objectName=self.objectType.name + " Course"
	else:
	    objectName="-"
	return objectName


    def jdefault(self):
	json_objects = simplejson.dumps( [{
                           'objectName': o.get_objectType_name(),
                           'total_duration':o.total_duration} for o in self.child_groups] )
	return json_objects

    
    def sub_group_by(self, objectType):
	try:
	    all_statementinfo = models.StatementInfo.objects.filter(statement__in=self.statements)

            if len(all_statementinfo) != len(self.statements):
		if len(list(set(all_statementinfo))) != len(list(set(self.statements))):
		    logger.info("!!Something went wrong. Statements and statementinfo unique count does not match")
		else:
		    logger.info("~You may have duplicate results coming in for grouping")
	except:
	    logger.info("!!Couldnt not fetch statement info")

	applicable_stmts=[]
	all_statementinfo = models.StatementInfo.objects.filter(statement__in=self.statements)
	
	"""
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
	#if objectType == "School":
	    #We first get all the schools from the statements
	    schools=all_statementinfo.values('school').distinct()
	    for schooldict in schools:
		school_statements=models.Statement.objects.filter(\
			id__in=models.StatementInfo.objects.filter(\
			    statement__in=self.statements,school__id=schooldict['school']).\
				values_list('statement', flat=True))
		applicable_stmts.append(school_statements)
		#subGroup = StatementGroupEntry(school_statements, self.objectVal, self.level+1, self, 'School')
		school=School.objects.get(id=schooldict['school'])
		subGroup = StatementGroupEntry(school_statements, self.objectVal, self.level+1, self, school)
		self.child_groups.append(subGroup)

	#elif objectType == "Class":
	if isinstance(objectType, Allclass):
	    #We first have to get all of the classes from the statements
	    all_statementinfo = models.StatementInfo.objects.filter(statement__in=self.statements)
	    allclasses=all_statementinfo.values('allclass').distinct()
	    for allclassdict in allclasses:
		allclass_statements=models.Statement.objects.filter(\
		    id__in=models.StatementInfo.objects.filter(\
			statement__in=self.statements, allclass__id=allclassdict['allclass']).\
			    values_list('statement', flat=True))
		applicable_stmts.append(allclass_statements)
		allclass=Allclass.objects.get(id=allclassdict['allclass'])
	        #subGroup=StatementGroupEntry(allclass_statements, self.objectVal, self.level+1, self,'Class')
		subGroup=StatementGroupEntry(allclass_statements, self.objectVal, self.level+1, self, allclass)
	        self.child_groups.append(subGroup)

	if isinstance(objectType, User):
	#elif objectType == "User":
	    #We first have to get all the users from the statements
	    users = all_statementinfo.values('user').distinct()
	    for userdict in users:
		user_statements=models.Statement.objects.filter(\
		    id__in=models.StatementInfo.objects.filter(\
			statement__in=self.statements, user__id=userdict['user']).\
			    values_list('statement', flat=True))
		applicable_stmts.append(user_statements)
		user=User.objects.get(id=userdict['user'])
		#subGroup=StatementGroupEntry(user_statements, self.objectVal, self.level+1, self, 'User')
		subGroup=StatementGroupEntry(user_statements, self.objectVal, self.level+1, self, user)
		self.child_groups.append(subGroup)

	if isinstance(objectType, Course):
	#elif objectType == "Course":
	    #We first have to get all the courses from the statements
	    courses = all_statementinfo.values('course').distinct()
	    for coursedict in courses:
		course_statements=models.Statement.objects.filter(\
		    id__in=models.StatementInfo.objects.filter(\
			statement__in=self.statements, course__id=coursedict['course']).\
			    values_list('statement', flat=True))
	    	applicable_stmts.append(course_statements)
		course=Course.objects.get(id=coursedict['course'])
	  	#subGroup=StatementGroupEntry(course_statements, self.objectVal, \
						#self.level+1, self, 'Course')
		subGroup=StatementGroupEntry(course_statements, self.objectVal, \
                                                self.level+1, self, course)
                self.child_groups.append(subGroup)

	if isinstance(objectType, Block):
	#elif objectType == "Block":
            #We first have to get all the courses from the statements
            objects = all_statementinfo.values('block').distinct()
            for objectdict in objects:
                object_statements=models.Statement.objects.filter(\
                    id__in=models.StatementInfo.objects.filter(\
                        statement__in=self.statements, block__id=objectdict['block']).\
                            values('statement', flat=True))
                applicable_stmts.append(object_statements)
		theobject=Block.objects.get(id=objectdict['block'])
                #subGroup=StatementGroupEntry(object_statements, self.objectVal,\
						 #self.level+1, self, 'Block')
		subGroup=StatementGroupEntry(object_statements, self.objectVal,\
                                                 self.level+1, self, theobject)
                self.child_groups.append(subGroup)
		
	else:
	    pass
	    #print("No object Type left/given.")

    def add_child(child_group):
        child_groups.append(child_group)
    
    def get_total_duration(self):
	total_duration=0
	for statement in self.statements:
	    duration=statement.get_r_duration()
	    #try:
	    if True:
		if duration != "-":
	    	    total_duration=total_duration + int(statement.get_r_duration().seconds)
			
	    #except:
		#pass
	    #total_duration=total_duration+models.StatementInfo.objects.get(statement=statement).duration
	self.total_duration=total_duration
	return total_duration
	    
        #loop over all statements and sum duration

@login_required(login_url="/login/")    #added by Varuna
def show_statements_from_db(request,template_name='statements_db_01.html'):
    if request.user.is_staff == False:
	return redirect('reports')
    all_statements=models.Statement.objects.all()
    data={}
    return render(request, template_name,{'all_statements':all_statements} )

@login_required(login_url="/login/")    #Added by varuna
def statements_db_dynatable(request,template_name='statements_db_02.html'):
    logger.info("User="+request.user.username+" accessed /reports/allstatements/")
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid;
    all_org_users= User.objects.filter(pk__in=User_Organisations.objects.filter(organisation_organisationid=organisation).values_list('user_userid', flat=True))
    all_statements = models.Statement.objects.filter(user__in=all_org_users)
    #all_statements=models.Statement.objects.filter(id=749)
    data={}
    pagetitle="All statements from my organisation"
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
    table_headers_html.append("course_name")
    table_headers_name.append("Course")
    table_headers_html.append("block_name")
    table_headers_name.append("Block")
    table_headers_html.append("duration")
    table_headers_name.append("Duration")
    table_headers_html.append("timestamp")
    table_headers_name.append("Time")

    table_headers_html = zip(table_headers_html, table_headers_name)
    logicpopulation = "{\"user\":\"{{c.user.first_name}} {{c.user.last_name}}\",\"activity_verb\":\"{{c.verb.get_display}}\",\"activity_type\":\"{{c.object_activity.get_a_name}}\",\"timestamp\":\"{{c.timestamp}}\"},\"duration\":\"{{c.result_duration}}\""

    return render(request, template_name,{'object_list':all_statements, 'table_headers_html':table_headers_html, 'pagetitle':pagetitle, 'tabletypeid':tabletypeid, 'logicpopulation':logicpopulation} )


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
    logicpopulation = "{\"user\":\"{{c.user.first_name}} {{c.user.last_name}}\",\"activity_verb\":\"{{c.verb.get_display}}\",\"activity_type\":\"{{c.object_activity.get_a_name}}\",\"timestamp\":\"{{c.timestamp}}\"},\"duration\":\"{{c.result_duration}}\""

    return render(request, template_name,{'object_list':all_statements, 'table_headers_html':table_headers_html, 'pagetitle':pagetitle, 'tabletypeid':tabletypeid, 'logicpopulation':logicpopulation} )

@login_required(login_url="/login/")
def all_statements_table(request, userid, template_name='user_statements_report_04.html'):
    #, date_since, date_until):
    requestuser=request.user
    try:
        user=User.objects.get(id=userid)
    except:
	logger.info("User="+request.user.username+" tried to access a false user's statements")
	return redirect('reports')
    
    logger.info("User="+request.user.username+" accessed " +user.username+ " statements at /reports/durationreport/getstatements/"+str(user.id)+"/")
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
    logicpopulation = "{\"user\":\"{{c.user.first_name}} {{c.user.last_name}}\",\"activity_verb\":\"{{c.verb.get_display}}\",\"activity_type\":\"{{c.object_activity.get_a_name}}\",\"timestamp\":\"{{c.timestamp}}\"},\"duration\":\"{{c.result_duration}}\""
    return render(request, template_name,{'object_list':all_statements, 'table_headers_html':table_headers_html, 'pagetitle':pagetitle, 'tabletypeid':tabletypeid, 'logicpopulation':logicpopulation} )


@login_required(login_url="/login/")
def allclasse_students(request, allclassid):
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid
    allclasses=Allclass.objects.filter(school__in=School.objects.filter(organisation=organisation));
    allclass_class = Allclass.objects.get(id=allclassid)
    if allclass_class in allclasses:
        student_list =allclass_class.students.all()
        #json_students = serializers.serialize("json", student_list)
	#Not sending complete user object to avoid someone hacking and getting user information like encrypted password, roles and all other information. This only returns id and first and last name which is checked by request.user's logged in account anyway.
	json_students = simplejson.dumps( [{'id': o.id,
                           'first_name': o.first_name,	
			    'last_name':o.last_name} for o in student_list] )
        return HttpResponse(json_students, mimetype="application/json")
    else:
        logger.info("Class requested not part of request user's organisation. Something is fishy")
        return HttpResponse(None)

@login_required(login_url='/login/')
def allcourses_blocks(request):
    try:
	allcourseid=request.GET.get('id')
    	organisation = User_Organisations.objects.get(\
	    	user_userid=request.user).organisation_organisationid
    	allcourse_course = get_object_or_404(Course, pk=allcourseid)
	allcourses_organisation = Course.objects.filter(\
					organisation=organisation)
	if allcourse_course not in allcourses_organisation:
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


@login_required(login_url='/login/')
def school_allclasses(request):
    try:
	schoolid=request.GET.get('id')
	organisation = User_Organisations.objects.get(\
		user_userid=request.user).organisation_organisationid
	school = get_object_or_404(School, pk=schoolid)
	if school.organisation != organisation:
		logger.info("That school does not exist in your organisation")
  		return HttpResponse("That school does not exist in your organisation")
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
	    

@login_required(login_url='/login/')
def allcourses(request):
    try:
     	organisation = User_Organisations.objects.get(user_userid=request.user)\
		.organisation_organisationid
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
	
"""
@login_required(login_url='/login/')
def chartjs_test_selection(request):
        #c = {}
        #c.update(csrf(request))
	organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid
    	current_user = request.user.username + " (" + organisation.organisation_name + ")"
    	current_user_role = User_Roles.objects.get(user_userid=request.user.id).role_roleid.role_name;
	current_user = "Hi, " + request.user.first_name + ". You are a " + current_user_role + " in " + organisation.organisation_name + " organisation."

	return render_to_response("report_umlrs_03_selection.html", {'current_user':current_user},
                              context_instance = RequestContext(request))
        #return render(request, "report_umlrs_03_selection.html" ,context_instance=RequestContext(request))
"""

@login_required(login_url='/login/')
def durationreport_selection(request):
	logger.info("User="+request.user.username+" accessed /reports/durationreport_selection/")
	organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid
	current_user = request.user.username + " (" + organisation.organisation_name + ")"
	current_user_role = User_Roles.objects.get(user_userid=request.user.id).role_roleid.role_name;
	current_user = "Hi, " + request.user.first_name + ". You are a " + current_user_role + " in " + organisation.organisation_name + " organisation."
	return render_to_response('duration_report_05_selection.html', {'current_user':current_user}, 
				context_instance = RequestContext(request))

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
                        all_statements_current_date = models.Statement.objects.filter(user=user_with_statement, timestamp__year=current_date.year, timestamp__month=current_date.month, timestamp__day=current_date.day)
                        current_duration=0
                        for every_statement_current_date in all_statements_current_date:
				try:
                                	current_duration=current_duration + int(every_statement_current_date.get_r_duration().seconds)
				except:
					current_duration=current_duration + 0
                        if current_duration == 0 :
                                current_duration=0
                        useryaxis.append(current_duration)
                        user_duration=user_duration+current_duration
                user_by_duration.append(td(seconds=user_duration))
                yaxis.append(useryaxis)
		try:
			a=models.Statement.objects.filter(user=user_with_statement, object_activity__activity_definition_type__icontains="activities/module").latest("timestamp")
			b=a.object_activity.get_a_id() + " - " + a.object_activity.get_a_name() + " : " + str(a.timestamp.strftime('%b %d, %Y'))
		except:
			b="-"
		last_activity.append(b)
        #Reduction by help of a fellow stack overflow use: 
        #http://stackoverflow.com/questions/25656550/remove-occuring-elements-from-multiple-lists-shorten-multiple-lists-by-value/25656674#25656674
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

    	#return render(request, template_name,{'object_list':all_statements, 'table_headers_html':table_headers_html, 'pagetitle':pagetitle, 'tabletypeid':tabletypeid, 'logicpopulation':logicpopulation} )


    return render(request, template_name, data)

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

@login_required(login_url="/login/")
def get_all_blocks_in_this_organisation(request):
    organisation = User_Organisations.objects.get(\
                user_userid=request.user).organisation_organisationid
    try:
	blocks = Block.objects.filter(success="YES", publisher__in=User.objects.filter(pk__in=User_Organisations.objects.filter(organisation_organisationid=organisation).values_list('user_userid', flat=True)))
        return blocks 
    except:
        logger.info("Something went wrong in getting all blocks in this organisation")
        return None

#Calculates statment based on indicators,. users, blocks and date range
"""
To Do: Update duration return to account for blocks and test statement 
To Do: Delete duplicate statements in relevant_statements
"""
def calculate_statements(students, date_since, date_until, blocks):
    delta=(date_until - date_since)
    total_duration=0
    user_by_duration=[]
    all_statements=[]
    all_statements_blocked=[]
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
		
	#To calculate the duration in all of these statements per user
        current_duration=0
        for every_statement in student_statements:
                try:
                        current_duration=current_duration + int(every_statement.get_r_duration().seconds)
                except:
                        current_duration=current_duration + 0
        user_duration=current_duration
        user_by_duration.append(td(seconds=user_duration))
        total_duration=total_duration+user_duration

    return all_statements_blocked, user_by_duration

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

def get_sge_details(obj):
    json_objects = [{'objectName': o.get_objectType_name(),
                           'total_duration':o.total_duration,
			   'children': get_sge_details(o)}\
				for o in obj.child_groups]
    return json_objects

"""
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
    if request.method == 'POST':
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
				logger.info("Something went wrong in getting users in this organiation")
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
		if blocks is None:
			logger.info("Something went wrong")
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
	indicators = []
	#each indicator will be 'on' or False
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
	
	#Other piece of relevant data:
	#blocks=[Algebra, Combustion]	
	#Need to create this.
        #blocks_by_user = [[Algebra, Combustion],[Combustion, Photosynthesis]]
        #[Bob[Algebra,Combustion], Adonbilivit[Combustion, Photosynthesis]]
	blocks_by_user, courses_by_user = get_blocks_courses_by_user(users)
	#print(blocks_by_user)
	#print(courses_by_user)

	relevant_statements=[]
	relevant_statements, user_by_duration=calculate_statements(\
				users, date_since, date_until, blocks)
	
	#user_by_course_by_duration = [[5,5],[6,5]]
	#[Bob[Algebra(5),Combustion(5)], Adonbilivit[Combustion(6), Photosynthesis(5)]]

	#print(date_since)
	#print(date_until)
	#print(reporttype)
	#print(users)
        #print(blocks)
	#print(indicators)
	#print("All statements:")
	#print(relevant_statements)
	#print(len(relevant_statements))
	#print(user_by_duration) 

	#Push this to the statement Grouping
	#		 (Statements, objectVal, level, parent, objectType)
	root = StatementGroupEntry(relevant_statements, None, 0, None, None)
	#default
	grouping = [School()]
	group_em(0, root, grouping, indicators) 

	#We want to send this to the template.
	
	levels_of_grouping=len(grouping)
	data={}
	data['grouping']=grouping
	data['root']=root
	data['levels_of_grouping']=levels_of_grouping
	data['current_user']=current_user
	template_name='usage_report_06.html'
	return render(request, template_name, data)

	
    return render_to_response('usage_report_06.html', {'current_user':current_user},
                                context_instance = RequestContext(request))

"""Common function used by duration report to calculate duration for a list of
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

    
"""Used to render a breakdown report that is old style and doesnt need
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


"""This view is called when usage report submit button is clicked. This renders a JSON 
that is fetched back by the page to render the usage report within the same page.
"""
@login_required(login_url="/login/")
def usage_report_data_ajax_handler(request):
    logger.info("User="+request.user.username+" submitted a request to /reports/usagereport/")

    if request.method == 'POST':
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
        blocks_by_user, courses_by_user = get_blocks_courses_by_user(users)
        relevant_statements=[]
        relevant_statements, user_by_duration=calculate_statements(\
                                users, date_since, date_until, blocks)

	"""
	print('\n')
        print(date_since)
        print(date_until)
        print(reporttype)
        print(users)
        print(blocks)
        print(indicators)
        print("All statements:")
        print(relevant_statements)
        print(len(relevant_statements))
        print(user_by_duration) 
	"""

	print("\n")
        #Push this to the statement Grouping
        #   (Statements, objectVal, level, parent, objectType)
        root = StatementGroupEntry(relevant_statements, None, 0, None, None)
        grouping = [School(), Allclass(), User()]
        group_em(0, root, grouping, indicators)

	json_object=[]
	for child in root.child_groups:
	    a=get_sge_details(child)
	    json_obj = {
			'objectName':child.get_objectType_name(),
			'total_duration':child.total_duration,
			'children':a}
	    json_object.append(json_obj)
	json_object_json=simplejson.dumps(json_object)
	#print(json_object_json)

	#js=root.jdefault()
	
	return HttpResponse(json_object_json, mimetype="application/json")

    
    else:
        logger.info("Not a POST request brah, check your code.")
	return HttpResponse(False)

"""Internal function, not used in any views or functioning of reporting. 
Purpose is to assign existing statements to statementinfo and re assign them during transition of block and courses
assignement with statements
"""

@login_required(login_url="/login/")
def generate_statementinfo_existing_statements(request):
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid;
    all_org_users= User.objects.filter(pk__in=User_Organisations.objects.filter(organisation_organisationid=organisation).values_list('user_userid', flat=True))
    all_statements = models.Statement.objects.all()
    all_org_statements = models.Statement.objects.filter(user__in=all_org_users)
    """
    for org_statement in all_org_statements:
	print(org_statement.id)
	org_statement.save()
    """
    
    authresponse=HttpResponse(status=200)
    authresponse.write("What is Life?")
    return authresponse

"""Internal function, not used in any views or functioning of reporting. 
Purpose is to fix statements and re assign them during transition of block and courses
assignement with statements
"""
### To fix already stored statements
@login_required(login_url="/login/")
def assign_already_stored_statements(request):
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid;
    all_org_users= User.objects.filter(pk__in=User_Organisations.objects.filter(organisation_organisationid=organisation).values_list('user_userid', flat=True))
    all_statements = models.Statement.objects.filter(user__in=all_org_users)
    all_statementinfos = models.StatementInfo.objects.filter(statement__in = all_statements)
    for every_statement in all_statements:
	checkFlag=False
	try:
	    a=models.StatementInfo.objects.filter(statement=every_statement)
	    checkFlag=True
	except:
	    checkFlag=False

	if checkFlag ==False:
	    if every_statement.get_r_duration()=="-":
		statementinfo=models.StatementInfo.objects.create\
			(statement=every_statement)
	    else:
	        statementinfo=models.StatementInfo.objects.create(statement=every_statement,\
			duration=every_statement.get_r_duration())

	else: #If Statement info exists		
	    statementinfo=models.StatementInfo.objects.get(statement=every_statement)

            try:
                activityid=every_statement.object_activity.activity_id
                #removing trailing and leading slash ("/")
                activityid=activityid.strip("/")
                st_elpid=activityid.rsplit('/',1)[1]
                st_tincanid=activityid.rsplit('/',1)[0]
		again_st_tincanid=st_tincanid.rsplit('/',1)[1]
		print(again_st_tincanid)
                #Block only sets block to statement info for blocks within its organisations. A user 
                #Cannot make statements for other organisations
                organisation=User_Organisations.objects.get(user_userid=every_statement.user).organisation_organisationid;
                block=Block.objects.filter(name=again_st_tincanid, \
                            publisher__in=User.objects.filter(\
                                pk__in=User_Organisations.objects.filter(\
                                    organisation_organisationid=organisation\
                                            ).values_list('user_userid', flat=True)))[0]
                statementinfo.block=block;
                statementinfo.save()
            except:
                logger.info("EXCEPTION IN ASSIGNING BLOCK")

	    try:
                logger.info("Starting Course hunt")
                #We have to check if parent is set. If it isn;t, 
                #We thenget the user's last launched activity.
		every_statement_full_statement=str(every_statement.full_statement)
		statement_json=every_statement.full_statement
		#statement_json=json.loads(every_statement_full_statement)
                #statement_json=json.loads(str(every_statement.full_statement))
                try:
                    context_parent = statement_json[u'context'][u'contextActivities'][u'parent']
                except:
                    #print("Could not determing the context, it is not present.")
                    logger.info("Finding course by previous launch entry")
		    try:
                    	last_launched_statement=models.Statement.objects.filter(user=every_statement.user, verb__display__contains='launched').latest("timestamp")
			last_launched_statementinfo = StatementInfo.objects.get(statement=last_launched_statement)
		    except:
			logger.info("No launch query, finding course by assigned blocks")
			course=Course.objects.get(packages=block)
			statementinfo.course=course
			statementinfo.save()

		    else:
                    	course=last_launched_statementinfo.course
                    	statementinfo.course=course
                    	statementinfo.save()
	    except:
                logger.info("EXCEPTION. COULD NOT FIGURE OUT COURSE")

	    try:
            	logger.info("Trying to assign class and school to statement")
            	allclasses_from_statement = statementinfo.course.allclasses.all()
            	for allclass in allclasses_from_statement:
                    if every_statement.user in allclass.students.all():
                    	statementinfo.allclass=allclass
                    	statementinfo.school=allclass.school
                    	statementinfo.save()
                    	break
            except:
            	logger.info("EXCEPTION. Could NOT ASSIGN Class or School to Statement")

    statementids=[]
    for statement in all_statements:
	statementids.append(statement.id)

    return HttpResponse(simplejson.dumps(statementids))

# Create your views here.
