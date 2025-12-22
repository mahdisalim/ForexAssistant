#!/usr/bin/env python3
"""
Test Email System in Docker Container
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forex_assistant.settings')
django.setup()

from django.conf import settings
from apps.accounts.models import User, EmailVerification, EmailNotification
from apps.accounts.email_service import get_email_service

print("=" * 70)
print("🧪 Testing Email System in Docker Container")
print("=" * 70)

# Test 1: Check Settings
print("\n1️⃣ Checking Settings...")
print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"   CELERY_BROKER_URL: {settings.CELERY_BROKER_URL}")
print("   ✅ Settings OK")

# Test 2: Check Models
print("\n2️⃣ Checking Database...")
try:
    user_count = User.objects.count()
    print(f"   Users: {user_count}")
    
    verification_count = EmailVerification.objects.count()
    print(f"   Email Verifications: {verification_count}")
    
    notification_count = EmailNotification.objects.count()
    print(f"   Email Notifications: {notification_count}")
    print("   ✅ Database OK")
except Exception as e:
    print(f"   ❌ Database error: {e}")
    sys.exit(1)

# Test 3: Test EmailService
print("\n3️⃣ Testing EmailService...")
try:
    email_service = get_email_service()
    print("   ✅ EmailService initialized")
    
    # Test SMTP
    import smtplib
    server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
    server.starttls()
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    server.quit()
    print("   ✅ SMTP connection successful")
    
except Exception as e:
    print(f"   ❌ EmailService error: {e}")
    sys.exit(1)

# Test 4: Send Test Email
print("\n4️⃣ Sending Test Email...")
try:
    if user_count > 0:
        test_user = User.objects.first()
        print(f"   Testing with: {test_user.email}")
        
        verification = email_service.send_verification_email(test_user, 'fa')
        if verification:
            print(f"   ✅ Email sent! Code: {verification.code}")
            print(f"   📧 Check inbox: {test_user.email}")
        else:
            print("   ❌ Failed to send")
    else:
        print("   ℹ️  No users - skipping")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Check Celery
print("\n5️⃣ Checking Celery...")
try:
    from forex_assistant.celery import app
    print(f"   Broker: {app.conf.broker_url}")
    
    if app.conf.beat_schedule:
        print("   📅 Scheduled tasks:")
        for name in app.conf.beat_schedule.keys():
            print(f"      - {name}")
    print("   ✅ Celery configured")
    
except Exception as e:
    print(f"   ⚠️  Celery: {e}")

print("\n" + "=" * 70)
print("✅ Email System Test Completed!")
print("=" * 70)
