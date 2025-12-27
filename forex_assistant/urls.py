"""
URL Configuration for Forex Analysis Assistant
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Apps URLs
    path('', include('apps.accounts.urls')),
    path('api/', include('apps.analysis.urls')),
    path('api/', include('apps.trading.urls')),
    path('api/', include('apps.scraping.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
