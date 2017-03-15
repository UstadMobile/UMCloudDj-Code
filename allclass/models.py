from django.db import models
from school.models import School
from django.contrib.auth.models import User
from holiday.models import Calendar
from organisation.models import Organisation

"""
Gets the max number of enrollments in that class and returns the next
available roll number
"""
def get_next_roll_number(allclass):
    print("Roll number calculation")
    no = len(User.objects.filter(enrollment__allclass = allclass))
    try:
        max_roll_number = Enrollment.objects.filter(allclass = allclass).order_by("-roll_number")[0].roll_number
        print("Max: " + str(max_roll_number) + " no: " + str(no))
        if max_roll_number != no and max_roll_number != 0:
            print("Max roll number not equal to the number of students. I wonder why.")
            if max_roll_number > no:
                print("Taking the next roll number")
                no = max_roll_number
    	if max_roll_number == 0:
	    no = None
    except:
        pass
    if not no:
            return 1
    else:
            no = no + 1
            return no


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
    #students = models.ManyToManyField(User, related_name='allclassstudents')
    students = models.ManyToManyField(User, related_name='allclassstudents', through='Enrollment')
    teachers = models.ManyToManyField(User, related_name='teachers')
    school = models.ForeignKey(School, null=True)
    #days = models.ManyToManyField('uploadeXe.Weekday', null = True)
    #days = models.ManyToManyField('uploadeXe.DateTime', null = True)
    days = models.ManyToManyField('uploadeXe.Week_Day_Time', null = True)
    holidays = models.ManyToManyField(Calendar, null = True)
    def __unicode__(self):
        return u'%s ' % (self.allclass_name)

    def students_all(self):
        allstudents = User.objects.filter(enrollment__active = True,\
        enrollment__allclass = self).order_by('enrollment__roll_number')
        return allstudents

    def students_all_ever(self):
	allstudents_ever = User.objects.filter(enrollment__allclass = \
	    self).order_by('enrollment__roll_number')
	return allstudents_ever

    def students_add(self, student):
        try:
            #Will throw exception if student isnt already enrolled
            enroll = Enrollment.objects.get(user = student,\
                allclass = self)
            if enroll.active == False:
                enroll.active = True
                enroll.save()
        except Exception, e:
	    print("Exception in class's students add : " + str(e))
            enroll = Enrollment(user = student, allclass = self, active = True)
	    enroll.roll_number = get_next_roll_number(self)
	    enroll.save()
            self.save()

    def students_remove(self, student):
        try:
            enroll = Enrollment.objects.get(user = student,\
                allclass = self, active = True)
            enroll.active = False
            enroll.save()
        except Exception, e:
            pass


"""
The Enrollment Class: This is an extended mapping of Classes and
Users (Students). Teachers enroll students in their classes. The
reason for this m2m through table is so that we can assign roll 
numbers and find out when they were added and updated. Students 
can be unasigned to the class by their active status and can re 
join by this status. This would not disrupt the roll numbers if
a teacher wants to use those and returning students still have 
theirs. By default the roll numbers are assigned and updated in 
order of the enrollment date. There could be another method that 
changes the order of the roll numbers in the future. 
"""
class Enrollment(models.Model):
        allclass = models.ForeignKey(Allclass)
        user = models.ForeignKey(User)
        date_joined = models.DateTimeField(auto_now_add=True)
        date_modified = models.DateTimeField(auto_now = True)
        date_updated = models.DateTimeField(null=True)
        active = models.BooleanField(default = True)
        notes = models.CharField(max_length=1024, null=True)
        roll_number = models.IntegerField(default=0)
        def save(self, *args, **kwargs):
                super(Enrollment, self).save(*args, **kwargs)
		#We don't want the roll number to be updated every 
		# time we save an enrollment. This was only useful 
		#  when we were migrating. Remove this after all OK
		#self.roll_number = number(self.allclass)
		#super(Enrollment, self).save(*args, **kwargs)
                if self.date_modified:
                        print("Updating date updated")
                        self.date_updated = self.date_modified
                        super(Enrollment,self).save(*args, **kwargs)

"""
Alert Models
"""

class Allclass_alert_settings(models.Model):
  allclass = models.ForeignKey(Allclass)
  cut_off_time = models.IntegerField(default = 1) #in hours

class Alert_type(models.Model):
   name = models.CharField(max_length=300)

class Alert(models.Model):
   organisation = models.ForeignKey(Organisation)
   schools = models.ManyToManyField(School, null = True, related_name = "alert_schools")
   allclasses = models.ManyToManyField(Allclass, null = True, related_name = "alert_classes")
   #Frequency
   day_of_week = models.IntegerField(null=True)
   month = models.IntegerField(null=True)
   day_of_month = models.IntegerField(null=True)
   minute = models.IntegerField(null=True)
   active = models.BooleanField(default=False)
   #Alert Type
   types = models.ManyToManyField(Alert_type, null = False)
   to_emails = models.CharField(max_length = 1000)



# Create your models here.
