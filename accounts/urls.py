from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.role_dashboard_view, name='role_dashboard'),
    path('dashboard/instructor/', views.instructor_dashboard_view, name='instructor_dashboard'),
    path('dashboard/student/', views.student_dashboard_view, name='student_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
]
