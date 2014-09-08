from django.db import models
from school.models import School
from django.contrib.auth.models import User

class Allclass(models.Model):
    allclass_name = models.CharField(max_length=300)
    allclass_desc = models.CharField(max_length=1000)
    allclass_location = models.CharField(max_length=200)
    students = models.ManyToManyField(User, related_name='allclassstudents')
    teachers = models.ManyToManyField(User, related_name='teachers')
    school = models.ForeignKey(School, null=True)
    
    def __unicode__(self):
        return u'%s ' % (self.allclass_name)
# Create your models here.
