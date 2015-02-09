# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

urlpatterns = patterns('opds.views',
    url(r'^$', 'root_view', name='opds_root'),
    url(r'^assigned_courses/$', 'assigned_courses', name='assigned_courses'),
    #url(r'^get_course/$', 'get_course', name='get_course'),
    url(r'^course/$', 'get_course', name='course')
    #url(r'^delete/(?P<pk>\d+)$', 'delete', name='delete'),
    #url(r'^elpparse/$', 'elpparse', name='elpparse'),
    #url(r'^managecourses/$','course_table', name='managecourses'),

)
