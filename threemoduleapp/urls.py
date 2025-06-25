from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('teacher_register/', views.teacher_register, name='teacher_register'),
    path('student_register/', views.student_register, name='student_register'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('approve_user/<int:user_id>/', views.approve_user, name='approve_user'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('add_course/', views.add_course, name='add_course'),
    path('password_reset/', views.password_reset_request, name='password_reset_request'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('teacher_dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('change_password/', views.change_password, name='change_password'),

]