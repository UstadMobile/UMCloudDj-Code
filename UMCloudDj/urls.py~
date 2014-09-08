#from django.conf.urls import patterns, include, url

#from django.contrib import admin
#admin.autodiscover()

#urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'UMCloudDj.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

#    url(r'^admin/', include(admin.site.urls)),
#)

# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib import admin

#UMCloudDj.uploadeXe

urlpatterns = patterns('',
	url(r'^getreportzambia/', 'UMCloudDj.views.get_report_zambia'),
	url(r'^reports/$', 'UMCloudDj.views.report_selection_view', name='reports'),
	url(r'^jsontest/$', 'UMCloudDj.views.readjsonfromlrs_view', name='jsontest'),
	url(r'^sendtestlog/$', 'UMCloudDj.views.sendtestlog_view', name='sendtestlog'),
	url(r'^getcourse/$', 'UMCloudDj.views.getcourse_view', name='getcourse'),
	url(r'^admin/', include(admin.site.urls)),
	url(r'^login/', 'UMCloudDj.views.loginview', name='login'),
	url(r'^auth/', 'UMCloudDj.views.auth_and_login'),
        url(r'^signup/', 'UMCloudDj.views.sign_up_in'),
        url(r'^$', 'UMCloudDj.views.secured'),
	url(r'^logout/$', 'UMCloudDj.views.logout_view'),
	url(r'^register/$', 'UMCloudDj.views.register_view', name='register'),
	#url(r'^progressbarupload/', include('progressbarupload.urls')),

 	#For upload feature. Need both for file upload. The second one re directs to the url and first one does somehting related to that. 
	(r'^uploadeXe/', include('uploadeXe.urls')),
	(r'^uploadeXe/$', RedirectView.as_view(url='/uploadeXe/list/')), # Just for ease of use.
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
