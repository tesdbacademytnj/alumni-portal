from django.urls import path
from . import views

urlpatterns = [
    path('user-register/',           views.user_register,      name='user_register'),
    path('verify-otp/',              views.verify_otp,         name='verify_otp'),
    path('resend-otp/',              views.resend_otp,         name='resend_otp'),
    path('user-login/',              views.user_login,         name='user_login'),
    path('admin-login/',             views.admin_login,        name='admin_login'),
    path('logout/',                  views.user_logout,        name='logout'),
    path('forgot-password/',         views.forgot_password,    name='forgot_password'),
    path('verify-reset-otp/',        views.verify_reset_otp,   name='verify_reset_otp'),
    path('resend-reset-otp/',        views.resend_reset_otp,   name='resend_reset_otp'),
    path('reset-password/',          views.reset_password,     name='reset_password'),
    path('dashboard/',               views.dashboard,          name='dashboard'),
    path('edit-profile/',            views.edit_profile,       name='edit_profile'),
    path('admin-dashboard/',         views.admin_dashboard,    name='admin_dashboard'),
    path('admin/user/<int:user_id>/',        views.user_detail,        name='user_detail'),
    path('admin/message/<int:message_id>/read/', views.mark_message_read, name='mark_message_read'),
    path('admin/job/<int:pk>/publish/',   views.publish_job,   name='publish_job'),
    path('admin/job/<int:pk>/reject/',    views.reject_job,    name='reject_job'),
    path('admin/job/<int:pk>/unpublish/', views.unpublish_job, name='unpublish_job'),
]
