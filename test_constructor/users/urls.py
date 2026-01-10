from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_api),
    path('login/', views.login_api),
    path('main/', views.main_page_api),
    path('logout/', views.logout_api),
    path('profile/', views.profile_view),
]