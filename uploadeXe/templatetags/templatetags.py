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
from uploadeXe.models import Categories
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
    user=context['user']
    student_role = Role.objects.get(pk=6)
    organisation = User_Organisations.objects.get(user_userid=user).organisation_organisationid;
    student_list= User.objects.filter(pk__in=User_Organisations.objects.filter(organisation_organisationid=organisation).values_list('user_userid', flat=True)).filter(pk__in=User_Roles.objects.filter(role_roleid=student_role).values_list('user_userid', flat=True))
    allclass_list=Allclass.objects.filter(school__in=School.objects.filter(organisation=organisation));

    return {'allclass_list' : allclass_list}

@register.inclusion_tag("templatetags/course_create.html", takes_context=True)
def all_root_categories(context):
    all_categories = Categories.objects.filter(parent_id = 0)
    return {'all_root_categories' : all_categories }

