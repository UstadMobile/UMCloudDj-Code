from django.db import models
from school.models import School
from django.contrib.auth.models import User

"""
Class object called Allclass because we cant
call it class to avoid confusion
This model is for classes that reside under a school 
which is part of an organisation. 
Class is realted to School (assigned to organisation)
and teachers and students are assigned to the class. 
"""
class Allclass(models.Model):
    allclass_name = models.CharField(max_length=300)
    allclass_desc = models.CharField(max_length=1000)
    allclass_location = models.CharField(max_length=200)
    students = models.ManyToManyField(User, related_name='allclassstudents')
    teachers = models.ManyToManyField(User, related_name='teachers')
    school = models.ForeignKey(School, null=True)
    #days = models.ManyToManyField('uploadeXe.Weekday', null = True)
    #days = models.ManyToManyField('uploadeXe.DateTime', null = True)
    days = models.ManyToManyField('uploadeXe.Week_Day_Time', null = True)
    def __unicode__(self):
        return u'%s ' % (self.allclass_name)
# Create your models here.
