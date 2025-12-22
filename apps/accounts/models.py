"""
Custom User Model with Email Authentication
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import secrets


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, email2=None, password=None, **extra_fields):
        # Handle both create_superuser(email, password) and create_superuser(email, email, password)
        if email2 is not None and password is None:
            password = email2
        elif email2 is not None and password is not None:
            # Called with (email, email, password) - ignore email2
            pass
            
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model using email for authentication"""
    
    email = models.EmailField(unique=True, db_index=True)
    name = models.CharField(max_length=150, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Subscription
    subscription_plan = models.CharField(
        max_length=20,
        choices=[('free', 'Free'), ('premium', 'Premium')],
        default='free'
    )
    subscription_expires = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return self.name or self.email.split('@')[0]
    
    def get_short_name(self):
        return self.name.split()[0] if self.name else self.email.split('@')[0]


class AuthToken(models.Model):
    """Token for API authentication"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auth_tokens')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Token for {self.user.email}"
    
    @classmethod
    def generate_token(cls):
        return secrets.token_hex(32)
    
    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True


class EmailVerification(models.Model):
    """Email verification codes"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    code = models.CharField(max_length=6, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Verification code for {self.user.email}"
    
    @classmethod
    def generate_code(cls):
        """Generate 6-digit verification code"""
        import random
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    def is_valid(self):
        """Check if code is still valid"""
        if self.is_used:
            return False
        if timezone.now() > self.expires_at:
            return False
        return True


class PasswordResetToken(models.Model):
    """Password reset tokens"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Password reset for {self.user.email}"
    
    @classmethod
    def generate_token(cls):
        return secrets.token_urlsafe(32)
    
    def is_valid(self):
        if self.is_used:
            return False
        if timezone.now() > self.expires_at:
            return False
        return True


class EmailNotification(models.Model):
    """Track sent email notifications"""
    
    NOTIFICATION_TYPES = [
        ('verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
        ('purchase', 'Purchase Confirmation'),
        ('expiry_10', 'Expiry Warning - 10 Days'),
        ('expiry_5', 'Expiry Warning - 5 Days'),
        ('expiry_3', 'Expiry Warning - 3 Days'),
        ('expired', 'Subscription Expired'),
        ('discount', 'Discount Offer'),
        ('event', 'Event Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    subject = models.CharField(max_length=255)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['user', 'notification_type', '-sent_at']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} to {self.user.email}"
