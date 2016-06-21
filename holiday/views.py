from django.shortcuts import render
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib import auth
from django.template import RequestContext
from django.forms import ModelForm
from django import forms
from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
import datetime
import time
import json

from holiday.models import Calendar, Holiday
from organisation.models import Organisation, User_Organisations



"""
Holiday Form
"""
class CalendarForm(ModelForm):
    class Meta:
        model=Calendar
        fields = {'name'}

"""
This view renmders all Holiday Calendars.
It displays it to the template that renders it to a primeui table.
"""
@login_required(login_url='/login/')
def calendar_table(request, template_name='holiday/calendar_table.html', rstate=''):
    organisation = User_Organisations.objects.get(\
                        user_userid=request.user\
                        ).organisation_organisationid;
    calendars = Calendar.objects.filter(organisation=organisation)
    data = {}
    data['object_list'] = calendars
    calendars_as_json = serializers.serialize('json', calendars)
    calendars_as_json =json.loads(calendars_as_json)
    return render(request, template_name, {\
                        'data':data, \
                        'calendars_as_json':calendars_as_json\
                                        })

"""Creates the Calender object. Shared bits of code and checks
"""
def make_calendar_object(name, holiday_string_dates, organisation):
	if holiday_string_dates == None or not holiday_string_dates:
		holidays = None
		state="An empty Holidy Calendar " + name + " has been created."
		statesuccess = 1
	else:
		holidays = holiday_string_dates.split(',')
	holiday_calendar = Calendar(name=name, organisation=organisation)
	holiday_calendar.save()
	if holidays:
		for every_holiday in holidays:
			holiday_date = datetime.datetime.strptime(every_holiday, "%m/%d/%Y")
			holiday = Holiday(date=holiday_date)
			holiday.save()
			holiday_calendar.holidays.add(holiday)
			holiday_calendar.save()
		state="The Holiday Calendar " + name + " has been created"
		statesuccess = 1

	return holiday_calendar, state, statesuccess
			
	

"""View to render template for setting up Holiday calendar
"""
@login_required(login_url='/login/')
def calendar_new(request, template_name="holiday/calendar_new.html"):
    current_user = request.user.username
    organisation = User_Organisations.objects.get(\
                        user_userid=request.user\
                        ).organisation_organisationid;
    #form = HolidayCalendar(request.POST or None)
    data = {}
    data['current_user'] = current_user
    if request.method == "POST":
	print("calendar_new")
	post = request.POST
	holiday_calendar = None
	try:
		name = post['holiday_name']
		hidden_holidays = post['hidden_holidays']
		holiday_calendar, state, statesuccess = make_calendar_object(name, hidden_holidays, organisation);
		calendars = Calendar.objects.filter(organisation=organisation)
    		data['object_list'] = calendars
    		calendars_as_json = serializers.serialize('json', calendars)
    		calendars_as_json =json.loads(calendars_as_json)
		data['calendars_as_json'] = calendars_as_json
		
		return render(request, "holiday/calendar_table.html", data)
			
		#return render(request, template_name, data)
	except Exception as e:
		if holiday_calendar:
			holiday_calendar.delete()
		data['state'] = repr(e)
		
		#data['state'] = "Couldn't create that calendar. Please report this to us."
		return render(request, template_name, data)
        return redirect('home')

    return render(request, template_name, data)


"""
View to render and update holiday calendars
"""
@login_required(login_url='/login/')
def calendar_update(request, pk, template_name='holiday/calendar_form.html'):
    organisation = User_Organisations.objects.get(\
                        user_userid=request.user\
                        ).organisation_organisationid;
    calendar = get_object_or_404(Calendar, pk=pk)
    if organisation != calendar.organisation:
	return redirect('holiday_calendar_table')

    holidays = calendar.holidays.all()
    holidays_date = []
    holidays_date_string = []
    for every_holiday in holidays:
	#TODO: Change to string that works with the JS API
	holidays_date.append(every_holiday.date)
	holidays_date_string.append(str(every_holiday.date.strftime('%m/%d/%Y').encode('utf8')))
    form = CalendarForm(request.POST or None, instance=calendar)
    if form.is_valid():
	print("calendar_updare")
	post=request.POST
        form.save()
	print("Holidays mapping..")
	hidden_holidays = post['hidden_holidays']
	if hidden_holidays is None or not hidden_holidays:
		calendar.holidays.clear()
		return redirect('holiday_calendar_table')
	holidays_list = hidden_holidays.split(',')
	if not holidays_list:
		return redirect('holiday_calendar_table')
	else:
		calendar.holidays.clear()
	for every_holidate in holidays_list:
		holiday_date = datetime.datetime.strptime(every_holidate, "%m/%d/%Y")
		holiday = Holiday(date=holiday_date)
		holiday.save()
		calendar.holidays.add(holiday)
		calendar.save()


        return redirect('holiday_calendar_table')
    return render(request, template_name, {'form':form, 'calendar': calendar, 'holidays':holidays_date, 'holidays_string':holidays_date_string})


# Create your views here.
