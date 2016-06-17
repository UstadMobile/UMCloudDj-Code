"""
from django.db import models
from django.contrib.auth.models import User


class Weekday(models.Model):
   name = models.CharField(max_length=300)

   def __unicode__(self):
        return u'%s ' % (self.name)
"""

"""
# -*- coding: utf-8 -*-
from django.db import models

import os
import uuid
import time

def get_file_path(instance, filename):
   ext = filename.split('.')[-1]
   ext = "um."
   filename = "%s.%s" % (uuid.uuid4(), ext) + filename
   return os.path.join('eXeUpload/', filename)

def update_filename(instance, filename):
   path = "eXeUpload/"
   timestamp = str(time.time())
   filename = instance.user + timestamp + ".um." + filename
   return os.path.join(path, filename)

class DateTimeModel(models.Model):
   start = models.DateTimeField()

class testTable(models.Model):
   name = models.CharField(max_length=300)

# Create your models here.
"""
