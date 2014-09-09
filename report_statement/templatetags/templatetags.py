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
from django.shortcuts import render_to_response
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

from lrs import forms, models, exceptions
from lrs.util import req_validate, req_parse, req_process, XAPIVersionHeaderMiddleware, accept_middleware, StatementValidator
from oauth_provider.consts import ACCEPTED, CONSUMER_STATES
from django.shortcuts import render


register = template.Library()

@register.inclusion_tag("templatetags/report_umlrs_03_selection_students.html", takes_context=True)
def all_students_select(context):
    print("REQUEST IS:")
    print(context['user'])
    user=context['user']
    print user.username
    print("In template tag")
    student_role = Role.objects.get(pk=6)
    organisation = User_Organisations.objects.get(user_userid=user).organisation_organisationid;
    student_list= User.objects.filter(pk__in=User_Organisations.objects.filter(organisation_organisationid=organisation).values_list('user_userid', flat=True)).filter(pk__in=User_Roles.objects.filter(role_roleid=student_role).values_list('user_userid', flat=True))
    allclass_list=Allclass.objects.filter(school__in=School.objects.filter(organisation=organisation));

    return {'allclass_list' : allclass_list}

@register.inclusion_tag("templatetags/report_umlrs_05.html", takes_context=True)
def all_statements_table_notused(context):
    print("In statement request")
    print("REQUEST IS:")
    requestuser=context['user']
    user=context['forthisuser']
    date_since = context['since_1_alt']
    date_until = context['until_1_alt']

    all_statements=models.Statement.objects.filter(user=user)
    print(all_statements)
    data={}
    pagetitle="UstadMobile User Statements"
    tabletypeid="userstatementasrequesteddyna"
    table_headers_html=[]
    table_headers_name=[]

    table_headers_html.append("user")
    table_headers_name.append("User")
    table_headers_html.append("activity_verb")
    table_headers_name.append("Activity Verb")
    table_headers_html.append("activity_type")
    table_headers_name.append("Activity Type")
    table_headers_html.append("duration")
    table_headers_name.append("Duration")
    table_headers_html.append("timestamp")
    table_headers_name.append("Time")

    table_headers_html = zip(table_headers_html, table_headers_name)
    logicpopulation = "{\"user\":\"{{c.user.first_name}} {{c.user.last_name}}\",\"activity_verb\":\"{{c.verb.get_display}}\",\"activity_type\":\"{{c.object_activity.get_a_name}}\",\"timestamp\":\"{{c.timestamp}}\"},\"duration\":\"{{c.result_duration}}\""

    return {'object_list':all_statements, 'table_headers_html':table_headers_html, 'pagetitle':pagetitle, 'tabletypeid':tabletypeid, 'logicpopulation':logicpopulation}



   
