from django.db import models
import datetime
from django.contrib.auth.models import User

"""
This model sets the subscription package for a particular organisation. 
"""
class UMCloud_Package(models.Model):
   package_name = models.CharField(max_length=300)
   package_desc = models.CharField(max_length=2000)
   max_students = models.IntegerField()
   max_publishers = models.IntegerField()
   price_rate_permonth = models.FloatField()
   def __unicode__(self):
        return u'%s ' % (self.package_name)

"""
Every Organisation is treated as its own with having a subscription package
Org are directly realted to schools which relate to classes
"""
class Organisation(models.Model):
   organisation_name = models.CharField(max_length=300)
   organisation_desc = models.CharField(max_length=1000)
   add_date = models.DateTimeField(default=datetime.datetime.now)
   set_package = models.ForeignKey(UMCloud_Package)
   public = models.BooleanField(default = False)

   def __unicode__(self):
        return u'%s ' % (self.organisation_name)

"""
Every user is realted to a single organisation
"""
class User_Organisations(models.Model):
   #add_date = models.DateTimeField(auto_now_add=True)
   add_date = models.DateTimeField(default=datetime.datetime.now)
   user_userid = models.ForeignKey(User)
   organisation_organisationid = models.ForeignKey(Organisation)

"""
Every organisation has a sign up code that can be linked and shared
this enables the organisation manager to approve or reject user
requests. 
"""
class Organisation_Code(models.Model):
   organisation = models.ForeignKey(Organisation)
   code=models.CharField(max_length=100)


# Create your models here.
