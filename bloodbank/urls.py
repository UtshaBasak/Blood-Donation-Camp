"""
URL configuration for cse370 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from xml.etree.ElementInclude import include
from .  import views
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('', views.home, name='home'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('register', views.register, name='register'),
    path('about', views.about, name='about'),
    path('profile', views.profile, name='profile'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('entry', views.entry, name='entry'),
    path('details', views.details, name='details'),
    path('list', views.list, name='list'),
    path('donate', views.donate, name='donate'),
    path('search', views.search, name='search'),
    # path('donor_list', views.donor_list, name='donor_list'),

    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('users/<int:user_id>/update_active_status/', views.update_active_status, name='update_active_status'),

]
