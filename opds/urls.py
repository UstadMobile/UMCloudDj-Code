# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

urlpatterns = patterns('opds.views',
    url(r'^$', 'root_view', name='opds_root'),
    url(r'^assigned_courses/$', 'assigned_courses', name='assigned_courses'),
    #url(r'^get_course/$', 'get_course', name='get_course'),
    url(r'^course/$', 'get_course', name='course'),
    url(r'^public/$', 'public_view', name='public_view'),
    url(r'^public/providers/$', 'public_providers', name = 'public_providers'),
    url(r'^public/providers/(?P<pk>\d+)$', 'public_providers_nocategories', name = 'public_providers_nocategories'),
    url(r'^public/providers/(?P<pk>\d+)/(?P<ct>\d+)/$', 'public_providers_categories', name = 'public_providers_categories'),
    url(r'^public/categories/$', 'public_categories_view', name='public_categories_view'),
    url(r'^public/categories/(?P<pk>\d+)$', 'public_category_view', name='public_category_view'),
    url(r'^public/course/$', 'get_public_course', name='get_public_course'),
    url(r'^public/opensearch/$', 'public_opensearch_description', name='opensearch_description'),
    url(r'^public/alphabetical/$', 'public_alphabetical_view', name='public_alphabetical_view'),
    #url(r'^delete/(?P<pk>\d+)$', 'delete', name='delete'),
    #url(r'^elpparse/$', 'elpparse', name='elpparse'),
    #url(r'^managecourses/$','course_table', name='managecourses'),

)
