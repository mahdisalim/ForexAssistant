"""
Celery Tasks for Email Notifications and Subscription Management
"""
import logging
from datetime import timedelta
from django.utils import timezone
from celery import shared_task

from .models import User, EmailNotification
from .email_service import get_email_service

logger = logging.getLogger(__name__)


@shared_task
def check_subscription_expiry():
    """
    Check all users for upcoming subscription expiry
    Send warnings at 10, 5, and 3 days before expiry
    Run this task daily
    """
    try:
        email_service = get_email_service()
        now = timezone.now()
        
        # Get users with active premium subscriptions
        users = User.objects.filter(
            subscription_plan='premium',
            subscription_expires__isnull=False,
            subscription_expires__gt=now
        )
        
        for user in users:
            days_until_expiry = (user.subscription_expires - now).days
            
            # Check if we need to send a warning
            if days_until_expiry in [10, 5, 3]:
                # Check if we already sent this warning
                notification_type = f'expiry_{days_until_expiry}'
                recent_notification = EmailNotification.objects.filter(
                    user=user,
                    notification_type=notification_type,
                    sent_at__gte=now - timedelta(hours=12)  # Don't send twice in 12 hours
                ).exists()
                
                if not recent_notification:
                    logger.info(f"Sending {days_until_expiry}-day expiry warning to {user.email}")
                    email_service.send_expiry_warning(user, days_until_expiry, language='fa')
        
        logger.info(f"Subscription expiry check completed. Checked {users.count()} users.")
        
    except Exception as e:
        logger.error(f"Error in check_subscription_expiry task: {e}", exc_info=True)


@shared_task
def check_expired_subscriptions():
    """
    Check for expired subscriptions and send notifications
    Run this task daily
    """
    try:
        email_service = get_email_service()
        now = timezone.now()
        
        # Get users whose subscription just expired (within last 24 hours)
        users = User.objects.filter(
            subscription_plan='premium',
            subscription_expires__isnull=False,
            subscription_expires__lte=now,
            subscription_expires__gte=now - timedelta(days=1)
        )
        
        for user in users:
            # Check if we already sent expiry notification
            recent_notification = EmailNotification.objects.filter(
                user=user,
                notification_type='expired',
                sent_at__gte=now - timedelta(hours=12)
            ).exists()
            
            if not recent_notification:
                logger.info(f"Sending expiry notification to {user.email}")
                email_service.send_subscription_expired(user, language='fa')
                
                # Downgrade to free plan
                user.subscription_plan = 'free'
                user.save(update_fields=['subscription_plan'])
        
        logger.info(f"Expired subscription check completed. Processed {users.count()} users.")
        
    except Exception as e:
        logger.error(f"Error in check_expired_subscriptions task: {e}", exc_info=True)


@shared_task
def send_verification_email_task(user_id: int, language: str = 'fa'):
    """
    Send email verification code (async task)
    
    Args:
        user_id: User ID
        language: 'fa' or 'en'
    """
    try:
        user = User.objects.get(id=user_id)
        email_service = get_email_service()
        email_service.send_verification_email(user, language)
        logger.info(f"Verification email sent to {user.email}")
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
    except Exception as e:
        logger.error(f"Error sending verification email: {e}", exc_info=True)


@shared_task
def send_password_reset_task(user_id: int, language: str = 'fa'):
    """
    Send password reset email (async task)
    
    Args:
        user_id: User ID
        language: 'fa' or 'en'
    """
    try:
        user = User.objects.get(id=user_id)
        email_service = get_email_service()
        email_service.send_password_reset_email(user, language)
        logger.info(f"Password reset email sent to {user.email}")
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
    except Exception as e:
        logger.error(f"Error sending password reset email: {e}", exc_info=True)


@shared_task
def send_purchase_confirmation_task(user_id: int, plan_name: str, amount: float, language: str = 'fa'):
    """
    Send purchase confirmation email (async task)
    
    Args:
        user_id: User ID
        plan_name: Subscription plan name
        amount: Purchase amount
        language: 'fa' or 'en'
    """
    try:
        user = User.objects.get(id=user_id)
        email_service = get_email_service()
        email_service.send_purchase_confirmation(user, plan_name, amount, language)
        logger.info(f"Purchase confirmation sent to {user.email}")
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
    except Exception as e:
        logger.error(f"Error sending purchase confirmation: {e}", exc_info=True)


@shared_task
def send_discount_offer_task(user_id: int, discount_code: str, discount_percent: int, language: str = 'fa'):
    """
    Send discount offer email (async task)
    
    Args:
        user_id: User ID
        discount_code: Discount code
        discount_percent: Discount percentage
        language: 'fa' or 'en'
    """
    try:
        user = User.objects.get(id=user_id)
        email_service = get_email_service()
        email_service.send_discount_offer(user, discount_code, discount_percent, language)
        logger.info(f"Discount offer sent to {user.email}")
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
    except Exception as e:
        logger.error(f"Error sending discount offer: {e}", exc_info=True)


@shared_task
def send_event_notification_task(user_id: int, event_title: str, event_description: str, language: str = 'fa'):
    """
    Send event notification email (async task)
    
    Args:
        user_id: User ID
        event_title: Event title
        event_description: Event description
        language: 'fa' or 'en'
    """
    try:
        user = User.objects.get(id=user_id)
        email_service = get_email_service()
        email_service.send_event_notification(user, event_title, event_description, language)
        logger.info(f"Event notification sent to {user.email}")
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
    except Exception as e:
        logger.error(f"Error sending event notification: {e}", exc_info=True)


@shared_task
def bulk_send_discount_offer(discount_code: str, discount_percent: int, language: str = 'fa'):
    """
    Send discount offer to all active users
    
    Args:
        discount_code: Discount code
        discount_percent: Discount percentage
        language: 'fa' or 'en'
    """
    try:
        email_service = get_email_service()
        users = User.objects.filter(is_active=True)
        
        sent_count = 0
        for user in users:
            try:
                success = email_service.send_discount_offer(user, discount_code, discount_percent, language)
                if success:
                    sent_count += 1
            except Exception as e:
                logger.error(f"Error sending discount to {user.email}: {e}")
                continue
        
        logger.info(f"Bulk discount offer completed. Sent to {sent_count}/{users.count()} users.")
        
    except Exception as e:
        logger.error(f"Error in bulk_send_discount_offer task: {e}", exc_info=True)


@shared_task
def bulk_send_event_notification(event_title: str, event_description: str, language: str = 'fa'):
    """
    Send event notification to all active users
    
    Args:
        event_title: Event title
        event_description: Event description
        language: 'fa' or 'en'
    """
    try:
        email_service = get_email_service()
        users = User.objects.filter(is_active=True)
        
        sent_count = 0
        for user in users:
            try:
                success = email_service.send_event_notification(user, event_title, event_description, language)
                if success:
                    sent_count += 1
            except Exception as e:
                logger.error(f"Error sending event notification to {user.email}: {e}")
                continue
        
        logger.info(f"Bulk event notification completed. Sent to {sent_count}/{users.count()} users.")
        
    except Exception as e:
        logger.error(f"Error in bulk_send_event_notification task: {e}", exc_info=True)
