from django.urls import path
from . import views


app_name = 'users'
urlpatterns = [
    path('password-reset/', views.send_password_reset, name='send-password-reset'),
    path('password-reset-done/', views.password_reset_done, name='password-reset-done'),
    path('reset-password/<str:pk>/<str:password_reset_token>/', views.reset_password, name='reset-password'),
    path('reset-password-complete/', views.password_reset_complete, name='password-reset-complete'),
    path('change-password/', views.change_password, name='change-password'),
    path('signup/', views.signup, name='signup'),
    path('signup/complete', views.signup_complete, name='signup-complete'),
    path('give-me-script/', views.give_me_script, name='give-me-script'),
    #path('user/create/', views.create_user, name='create-user'),
    #path('user/edit/<int:pk>/', views.edit_user, name='edit-user'),
]
