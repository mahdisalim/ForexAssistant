#!/usr/bin/env python3
"""
Simple SMTP Test - No Django Required
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

print("=" * 60)
print("🧪 Testing Gmail SMTP Connection")
print("=" * 60)

# Email configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'mohammadmahdishakhssalim@gmail.com'
EMAIL_PASSWORD = 'egaeaizctnlwapjg'  # بدون فاصله

print(f"\n📧 Configuration:")
print(f"   Host: {EMAIL_HOST}")
print(f"   Port: {EMAIL_PORT}")
print(f"   User: {EMAIL_USER}")
print(f"   Password: {'*' * 16}")

# Test 1: SMTP Connection
print(f"\n1️⃣ Testing SMTP Connection...")
try:
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
    print("   ✅ Connected to SMTP server")
    
    server.starttls()
    print("   ✅ TLS started")
    
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    print("   ✅ Login successful!")
    
    server.quit()
    print("   ✅ Connection closed")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"   ❌ Authentication failed: {e}")
    print("\n💡 Troubleshooting:")
    print("   1. Make sure 2-Step Verification is enabled")
    print("   2. Generate a new App Password at: https://myaccount.google.com/apppasswords")
    print("   3. Copy the password without spaces")
    exit(1)
    
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    exit(1)

# Test 2: Send Test Email
print(f"\n2️⃣ Sending Test Email...")
try:
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = '🧪 Test Email from Forex Assistant'
    msg['From'] = f'Forex Assistant <{EMAIL_USER}>'
    msg['To'] = EMAIL_USER
    
    # HTML content
    html = """
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #667eea; text-align: center;">✅ Email System Test Successful!</h2>
            <p style="font-size: 16px; color: #333;">Your Gmail SMTP configuration is working correctly.</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #667eea; margin-top: 0;">Configuration Details:</h3>
                <ul style="color: #666;">
                    <li>SMTP Host: smtp.gmail.com</li>
                    <li>Port: 587</li>
                    <li>TLS: Enabled ✅</li>
                    <li>Authentication: Successful ✅</li>
                </ul>
            </div>
            
            <p style="color: #28a745; font-weight: bold; text-align: center; font-size: 18px;">
                🎉 Your email system is ready to use!
            </p>
            
            <p style="color: #666; font-size: 12px; text-align: center; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 15px;">
                This is an automated test email from Forex Assistant Email System<br>
                Sent on: """ + str(__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + """
            </p>
        </div>
    </body>
    </html>
    """
    
    # Plain text fallback
    text = """
    ✅ Email System Test Successful!
    
    Your Gmail SMTP configuration is working correctly.
    
    Configuration Details:
    - SMTP Host: smtp.gmail.com
    - Port: 587
    - TLS: Enabled
    - Authentication: Successful
    
    🎉 Your email system is ready to use!
    """
    
    part1 = MIMEText(text, 'plain', 'utf-8')
    part2 = MIMEText(html, 'html', 'utf-8')
    
    msg.attach(part1)
    msg.attach(part2)
    
    # Send email
    server.send_message(msg)
    server.quit()
    
    print(f"   ✅ Test email sent successfully!")
    print(f"   📧 Check your inbox: {EMAIL_USER}")
    
except Exception as e:
    print(f"   ❌ Failed to send email: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("✅ All Tests Passed!")
print("=" * 60)
print("\n📝 Summary:")
print("   ✅ SMTP Connection: Working")
print("   ✅ Authentication: Successful")
print("   ✅ Email Sending: Working")
print("\n🎉 Your Gmail SMTP is configured correctly!")
print(f"📧 Check your email at: {EMAIL_USER}")
