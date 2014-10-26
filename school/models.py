from django.db import models
from django.contrib.auth.models import User
from organisation.models import Organisation

"""
This is the model for schools. Schools are directly
related to organisations and have a name and desc.
"""
class School(models.Model):
   school_name = models.CharField(max_length=300)
   school_desc = models.CharField(max_length=1000)
   organisation = models.ForeignKey(Organisation)

   def __unicode__(self):
	return u'%s ' % (self.school_name)

# Create your models here.
