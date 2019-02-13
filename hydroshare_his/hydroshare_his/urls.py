from django.contrib import admin
from django.urls import include
from django.conf.urls import url
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import path
from hydroshare_his import settings


schema_view = get_schema_view(
   openapi.Info(
      title="HydroShare HIS API",
      default_version='v1.0',
      description="HydroShare HIS Rest API",
      contact=openapi.Contact(email="kjlippold@gmail.com")
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   url=settings.PROXY_BASE_URL
)

urlpatterns = [
    url(r'^his/admin/', admin.site.urls),
    url(r'^his/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^his/services/', include('web_services_manager.urls')),
]
