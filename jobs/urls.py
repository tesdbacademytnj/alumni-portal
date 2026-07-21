from django.urls import path
from . import views

urlpatterns = [
    path('post-opening/',             views.post_opening,         name='post_opening'),
    path('admin-post-opening/',       views.admin_post_opening,   name='admin_post_opening'),
    path('seek-job/',                 views.seek_job,          name='seek_job'),
    path('my-opening/<int:pk>/',      views.my_opening_detail, name='my_opening_detail'),
    path('my-application/<int:pk>/',  views.my_seeker_detail,  name='my_seeker_detail'),

    path('board/',                    views.job_board,         name='job_board'),
    path('board/<int:pk>/',           views.job_detail,        name='job_detail'),
    path('board/<int:pk>/quick-view/',views.job_quick_view,    name='job_quick_view'),
    path('board/<int:pk>/apply/',     views.job_apply,         name='job_apply'),
    path('board/<int:pk>/interest/',  views.toggle_interest,   name='toggle_interest'),
    path('board/<int:pk>/interests/', views.interest_list,     name='interest_list'),
]
