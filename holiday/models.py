from django.db import models
from django.contrib.auth.models import User #Added user.
from organisation.models import Organisation
from django.core.urlresolvers import reverse #Added reverse..
import os
import uuid
import time
import datetime
import holidays

"""
This is a holiday
"""
class Holiday(models.Model):
    name = models.CharField(max_length=300, default="Holiday")
    date = models.DateField(auto_now = False, null = False)

"""
This is the holiday calender
"""
class Calendar(models.Model):
    name = models.CharField(max_length=300, default="Holiday Calendar")
    holidays = models.ManyToManyField(Holiday, related_name="holiday_calendar_holiday")
    organisation = models.ForeignKey(Organisation)

    """
    #Example use cases:
    school.holiday_calendar.holidays.all()
    school.holiday_calender.holidays.add(name="Fathers Day", date=datetime.date(2016,06,19))
    """
# Create your models here.
