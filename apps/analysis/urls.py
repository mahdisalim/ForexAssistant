"""
URL Configuration for Analysis App
"""
from django.urls import path
from . import views

urlpatterns = [
    path('pairs/', views.list_pairs, name='list_pairs'),
    path('pairs/add/', views.add_pair, name='add_pair'),
    path('pairs/<str:pair>/', views.remove_pair, name='remove_pair'),
    
    path('analysis/', views.get_all_analysis, name='all_analysis'),
    path('analysis/<str:pair>/', views.get_analysis, name='pair_analysis'),
    path('analysis/chart-image/', views.analyze_chart_image, name='analyze_chart_image'),
    
    path('summary/', views.get_summary, name='summary'),
    path('timeframes/', views.get_timeframes, name='timeframes'),
    path('mtf/<str:pair>/', views.get_mtf_analysis, name='mtf_analysis'),
    path('translate/', views.translate_text, name='translate'),
]
