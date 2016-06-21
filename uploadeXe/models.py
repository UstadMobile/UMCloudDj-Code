# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User #Added user.
from django.core.urlresolvers import reverse #Added reverse..
from organisation.models import Organisation
from allclass.models import Allclass
import os
import uuid
import time
import datetime

"""
This is a model for days in the week
"""
class Weekday(models.Model):
   name = models.CharField(max_length=300)
   def __unicode__(self):
	return u'%s' % (self.name)

"""
This is a model for days of the week.
"""
class Week_Day_Time(models.Model):
   #day_name = models.CharField(max_length=300)
   day = models.ForeignKey(Weekday, related_name='week_day')
   from_time = models.TimeField(default = datetime.time(00,00))
   to_time = models.TimeField(default=datetime.time(23,59))

   def __unicode__(self):
        return u'%s ' % (self.day + "(" + str(from_time) + "-" + str(to_time) + ")")

"""
This is a date model
"""
class DateTime(models.Model):
    date = models.DateTimeField()




"""used for getting and setting path to elp "blocks" from external
(eXe) and direc upload from umcloud portal
"""
def get_file_path(instance, filename):
   print("Yo, here in get_file_path." + str(filename))
   ext = filename.split('.')[-1]
   ext = "um."
   filename = "%s.%s" % (uuid.uuid4(), ext) + filename
   return os.path.join('eXeUpload/', filename)

"""
Common function to update filenames to add timestamp instance. 
Don't think this is used anywhere. Can be deleted.
"""
def update_filename(instance, filename):
   path = "eXeUpload/"
   timestamp = str(time.time())
   filename = instance.user + timestamp + ".um." + filename
   return os.path.join(path, filename)


"""
Course / Block Categories are declared over here. 
"""
class Categories(models.Model):
    name = models.CharField(max_length=200, unique=True)
    parent_id = models.IntegerField(default=0)
    def __unicode__(self):
	return u'%s' % (self.name)

"""This represents a BLOCK. a block is an elp file technically
and many blocks make the course.
Blocks are related to its publisher 
Students are related to a block
each block as a unique id, uid and elp id.
tin can id is set as well
"""
class Package(models.Model):
   elpid = models.CharField(max_length=200)
   exefile = models.FileField(upload_to=get_file_path, max_length=600) #saves as a unique id.
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
   tincanid = models.CharField(max_length=200,\
		default="http://www.ustadmobile.com/um-tincan/activities")
   description = models.CharField(max_length=1800, null=True)
   lang = models.CharField(max_length = 100, null=True)
   subject = models.CharField(max_length = 200, null=True)
   micro_edition=models.BooleanField(default = False)
   def __unicode__(self):
        return u'%s' % (self.name)


class AcquisitionLink(models.Model):
   exefile = models.FileField(upload_to=get_file_path, max_length=900) #saves as a unique id.
   mimetype = models.CharField(max_length=200, null=True)
   length = models.PositiveIntegerField(default=0)
   title = models.CharField(max_length=300)
   rel = models.CharField(max_length=400, default="http://opds-spec.org/acquisition")
   md5 = models.CharField(max_length=100)
   preview_path = models.CharField(max_length=900, null=True) #Used to be url
   entry = models.ForeignKey(Package, related_name="acquisitionlink")
   active = models.BooleanField(default = True)

"""
A course represents a combination of packages. Students 
and classes are assigned to a course
Students and Users download courses which are a bundle of 
blocks or even a single block.
A course has a tincan id and price .
An active course should be active and success as "YES"
Category is just string field for now
Course must be assigned to an organisation, but default 
treated as public (get course apis can access by course id)
"""
class Course(models.Model):
   name=models.CharField(max_length=200)   
   description=models.CharField(max_length=800)
   packages = models.ManyToManyField(Package, related_name='coursepackages') #blocks
   add_date=models.DateTimeField(auto_now_add=True)
   upd_date=models.DateTimeField(auto_now=True)
   category=models.CharField(max_length=200)
   cat = models.ManyToManyField(Categories, related_name='coursecategory')
   price=models.FloatField(default = 0)
   active=models.BooleanField(default = True)
   public=models.BooleanField(default = True)
   publisher = models.ForeignKey(User, related_name='coursepublisher')
   organisation = models.ForeignKey(Organisation, related_name='courseorganisation')
   success = models.CharField(max_length=10)
   students = models.ManyToManyField(User, related_name='coursestudents')
   allclasses = models.ManyToManyField(Allclass, related_name='coursesallclasses')
   tincanid = models.CharField(max_length=200, \
			default="http://www.ustadmobile.com/um-tincan/course")
   grade_level = models.CharField(max_length=100, null=True)
   lang = models.CharField(max_length = 100, null=True)
   

   def __unicode__(self):
        return u'%s' % (self.name)
"""
Links Country with Organisation and courses to be assigned. 
"""

class Country_Organisation(models.Model):
    country_code = models.CharField(max_length=300)
    organisation = models.ForeignKey(Organisation)
    allcourses = models.ManyToManyField(Course, related_name='countryorgnaisationcourses')
    def __unicode__(self):
	return u'%s' %(self.country_code)


"""
An Invitation object stores invitation unique uuid against invitations
made from eXe to an email address. The views handle populating the model
done is True when the email address is associated with a user and assigned
the course and block .
The views handle email check against existing users as well.
"""
class Invitation(models.Model):
    invitation_id = models.CharField(max_length=100, \
			unique=True, default=uuid.uuid4)
    organisation = models.ForeignKey(Organisation, \
			related_name='invitationorganisation')
    email = models.CharField(max_length=100)
    invitee = models.ForeignKey(User, related_name='invitee')
    block = models.ForeignKey(Package, \
				related_name='invitationblock')
    course = models.ForeignKey(Course, \
				related_name='invitationbourse')
    done = models.BooleanField(default=False)

    #blocks = models.ManyToManyField(Package, related_name='invitationblocks')
    #courses = models.ManyToManyField(Course, related_name='invitationcourses')

"""
Currently Depricated model of tests database for success and 
failure for different app platforms. Might use it later. 
"""
class Ustadmobiletest(models.Model):
   name = models.CharField(max_length=300)
   result = models.CharField(max_length=200)
   runtime = models.CharField(max_length=100)
   dategroup = models.CharField(max_length=100)
   platform = models.CharField(max_length=100)
   ustad_version = models.CharField(max_length=100)
   pub_date = models.DateTimeField(auto_now_add=True)
   upd_date = models.DateTimeField(auto_now=True)

"""
Every user has a role respective to its organisation
All roles will be stored in the role model. 
Initial data is provided in the initial data json.
"""
class Role(models.Model):
   #Assuming Django makes ID auto increment for every model by default
   role_name = models.CharField(max_length=300)
   role_desc = models.CharField(max_length=300)
   def __unicode__(self):
	return self.role_name
   def get_absolute_url(self):
	return reverse('role_edit', kwargs={'pk': self.pk})

"""
This is model for user mapped against roles. Every user should have a role.
Currently there is a One to Many relationship between User and Roles.
"""
class User_Roles(models.Model):
   name = models.CharField(max_length=200)
   user_userid = models.ForeignKey(User)
   role_roleid = models.ForeignKey(Role)
   add_date = models.DateTimeField(auto_now_add=True)
   def first(self):
	return self[0]
   
# Create your models here.
