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

from django import template
from django.core import serializers
import simplejson
from itertools import takewhile

from lrs import forms, models, exceptions
from lrs.util import req_validate, req_parse, req_process, XAPIVersionHeaderMiddleware, accept_middleware, StatementValidator
from oauth_provider.consts import ACCEPTED, CONSUMER_STATES
from django.shortcuts import render

# This uses the lrs logger for LRS specific information
logger = logging.getLogger(__name__)


@login_required(login_url="/login/")    #added by Varuna
def show_statements_from_db(request,template_name='report_umlrs_01.html'):
    all_statements=models.Statement.objects.all()
    #print(all_statements)
    data={}
    return render(request, template_name,{'all_statements':all_statements} )

@login_required(login_url="/login/")    #Added by varuna
def statements_db_dynatable(request,template_name='report_umlrs_02.html'):
    organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid;
    all_org_users= User.objects.filter(pk__in=User_Organisations.objects.filter(organisation_organisationid=organisation).values_list('user_userid', flat=True))
    all_statements = models.Statement.objects.filter(user__in=all_org_users)
    pks = [613, 614, 631, 642, 653, 469, 664, 673, 615, 632, 643, 654, 665, 470, 674, 682, 616, 633, 644, 655, 666, 471, 675, 683, 617, 634, 645, 656, 667, 472, 676, 684, 618, 635, 646, 657, 462, 473, 668, 677, 619, 620, 621, 622, 463, 636, 647, 658, 623, 624, 625, 626, 464, 637, 648, 659, 627, 638, 649, 660, 465, 669, 678, 685, 628, 639, 650, 661, 466, 670, 679, 686, 629, 640, 651, 662, 467, 671, 680, 687, 630, 641, 652, 663, 672, 468, 681, 688, 689, 690, 691, 692, 693, 694, 695, 696, 697, 698, 699, 700, 701, 702, 703, 704, 705, 706, 707, 708, 709, 710, 711, 712, 713, 714, 715, 716, 717, 718, 719, 720, 721, 722, 723, 724, 725, 726, 727, 728, 729, 730, 731, 732, 733, 734, 735, 736, 737, 738, 739, 740, 741, 742, 743, 744, 745]
    for pk in pks:
	try:
		statement=models.Statement.objects.get(pk=pk)
	except:
		print("Problem with id: " + str(pk))
		pass
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
    table_headers_html.append("duration")
    table_headers_name.append("Duration")
    table_headers_html.append("timestamp")
    table_headers_name.append("Time")

    table_headers_html = zip(table_headers_html, table_headers_name)
    logicpopulation = "{\"user\":\"{{c.user.first_name}} {{c.user.last_name}}\",\"activity_verb\":\"{{c.verb.get_display}}\",\"activity_type\":\"{{c.object_activity.get_a_name}}\",\"timestamp\":\"{{c.timestamp}}\"},\"duration\":\"{{c.result_duration}}\""

    return render(request, template_name,{'object_list':all_statements, 'table_headers_html':table_headers_html, 'pagetitle':pagetitle, 'tabletypeid':tabletypeid, 'logicpopulation':logicpopulation} )


@login_required(login_url="/login/")    #Added by varuna
def my_statements_db_dynatable(request,template_name='report_umlrs_04.html'):
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
def all_statements_table(request, userid, template_name='report_umlrs_04.html'):
    template_name="report_umlrs_04.html"
    #, date_since, date_until):
    requestuser=request.user
    user=User.objects.get(id=userid)

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
    #print("user: " + request.user.username + " requested all students of class: " + Allclass.objects.get(id=allclassid).allclass_name)
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
        return HttpResponse(json_students, mimetype="application/javascript")
    else:
        print("Class requested not part of request user's organisation. Something is fishy")
        return HttpResponse(None)

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

@login_required(login_url='/login/')
def usagereport_selection(request):
	organisation = User_Organisations.objects.get(user_userid=request.user).organisation_organisationid
	current_user = request.user.username + " (" + organisation.organisation_name + ")"
	current_user_role = User_Roles.objects.get(user_userid=request.user.id).role_roleid.role_name;
	current_user = "Hi, " + request.user.first_name + ". You are a " + current_user_role + " in " + organisation.organisation_name + " organisation."
	return render_to_response('report_umlrs_05_selection.html', {'current_user':current_user}, 
				context_instance = RequestContext(request))

@login_required(login_url='/login/') 
def usage_report(request, template_name='report_umlrs_05.html'):
    if request.method != 'POST':
	return redirect('usage_report_selection')

    date_since = request.POST['since_1_alt']
    date_until = request.POST['until_1_alt']
    user_selected = request.POST.getlist('model')

    if True:
        date_since = datetime.strptime(date_since[:10], '%Y-%m-%d')
        date_until = datetime.strptime(date_until[:10], '%Y-%m-%d')
        #print("new datetime dates converted from unicode to datetime")
        print(str(date_since) + "-->" + str(date_until))
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
        print("--------------------------------------")

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
		print("For user: " + str(user_id_with_statement) + " duration: " + str(user_duration))
                user_by_duration.append(td(seconds=user_duration))
                yaxis.append(useryaxis)
		try:
			a=models.Statement.objects.filter(user=user_with_statement, object_activity__activity_definition_type__icontains="activities/module").latest("timestamp")
			b=a.object_activity.get_a_id() + " - " + a.object_activity.get_a_name() + " : " + str(a.timestamp.strftime('%b %d, %Y'))
		except:
			b="-"
		print(b)
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
    	data['tabletypeid']="usagereportdynatable"
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


@login_required(login_url="/login/")    #added by Varuna
def chartjs_test(request,template_name='report_umlrs_03.html'):
    date_since = request.POST['since_1_alt']
    date_until = request.POST['until_1_alt']
    user_selected = request.POST.getlist('model')

    if True:
	date_since = datetime.strptime(date_since[:10], '%Y-%m-%d')
	date_until = datetime.strptime(date_until[:10], '%Y-%m-%d')
	#print("new datetime dates converted from unicode to datetime")
	print(str(date_since) + "-->" + str(date_until))
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
	print("--------------------------------------")
	
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
                                current_duration=current_duration + int(every_statement_current_date.get_r_duration().seconds)
                        if current_duration == 0 :
                                current_duration=0
                        useryaxis.append(current_duration)
                        user_duration=user_duration+current_duration
                user_by_duration.append(td(seconds=user_duration))
                yaxis.append(useryaxis)

	#Reduction by help of a fellow stack overflow use: 
	#http://stackoverflow.com/questions/25656550/remove-occuring-elements-from-multiple-lists-shorten-multiple-lists-by-value/25656674#25656674
	num_zeroes = len(list(takewhile(lambda p: p == 0, max(yaxis))))-1
	yaxis=[li[num_zeroes:] for li in yaxis]
	xaxis=xaxis[num_zeroes:]
	yaxis=zip(label_legend, yaxis, user_by_duration)
	data={}
	data['xaxis']=xaxis;
	data['yaxis']=yaxis
	data['date_since']=date_since
	data['date_until']=date_until

    return render(request, template_name, data)

# Create your views here.
