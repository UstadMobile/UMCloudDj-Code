# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User #Added user.
from django.core.urlresolvers import reverse #Added reverse..
from organisation.models import Organisation
from allclass.models import Allclass
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

class Package(models.Model):
   elpid = models.CharField(max_length=200)
   exefile = models.FileField(upload_to=get_file_path) #saves as a unique id.
   name = models.CharField(max_length=200)
   #elpname = models.CharField(max_length=200)
   pub_date = models.DateTimeField(auto_now_add=True) #added by Varuna Singh
   upd_date = models.DateTimeField(auto_now=True)
   url = models.CharField(max_length=200)
   uid = models.CharField(max_length=200)
   success = models.CharField(max_length=10)
   publisher = models.ForeignKey(User, related_name='packagepublisher')
   students = models.ManyToManyField(User, related_name='packagestudents')
   active = models.BooleanField(default = True)
   elphash = models.CharField(max_length=80)
   tincanid = models.CharField(max_length=200)

   def __unicode__(self):
        return u'%s' % (self.name)

class Course(models.Model):
   name=models.CharField(max_length=200)   
   description=models.CharField(max_length=800)
   packages = models.ManyToManyField(Package, related_name='coursepackages')
   add_date=models.DateTimeField(auto_now_add=True)
   upd_date=models.DateTimeField(auto_now=True)
   category=models.CharField(max_length=200)
   price=models.FloatField(default = 0)
   active=models.BooleanField(default = True)
   public=models.BooleanField(default = True)
   publisher = models.ForeignKey(User, related_name='coursepublisher')
   organisation = models.ForeignKey(Organisation, related_name='courseorganisation')
   success = models.CharField(max_length=10)
   students = models.ManyToManyField(User, related_name='coursestudents')
   allclasses = models.ManyToManyField(Allclass, related_name='coursesallclasses')
   tincanid = models.CharField(max_length=200, default="http://www.ustadmobile.com/um-tincan/course")

   def __unicode__(self):
        return u'%s' % (self.name)

class Invitation(models.Model):
    invitation_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    organisation = models.ForeignKey(Organisation, related_name='invitationorganisation')
    email = models.CharField(max_length=100)
    invitee = models.ForeignKey(User, related_name='invitee')
    block = models.ForeignKey(Package, related_name='invitationblock')
    course = models.ForeignKey(Course, related_name='invitationbourse')
    done = models.BooleanField(default=False)

    #blocks = models.ManyToManyField(Package, related_name='invitationblocks')
    #courses = models.ManyToManyField(Course, related_name='invitationcourses')


class Ustadmobiletest(models.Model):
   name = models.CharField(max_length=300)
   result = models.CharField(max_length=200)
   runtime = models.CharField(max_length=100)
   dategroup = models.CharField(max_length=100)
   platform = models.CharField(max_length=100)
   ustad_version = models.CharField(max_length=100)
   pub_date = models.DateTimeField(auto_now_add=True)
   upd_date = models.DateTimeField(auto_now=True)

class Role(models.Model):
   #Assuming Django makes ID auto increment for every model by default
   role_name = models.CharField(max_length=300)
   role_desc = models.CharField(max_length=300)
   def __unicode__(self):
	return self.role_name
   def get_absolute_url(self):
	return reverse('role_edit', kwargs={'pk': self.pk})

class User_Roles(models.Model):
   name = models.CharField(max_length=200)
   user_userid = models.ForeignKey(User)
   #user_userid = models.OneToOneField(User)
   role_roleid = models.ForeignKey(Role)
   #role_roleid = models.ManyToManyField(Role)
   add_date = models.DateTimeField(auto_now_add=True)
   def first(self):
	return self[0]
   
# Create your models here.
