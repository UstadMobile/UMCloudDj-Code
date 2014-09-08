from django.db import models
import datetime
from django.contrib.auth.models import User

class UMCloud_Package(models.Model):
   package_name = models.CharField(max_length=300)
   package_desc = models.CharField(max_length=2000)
   max_students = models.IntegerField()
   max_publishers = models.IntegerField()
   price_rate_permonth = models.FloatField()
   def __unicode__(self):
        return u'%s ' % (self.package_name)

class Organisation(models.Model):
   organisation_name = models.CharField(max_length=300)
   organisation_desc = models.CharField(max_length=1000)
   add_date = models.DateTimeField(default=datetime.datetime.now)
   set_package = models.ForeignKey(UMCloud_Package)

   def __unicode__(self):
        return u'%s ' % (self.organisation_name)

class User_Organisations(models.Model):
   #add_date = models.DateTimeField(auto_now_add=True)
   add_date = models.DateTimeField(default=datetime.datetime.now)
   user_userid = models.ForeignKey(User)
   organisation_organisationid = models.ForeignKey(Organisation)

class Organisation_Code(models.Model):
   organisation = models.ForeignKey(Organisation)
   code=models.CharField(max_length=100)


# Create your models here.
