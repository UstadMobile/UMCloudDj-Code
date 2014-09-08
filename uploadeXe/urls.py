# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

urlpatterns = patterns('uploadeXe.views',
    url(r'^list/$', 'list', name='list'),
    url(r'^manage/$', 'manage', name='manage'),
    url(r'^new/$', 'new', name='new'),
    url(r'^edit/(?P<pk>\d+)$', 'edit', name='edit'),
    url(r'^delete/(?P<pk>\d+)$', 'delete', name='delete'),
    #url(r'^elpparse/$', 'elpparse', name='elpparse'),
    url(r'^managecourses/$','course_table', name='managecourses'),
    url(r'^coursenew/$','course_create', name='coursenew'),
    url(r'^courseedit/(?P<pk>\d+)$','course_update', name='courseedit'),
    url(r'^coursedelete/(?P<pk>\d+)$','course_delete',name='coursedelete'),

)
