from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from web_services_manager import views

#(?P<resource_id>[\w\-]+)
#(?P<file_path>.*)

urlpatterns = [
    url(r'^update/(?P<resource_id>[\w\-]+)/$', views.Services.as_view({"post":"post_update_services"}), name="update_services"),
]

urlpatterns = format_suffix_patterns(urlpatterns, allowed=None)
