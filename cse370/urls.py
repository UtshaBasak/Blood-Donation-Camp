"""Root URL configuration for the cse370 project.

The Django admin lives under ``/admin/``; everything else is delegated to the
``bloodbank`` application.

Docs: https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('bloodbank.urls')),
]

admin.site.site_header = 'Blood Donation Camp administration'
admin.site.site_title = 'Blood Donation Camp'
admin.site.index_title = 'Manage donors, branches and stock'
