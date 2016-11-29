from django.db import models
from django.contrib.auth.models import User
from organisation.models import Organisation
import os
import uuid
import time


"""
method used by avatar upload file
"""
def get_image_path(instance, filename):
    return os.path.join('avatars', str(instance.id), filename)

"""
UserProfile model extends user (One To One Relationship)
Instead of modifying django's auth, we extend user model.
Organisation requested field goes here that gets compared.
Avatar capability also part of this model.
"""
class UserProfile(models.Model):
    user = models.OneToOneField(User)
    website = models.URLField("Website", blank=True)
    company_name = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=800, blank=True)
    phone_number = models.CharField(max_length=50, blank=True)
    gender = models.CharField(max_length=2, blank=True)
    admin_approved = models.BooleanField(default=False)
    organisation_requested = models.ForeignKey(Organisation)
    avatar=models.ImageField(upload_to=get_image_path, \
		    default='/media/avatars/no-img.jpg',\
		        	null=True)
    notes=models.TextField(null=True,blank=True)
    last_activity_date = models.DateTimeField(blank=True, null=True)
    custom_roll_no = models.CharField(max_length = 100, blank = True, null = True)

class PasswordReset(models.Model):
    user = models.ForeignKey(User)
    reg_id = models.CharField(max_length=100, \
                        unique=True, default=uuid.uuid4)
    done = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True) #added by Varuna Singh
    date_accessed = models.DateTimeField(auto_now=True, null=True)
# Create your models here.
