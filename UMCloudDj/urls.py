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

#For django-resumable 
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView
from resumable.views import ResumableUploadView
from UMCloudDj.views import ResumableBlockUploadView

#UMCloudDj.uploadeXe

urlpatterns = patterns('',
        (r'^umlrs/', include('lrs.urls')),
  	(r'^opds/', include('opds.urls')),
	url('^blockupload/$', csrf_exempt(ResumableBlockUploadView.as_view()), #Resumablejs block upload
	    name='block_upload'),
	url('^resumableupload/$', csrf_exempt(ResumableUploadView.as_view()),  #Resumable file upload.
            name='resumable_upload'),
	url(r'^$', RedirectView.as_view(url='/userstable/')), # Just for ease of use.
	url(r'^upload/', 'UMCloudDj.views.upload_view', name='oldcoursesview'),
	url(r'^management/', 'UMCloudDj.views.management_view', name='management'),
	url(r'^reports/$', 'UMCloudDj.views.reports_view', name='reports'),

	#url(r'^getreportzambia/', 'UMCloudDj.views.get_report_zambia'),
	#url(r'getreportstatements/', 'UMCloudDj.views.get_report_statements'),
        #url(r'statementsreports/$', 'UMCloudDj.views.report_statements_view'),
	#url(r'^mcqreports/$', 'UMCloudDj.views.report_selection_view', name='mcqreports'),
	#url(r'^sendtestlog/$', 'UMCloudDj.views.sendtestlog_view', name='sendtestlog'),
	url(r'^sendelpfile/$', 'UMCloudDj.views.sendelpfile_view', name='sendelpfile'),
	url(r'^checklogin/$', 'UMCloudDj.views.checklogin_view', name='checklogin'),
	url(r'^getassignedcourseids/$', 'UMCloudDj.views.getassignedcourseids_view', name='getassignedcourseids'),
	url(r'^assigned_courses/$', 'UMCloudDj.views.getassignedecourses_json', name='getassignedcourses_json'),
	url(r'^get_course_blocks/$', 'UMCloudDj.views.get_course_blocks', name='get_course_blocks'),
	url(r'^invite_to_course/$', 'UMCloudDj.views.invite_to_course', name='invite_to_course'),
	url(r'^register/invitation/$','UMCloudDj.views.check_invitation_view',  name='check_invitation_view'),

	#url(r'^updatelastactivity/$', 'report_statement.views.update_lastactivity', name='update_lastactivity'), #Internal fix only

   	url(r'^reports/lastactivity/$', 'report_statement.views.last_activity', name='last_activity'), #last activity report
	url(r'^reports/last_activity_selection/$', 'report_statement.views.last_activity_selection', name='last_activity_selection'), #last activity report selection
	url(r'^reports/durationreport_selection/$', 'report_statement.views.durationreport_selection', name='durationreport_selection'), #duration report selection
	url(r'^reports/durationreport/$', 'report_statement.views.durationreport', name='durationreport'), #duration report 
	url(r'^reports/durationreport/getstatements/(?P<userid>[-\w]+)/$', 'report_statement.views.user_statements_table'), #Get statements by userid
	url(r'^reports/stmtdb/$','report_statement.views.show_statements_from_db'), #SuperAdmin all statements
        url(r'^reports/allstatements/$','report_statement.views.statements_db_dynatable', name='allstatements'), #All organisation statements
	url(r'^reports/pagi_allstatements/$','report_statement.views.pagi_statements_db_dynatable', name='pagi_allstatements'), #All organisation statements
	#url(r'^reports/update_all_statementinfo/$', 'report_statement.views.update_all_statementinfo', name='update_all_statementinfo'), #SU SI update
	url(r'^reports/check_statementinfos/$', 'report_statement.views.check_statementinfos', name='check_statementinfos'),#Check si info
	url(r'^reports/statements_registration/$','report_statement.views.registration_statements', name='registration_statements'), #All registration statements
        url(r'^reports/mystmtsdynadb/$','report_statement.views.my_statements_db_dynatable'), #Current logged in user's statements
        url(r'^reports/usage_report','report_statement.views.test_usage_report'),  #Usage Report (Testing)
  	url(r'^reports/responsereport_selection/$', 'report_statement.views.response_report_selection', name='response_report_selection'), #Usage Report (Mockups)
	url(r'^reports/breakdown_report/$', 'report_statement.views.test_heather_report', name='heather_report'), #Breakdown report

	#For ajax fetchings
    	url(r'^fetch/allcategories/$','uploadeXe.views.allrootcategories', name='allcategories'),
	url(r'^fetch/allcategories/(?P<pk>\d+)$','uploadeXe.views.allsubcategories', name='allcategoriespk'),
	url(r'^fetch/allclass/(?P<allclassid>[-\w]+)/allclasse_students/$', 'report_statement.views.allclasse_students'),
 	url(r'^fetch/allcourses/','report_statement.views.allcourses',name='allcourses'),
	url(r'^fetch/allcourse/blocks/$', 'report_statement.views.allcourses_blocks', name='allcourses_blocks'),
	url(r'^fetch/allschools/','report_statement.views.allschools',name='allschools'),
	url(r'^fetch/school/allclasses/$', 'report_statement.views.school_allclasses', name='school_allclasses'),
	url(r'^fetch/allclass/students/$','report_statement.views.allclass_students', name='allclass_students'),
	#url(r'^fetch/superawesomeajax/$', 'report_statement.views.super_awesome_ajax_handler', name='super_awesome_ajax_handler'),
	url(r'^fetch/usage_report_data/$', 'report_statement.views.usage_report_data_ajax_handler', name='usage_report_data_ajax_handler'),


	#url(r'^testelpfiles/$', 'UMCloudDj.views.testelpfiles_view', name='testelpfiles'),
	#url(r'^selectelptest/$', 'UMCloudDj.views.elptestresults_selection_view', name='showelptestresults_selection'),
        #url(r'^selectapptest/$', 'UMCloudDj.views.apptestresults_selection_view', name='showappunittestresults_selection'),
	#url(r'^elptestresults/$', 'UMCloudDj.views.showelptestresults_view', name='showelptestresults'),
	#url(r'^apptestresults/$', 'UMCloudDj.views.showappunittestresults_view', name='showappunittestresults'),
	url(r'^getcourse/$', 'UMCloudDj.views.getcourse_view', name='getcourse'),
	url(r'^getblock/$', 'UMCloudDj.views.getblock_view', name='getblock'),
	url(r'^admin/', include(admin.site.urls)),
	url(r'^login/', 'UMCloudDj.views.loginview', name='login'),
	url(r'^auth/', 'UMCloudDj.views.auth_and_login'),
        url(r'^signup/', 'UMCloudDj.views.sign_up_in'),
	url(r'^orgsignup/', 'UMCloudDj.views.organisation_sign_up_in'),
        url(r'phoneinappreg/','UMCloudDj.views.phone_inapp_registration'),
        url(r'^home/$', 'UMCloudDj.views.secured',name='home'),
	url(r'^logout/$', 'UMCloudDj.views.logout_view'),
	url(r'^register/individual/$', 'UMCloudDj.views.register_individual_view', name='register_individual'),
	url(r'^register/org/$', 'UMCloudDj.views.register_organisation_view', name='register_organisation'),
	url(r'^register/start/$', 'UMCloudDj.views.register_selection_view', name='register_selection'),
	#url(r'^roles/$', 'UMCloudDj.views.role_list', name='role_list'),
	url(r'^rolestable/$', 'UMCloudDj.views.role_table', name='role_table'),
  	url(r'^rolenew/$', 'UMCloudDj.views.role_create', name='role_new'),
  	url(r'^roleedit/(?P<pk>\d+)$', 'UMCloudDj.views.role_update', name='role_edit'),
  	url(r'^roledelete/(?P<pk>\d+)$', 'UMCloudDj.views.role_delete', name='role_delete'),

	#url(r'^users/$', 'UMCloudDj.views.user_list', name='user_list'),
	url(r'^userstable/$', 'UMCloudDj.views.user_table', name='user_table'),
	url(r'^userstable/(?P<created>\d+)$', 'UMCloudDj.views.user_table', name='user_table'),
	url(r'^usersapprove/$','UMCloudDj.views.admin_approve_request', name='users_approve'),
 	#url(r'^userapprove/(?P<pk>\d+)$', 'UMCloudDj.views.user_approve_request', name='user_approve'),
        url(r'^usernew/$', 'UMCloudDj.views.user_create', name='user_new'),
        url(r'^useredit/(?P<pk>\d+)$', 'UMCloudDj.views.user_update', name='user_edit'),
        #url(r'^user/(?P<pk>\d+)$', 'UMCloudDj.views.user_profile', name='user_profile'),
        url(r'^userdelete/(?P<pk>\d+)$', 'UMCloudDj.views.user_delete', name='user_delete'),
  	#url(r'^upload_avatar/$', 'UMCloudDj.views.upload_avatar', name='upload_avatar'),

	url(r'^countryorgtable/$', 'organisation.views.country_organisation_table', name='countryorgtable'),
	url(r'^countryorgnew/$', 'organisation.views.country_organisation_create', name='countryorgnew'),
	url(r'newcountryorg/$', 'organisation.views.country_organisation_new', name='newcountryorg'),
	url(r'^countryorgedit/(?P<pk>\d+)$', 'organisation.views.country_organisation_edit', name='countryorgedit'),
	url(r'^countryorgdelete/(?P<pk>\d+)$', 'organisation.views.country_organisation_delete', name='countryorgdelete'),
	
	#url(r'^organisations/$', 'organisation.views.organisation_list', name='organisation_list'),
	url(r'^organisationstable/$', 'organisation.views.organisation_table', name='organisation_table'),
        url(r'^organisationnew/$', 'organisation.views.organisation_create', name='organisation_new'),
        url(r'^organisationedit/(?P<pk>\d+)$', 'organisation.views.organisation_update', name='organisation_edit'),
        url(r'^organisationdelete/(?P<pk>\d+)$', 'organisation.views.organisation_delete', name='organisation_delete'),
	url(r'^myorganisation/$', 'organisation.views.my_organisation', name='my_organisation'),
        url(r'^myorganisationedit/(?P<pk>\d+)$', 'organisation.views.my_organisation_update', name='my_organisation_update'),

	#url(r'^umpackages/$', 'organisation.views.umpackage_list', name='umpackage_list'),
	url(r'^umpackagestable/$', 'organisation.views.umpackage_table', name='umpackage_table'),
        url(r'^umpackagenew/$', 'organisation.views.umpackage_create', name='umpackage_new'),
        url(r'^umpackageedit/(?P<pk>\d+)$', 'organisation.views.umpackage_update', name='umpackage_edit'),
        url(r'^umpackagedelete/(?P<pk>\d+)$', 'organisation.views.umpackage_delete', name='umpackage_delete'),

	#url(r'^schools/$', 'school.views.school_list', name='school_list'),
	url(r'^schoolstable/$', 'school.views.school_table', name='school_table'),
        url(r'^schoolnew/$', 'school.views.school_create', name='school_new'),
        url(r'^schooledit/(?P<pk>\d+)$', 'school.views.school_update', name='school_edit'),
        url(r'^schooldelete/(?P<pk>\d+)$', 'school.views.school_delete', name='school_delete'),

	#url(r'^allclasses/$', 'allclass.views.allclass_list', name='allclass_list'),
	url(r'^allclassestable/$', 'allclass.views.allclass_table', name='allclass_table'),
        url(r'^allclassnew/$', 'allclass.views.allclass_create', name='allclass_new'),
        url(r'^allclassedit/(?P<pk>\d+)$', 'allclass.views.allclass_update', name='allclass_edit'),
        url(r'^allclassdelete/(?P<pk>\d+)$', 'allclass.views.allclass_delete', name='allclass_delete'),

	#url(r'^dynatableroles/$', 'UMCloudDj.views.role_dynatable', name='role_dynatable'),
	(r'^register/', RedirectView.as_view(url='/register/start/')),


	#url(r'^progressbarupload/', include('progressbarupload.urls')),

 	#For upload feature. Need both for file upload. The second one re directs to the url and first one does somehting related to that. 
	(r'^uploadeXe/', include('uploadeXe.urls')),
        #(r'^umlrs/', include('lrs.urls')),
	(r'^uploadeXe/$', RedirectView.as_view(url='/uploadeXe/list/')), # Just for ease of use.
	(r'^manageeXe/$', RedirectView.as_view(url='/uploadeXe/manage/')),
	(r'^managecourses/$',RedirectView.as_view(url='/uploadeXe/managecourses/')),
	(r'^messages/', include('django_messages.urls')),

) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

