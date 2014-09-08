from django.db import models
from django.contrib.auth.models import User
from organisation.models import Organisation

class School(models.Model):
   school_name = models.CharField(max_length=300)
   school_desc = models.CharField(max_length=1000)
   organisation = models.ForeignKey(Organisation)

   def __unicode__(self):
	return u'%s ' % (self.school_name)

# Create your models here.
