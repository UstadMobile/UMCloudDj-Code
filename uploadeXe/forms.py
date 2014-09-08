# -*- coding: utf-8 -*-
from django import forms

class ExeUploadForm(forms.Form):
    exefile = forms.FileField(
        label='Select .elp file'
	#content_types = 'application/elp'
    )

