from django.db import models
from organisation.models import Organisation

# Create your models here.

"""
This
"""
class status_label(models.Model):
	name = models.CharField(max_length = 300)

class organisation_status_label(models.Model):
	organisation = models.ForeignKey(Organisation)
	status_label = models.ForeignKey(status_label)
