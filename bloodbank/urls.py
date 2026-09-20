"""URL routes for the bloodbank application.

These patterns are mounted at the site root by ``cse370.urls``.
"""

from django.urls import path

from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),

    # Member area
    path('profile/', views.profile, name='profile'),
    path('profile/donor-status/', views.toggle_donor_status, name='toggle_donor_status'),
    path('search/', views.search, name='search'),

    # Manager area
    path('dashboard/', views.dashboard, name='dashboard'),
    path('stock/', views.blood_details, name='blood_details'),
    path('stock/entry/', views.blood_entry, name='blood_entry'),
    path('stock/issue/', views.blood_issue, name='blood_issue'),
    path('members/', views.user_list, name='user_list'),
    path('members/<int:user_id>/deactivate/', views.deactivate_user, name='deactivate_user'),
]
