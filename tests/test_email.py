#!/usr/bin/env python3
"""
Test Email System - SMTP Connection and Email Sending
"""
import os
import sys
import django
from pathlib import Path

# Add project to path
sys.path.insert(0, '/srv')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.django_settings')

# Setup Django
django.setup()

from dotenv import load_dotenv
load_dotenv('/srv/.env')

print("=" * 60)
print("🧪 Testing Email System")
print("=" * 60)

# Test 1: Check environment variables
print("\n1️⃣ Checking Environment Variables...")
email_user = os.getenv('EMAIL_HOST_USER')
email_pass = os.getenv('EMAIL_HOST_PASSWORD')
email_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
email_port = int(os.getenv('EMAIL_PORT', 587))

print(f"   EMAIL_HOST: {email_host}")
print(f"   EMAIL_PORT: {email_port}")
print(f"   EMAIL_HOST_USER: {email_user}")
print(f"   EMAIL_HOST_PASSWORD: {'*' * len(email_pass) if email_pass else 'NOT SET'}")

if not email_user or not email_pass:
    print("   ❌ Email credentials not found in .env file!")
    sys.exit(1)
else:
    print("   ✅ Email credentials found")

# Test 2: Test SMTP connection
print("\n2️⃣ Testing SMTP Connection...")
try:
    import smtplib
    server = smtplib.SMTP(email_host, email_port)
    server.starttls()
    server.login(email_user, email_pass)
    print("   ✅ SMTP connection successful!")
    server.quit()
except Exception as e:
    print(f"   ❌ SMTP connection failed: {e}")
    sys.exit(1)

# Test 3: Test EmailService
print("\n3️⃣ Testing EmailService...")
try:
    from apps.accounts.email_service import get_email_service
    email_service = get_email_service()
    print("   ✅ EmailService initialized")
except Exception as e:
    print(f"   ❌ EmailService initialization failed: {e}")
    sys.exit(1)

# Test 4: Send test email
print("\n4️⃣ Sending Test Email...")
try:
    success = email_service._send_email(
        to_email=email_user,  # Send to yourself
        subject='🧪 Test Email from Forex Assistant',
        html_content='''
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #667eea;">✅ Email System Test Successful!</h2>
            <p>Your email system is working correctly.</p>
            <p><strong>Configuration:</strong></p>
            <ul>
                <li>SMTP Host: smtp.gmail.com</li>
                <li>Port: 587</li>
                <li>TLS: Enabled</li>
            </ul>
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated test email from Forex Assistant.
            </p>
        </body>
        </html>
        ''',
        text_content='Email System Test - Your email system is working correctly!'
    )
    
    if success:
        print(f"   ✅ Test email sent successfully to {email_user}")
        print(f"   📧 Check your inbox!")
    else:
        print("   ❌ Failed to send test email")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ Error sending test email: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Test with User model (if users exist)
print("\n5️⃣ Testing with User Model...")
try:
    from apps.accounts.models import User
    
    user_count = User.objects.count()
    print(f"   Found {user_count} users in database")
    
    if user_count > 0:
        test_user = User.objects.first()
        print(f"   Testing with user: {test_user.email}")
        
        # Test verification email
        verification = email_service.send_verification_email(test_user, language='fa')
        if verification:
            print(f"   ✅ Verification email sent! Code: {verification.code}")
            print(f"   ⏰ Expires at: {verification.expires_at}")
        else:
            print("   ⚠️  Verification email failed (check logs)")
    else:
        print("   ℹ️  No users found - skipping user-based tests")
        
except Exception as e:
    print(f"   ⚠️  User model test failed: {e}")

print("\n" + "=" * 60)
print("✅ All Tests Completed!")
print("=" * 60)
print("\n📝 Summary:")
print("   - SMTP connection: Working")
print("   - Email sending: Working")
print("   - EmailService: Working")
print("\n🎉 Your email system is ready to use!")
