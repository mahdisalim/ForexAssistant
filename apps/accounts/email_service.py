"""
Email Service - Gmail SMTP Integration
Handles all email notifications including verification, password reset, and subscription alerts
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from .models import EmailVerification, PasswordResetToken, EmailNotification

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Gmail SMTP"""
    
    def __init__(self):
        self.smtp_host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'EMAIL_PORT', 587)
        self.smtp_user = getattr(settings, 'EMAIL_HOST_USER', '')
        self.smtp_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', self.smtp_user)
        self.from_name = getattr(settings, 'EMAIL_FROM_NAME', 'Forex Assistant')
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send email via Gmail SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text fallback (optional)
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text version if provided
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
            return False
    
    def send_verification_email(self, user, language='fa') -> Optional[EmailVerification]:
        """
        Send email verification code
        
        Args:
            user: User instance
            language: 'fa' for Persian, 'en' for English
        
        Returns:
            EmailVerification instance if successful, None otherwise
        """
        try:
            # Generate verification code
            code = EmailVerification.generate_code()
            expires_at = timezone.now() + timedelta(minutes=15)
            
            # Create verification record
            verification = EmailVerification.objects.create(
                user=user,
                code=code,
                expires_at=expires_at
            )
            
            # Prepare email content
            context = {
                'user': user,
                'code': code,
                'expires_minutes': 15,
                'site_name': 'Forex Assistant',
            }
            
            if language == 'fa':
                subject = f'کد تایید ایمیل - {code}'
                html_content = render_to_string('emails/verification_fa.html', context)
            else:
                subject = f'Email Verification Code - {code}'
                html_content = render_to_string('emails/verification_en.html', context)
            
            # Send email
            success = self._send_email(user.email, subject, html_content)
            
            # Log notification
            EmailNotification.objects.create(
                user=user,
                notification_type='verification',
                subject=subject,
                is_successful=success,
                error_message='' if success else 'Failed to send email'
            )
            
            return verification if success else None
            
        except Exception as e:
            logger.error(f"Error sending verification email to {user.email}: {e}", exc_info=True)
            return None
    
    def send_password_reset_email(self, user, language='fa') -> Optional[PasswordResetToken]:
        """
        Send password reset link
        
        Args:
            user: User instance
            language: 'fa' for Persian, 'en' for English
        
        Returns:
            PasswordResetToken instance if successful, None otherwise
        """
        try:
            # Generate reset token
            token = PasswordResetToken.generate_token()
            expires_at = timezone.now() + timedelta(hours=1)
            
            # Create reset token record
            reset_token = PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=expires_at
            )
            
            # Build reset URL
            reset_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={token}"
            
            # Prepare email content
            context = {
                'user': user,
                'reset_url': reset_url,
                'expires_hours': 1,
                'site_name': 'Forex Assistant',
            }
            
            if language == 'fa':
                subject = 'بازیابی رمز عبور'
                html_content = render_to_string('emails/password_reset_fa.html', context)
            else:
                subject = 'Password Reset Request'
                html_content = render_to_string('emails/password_reset_en.html', context)
            
            # Send email
            success = self._send_email(user.email, subject, html_content)
            
            # Log notification
            EmailNotification.objects.create(
                user=user,
                notification_type='password_reset',
                subject=subject,
                is_successful=success,
                error_message='' if success else 'Failed to send email'
            )
            
            return reset_token if success else None
            
        except Exception as e:
            logger.error(f"Error sending password reset email to {user.email}: {e}", exc_info=True)
            return None
    
    def send_purchase_confirmation(self, user, plan_name: str, amount: float, language='fa') -> bool:
        """Send purchase confirmation email"""
        try:
            context = {
                'user': user,
                'plan_name': plan_name,
                'amount': amount,
                'purchase_date': timezone.now(),
                'site_name': 'Forex Assistant',
            }
            
            if language == 'fa':
                subject = f'تایید خرید اشتراک {plan_name}'
                html_content = render_to_string('emails/purchase_confirmation_fa.html', context)
            else:
                subject = f'Purchase Confirmation - {plan_name}'
                html_content = render_to_string('emails/purchase_confirmation_en.html', context)
            
            success = self._send_email(user.email, subject, html_content)
            
            EmailNotification.objects.create(
                user=user,
                notification_type='purchase',
                subject=subject,
                is_successful=success
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending purchase confirmation to {user.email}: {e}", exc_info=True)
            return False
    
    def send_expiry_warning(self, user, days_left: int, language='fa') -> bool:
        """
        Send subscription expiry warning
        
        Args:
            user: User instance
            days_left: Days until expiry (10, 5, or 3)
            language: 'fa' or 'en'
        """
        try:
            # Determine notification type
            notification_type = f'expiry_{days_left}'
            
            context = {
                'user': user,
                'days_left': days_left,
                'expiry_date': user.subscription_expires,
                'renewal_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/pricing",
                'site_name': 'Forex Assistant',
            }
            
            if language == 'fa':
                subject = f'یادآوری: {days_left} روز تا پایان اشتراک شما'
                html_content = render_to_string('emails/expiry_warning_fa.html', context)
            else:
                subject = f'Reminder: {days_left} Days Until Subscription Expires'
                html_content = render_to_string('emails/expiry_warning_en.html', context)
            
            success = self._send_email(user.email, subject, html_content)
            
            EmailNotification.objects.create(
                user=user,
                notification_type=notification_type,
                subject=subject,
                is_successful=success
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending expiry warning to {user.email}: {e}", exc_info=True)
            return False
    
    def send_subscription_expired(self, user, language='fa') -> bool:
        """Send subscription expired notification"""
        try:
            context = {
                'user': user,
                'expiry_date': user.subscription_expires,
                'renewal_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/pricing",
                'site_name': 'Forex Assistant',
            }
            
            if language == 'fa':
                subject = 'اشتراک شما به پایان رسید'
                html_content = render_to_string('emails/subscription_expired_fa.html', context)
            else:
                subject = 'Your Subscription Has Expired'
                html_content = render_to_string('emails/subscription_expired_en.html', context)
            
            success = self._send_email(user.email, subject, html_content)
            
            EmailNotification.objects.create(
                user=user,
                notification_type='expired',
                subject=subject,
                is_successful=success
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending expiry notification to {user.email}: {e}", exc_info=True)
            return False
    
    def send_discount_offer(self, user, discount_code: str, discount_percent: int, language='fa') -> bool:
        """Send discount offer email"""
        try:
            context = {
                'user': user,
                'discount_code': discount_code,
                'discount_percent': discount_percent,
                'valid_until': timezone.now() + timedelta(days=7),
                'pricing_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/pricing",
                'site_name': 'Forex Assistant',
            }
            
            if language == 'fa':
                subject = f'پیشنهاد ویژه: {discount_percent}% تخفیف برای شما!'
                html_content = render_to_string('emails/discount_offer_fa.html', context)
            else:
                subject = f'Special Offer: {discount_percent}% Discount for You!'
                html_content = render_to_string('emails/discount_offer_en.html', context)
            
            success = self._send_email(user.email, subject, html_content)
            
            EmailNotification.objects.create(
                user=user,
                notification_type='discount',
                subject=subject,
                is_successful=success
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending discount offer to {user.email}: {e}", exc_info=True)
            return False
    
    def send_event_notification(self, user, event_title: str, event_description: str, language='fa') -> bool:
        """Send event notification email"""
        try:
            context = {
                'user': user,
                'event_title': event_title,
                'event_description': event_description,
                'site_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
                'site_name': 'Forex Assistant',
            }
            
            if language == 'fa':
                subject = f'رویداد جدید: {event_title}'
                html_content = render_to_string('emails/event_notification_fa.html', context)
            else:
                subject = f'New Event: {event_title}'
                html_content = render_to_string('emails/event_notification_en.html', context)
            
            success = self._send_email(user.email, subject, html_content)
            
            EmailNotification.objects.create(
                user=user,
                notification_type='event',
                subject=subject,
                is_successful=success
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending event notification to {user.email}: {e}", exc_info=True)
            return False


# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """Get or create email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
