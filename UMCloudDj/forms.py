"""
# -*- coding: utf-8 -*-
from django import forms
from datetimewidget.widgets import DateTimeWidget

class DTForm(forms.ModelForm):
    class Meta:
        model = DateTimeModel
        widgets = {
            #Use localization
            'datetime': DateTimeWidget(attrs={'id':"yourdatetimeid"}, usel10n = True)
        }
"""
