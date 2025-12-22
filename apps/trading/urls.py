"""
URL Configuration for Trading App
"""
from django.urls import path
from . import views

urlpatterns = [
    # Trading Accounts
    path('trading-accounts/', views.list_trading_accounts, name='list_accounts'),
    path('trading-accounts/add/', views.add_trading_account, name='add_account'),
    path('trading-accounts/<int:account_id>/refresh/', views.refresh_trading_account, name='refresh_account'),
    path('trading-accounts/<int:account_id>/risk/', views.update_account_risk, name='update_risk'),
    path('trading-accounts/<int:account_id>/', views.delete_trading_account, name='delete_account'),
    
    # Trading Robots
    path('robots/available/', views.get_available_robots, name='available_robots'),
    path('robots/', views.list_user_robots, name='list_robots'),
    path('robots/create/', views.create_robot, name='create_robot'),
    path('robots/<int:robot_id>/', views.update_robot, name='update_robot'),
    path('robots/<int:robot_id>/delete/', views.delete_robot, name='delete_robot'),
]
