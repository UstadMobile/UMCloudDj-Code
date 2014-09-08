from django.db import models
from django.contrib.auth.models import User
from organisation.models import Organisation
import os
import uuid
import time

def get_image_path(instance, filename):
    return os.path.join('avatars', str(instance.id), filename)

class UserProfile(models.Model):
    #user = models.ForeignKey(User, unique=True)
    user = models.OneToOneField(User)
    website = models.URLField("Website", blank=True)
    company_name = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=800, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    gender = models.CharField(max_length=2, blank=True)
    admin_approved = models.BooleanField(default=False)
    organisation_requested = models.ForeignKey(Organisation)
    avatar=models.ImageField(upload_to=get_image_path, default='/media/avatars/no-img.jpg', null=True)
    notes=models.TextField(null=True,blank=True)
# Create your models here.
