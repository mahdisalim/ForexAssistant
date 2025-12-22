"""
URL Configuration for Accounts App
"""
from django.urls import path
from . import views

urlpatterns = [
    # Page routes
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('pricing/', views.pricing_page, name='pricing'),
    path('thank-you/', views.thank_you_page, name='thank_you'),
    path('features/', views.features_page, name='features'),
    path('resources/', views.resources_page, name='resources'),
    path('assets/', views.assets_page, name='assets'),
    path('signup/', views.signup_page, name='signup'),
    path('signin/', views.signin_page, name='signin'),
    path('chart/', views.chart_view, name='chart'),
    
    # API routes (with and without trailing slash for compatibility)
    path('api/auth/signup/', views.sign_up, name='api_signup'),
    path('api/auth/signup', views.sign_up, name='api_signup_no_slash'),
    path('api/auth/signin/', views.sign_in, name='api_signin'),
    path('api/auth/signin', views.sign_in, name='api_signin_no_slash'),
    path('api/auth/logout/', views.logout, name='api_logout'),
    path('api/auth/logout', views.logout, name='api_logout_no_slash'),
    path('api/auth/me/', views.get_current_user, name='api_me'),
    path('api/auth/me', views.get_current_user, name='api_me_no_slash'),
    path('api/health/', views.health_check, name='api_health'),
    path('api/health', views.health_check, name='api_health_no_slash'),
]
