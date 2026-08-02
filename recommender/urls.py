from django.urls import path
from recommender.views import *

urlpatterns = [
    path('',home,name='home'),
    path('signup/',signup_view,name='signup'),
    path('predict/',predict_view,name='predict'),
    path('logout/',logout_view,name='logout'),
    path('login/',login_view,name='login'),
    path('user_history/',user_history_view,name='user_history'),
    path('history_delete/<int:id>/',user_delete_prediction,name='user_delete_prediction'),
    path('profile/',profile_view,name='profile'),
    path('change_password/',change_password_view,name='change_password'),
    path('admin_login/',admin_login_view,name="admin_login"),
    path('admin_dashboard/',admin_dashboard_view,name="admin_dashboard"),
    path('admin_users_view/',admin_user_view,name='admin_view_users'),
    path('user_delete/<int:id>/',admin_user_delete,name='admin_user_delete'),
    path('admin_predictions/',admin_predictions_view,name='admin_predictions'),
    path('admin_delete_prediction/<int:id>/',admin_delete_prediction,name='admin_delete_prediction'),
    path('admin_logout/',admin_logout_view,name='admin_logout'),
    path('admin_change/',admin_change_password_view,name='admin_change'),




]
