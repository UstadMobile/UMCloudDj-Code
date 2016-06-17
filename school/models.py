from django.db import models
from django.contrib.auth.models import User
from organisation.models import Organisation
from decimal import Decimal
#from uploadeXe.models import Weekday

"""
This is the model for schools. Schools are directly
related to organisations and have a name and desc.
"""
class School(models.Model):
   school_name = models.CharField(max_length=300)
   school_desc = models.CharField(max_length=1000)
   organisation = models.ForeignKey(Organisation)
   longitude = models.DecimalField(max_digits= 9, decimal_places = 6, null = True)
   lattitude = models.DecimalField(max_digits= 9, decimal_places = 6, null = True)
   show_location = models.BooleanField(default = False)
   show_exact_location = models.BooleanField(default = False)
   weekends = models.ManyToManyField('uploadeXe.Weekday', null = True)
   #holidays = models.ManyToManyField('uploadeXe.DateTime', null = True)

   def __unicode__(self):
	return u'%s ' % (self.school_name)

# Create your models here.
