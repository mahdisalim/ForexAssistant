"""
Secure Authentication Service
Handles user authentication, password hashing, and token management.
All sensitive operations are performed server-side for security.
"""

import hashlib
import secrets
import json
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class User:
    """User data model"""
    email: str
    name: str
    password_hash: str
    created_at: str
    last_login: Optional[str] = None
    token: Optional[str] = None
    token_expires: Optional[str] = None
    
    def to_safe_dict(self) -> Dict[str, Any]:
        """Return user data without sensitive fields"""
        return {
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at,
            "last_login": self.last_login
        }


class PasswordService:
    """Secure password hashing service"""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> str:
        """
        Hash password with salt using SHA256.
        In production, consider using bcrypt or argon2.
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Multiple rounds of hashing for added security
        hashed = password
        for _ in range(1000):
            hashed = hashlib.sha256(f"{salt}:{hashed}".encode()).hexdigest()
        
        return f"{salt}${hashed}"
    
    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        if "$" in stored_hash:
            # New format with salt
            salt, _ = stored_hash.split("$", 1)
            return PasswordService.hash_password(password, salt) == stored_hash
        else:
            # Legacy format (plain SHA256)
            return hashlib.sha256(password.encode()).hexdigest() == stored_hash


class TokenService:
    """Secure token management service"""
    
    TOKEN_EXPIRY_HOURS = 24 * 7  # 7 days
    
    @staticmethod
    def generate_token() -> str:
        """Generate a cryptographically secure random token"""
        return secrets.token_urlsafe(48)
    
    @staticmethod
    def get_token_expiry() -> str:
        """Get token expiry datetime"""
        expiry = datetime.now() + timedelta(hours=TokenService.TOKEN_EXPIRY_HOURS)
        return expiry.isoformat()
    
    @staticmethod
    def is_token_expired(expiry_str: Optional[str]) -> bool:
        """Check if token is expired"""
        if not expiry_str:
            return False  # Legacy tokens don't expire
        try:
            expiry = datetime.fromisoformat(expiry_str)
            return datetime.now() > expiry
        except:
            return False


class EmailValidator:
    """Email validation service"""
    
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    @staticmethod
    def is_valid(email: str) -> bool:
        """Validate email format"""
        return bool(EmailValidator.EMAIL_REGEX.match(email))
    
    @staticmethod
    def normalize(email: str) -> str:
        """Normalize email (lowercase, strip whitespace)"""
        return email.lower().strip()


class AuthService:
    """
    Main authentication service.
    Handles user registration, login, and session management.
    """
    
    MIN_PASSWORD_LENGTH = 8
    
    def __init__(self, users_file: Path):
        self.users_file = users_file
        self.password_service = PasswordService()
        self.token_service = TokenService()
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Ensure users file exists"""
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.users_file.exists():
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
    
    def _load_users(self) -> Dict[str, Dict]:
        """Load users from file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            return {}
    
    def _save_users(self, users: Dict[str, Dict]):
        """Save users to file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def register(self, name: str, email: str, password: str) -> Dict[str, Any]:
        """
        Register a new user.
        Returns user data and token on success, error on failure.
        """
        # Validate email
        email = EmailValidator.normalize(email)
        if not EmailValidator.is_valid(email):
            return {"success": False, "error": "Invalid email format"}
        
        # Validate password
        if len(password) < self.MIN_PASSWORD_LENGTH:
            return {"success": False, "error": f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters"}
        
        # Check if user exists
        users = self._load_users()
        if email in users:
            return {"success": False, "error": "Email already registered"}
        
        # Create user
        token = self.token_service.generate_token()
        now = datetime.now().isoformat()
        
        users[email] = {
            "name": name.strip(),
            "password": self.password_service.hash_password(password),
            "created_at": now,
            "last_login": now,
            "token": token,
            "token_expires": self.token_service.get_token_expiry()
        }
        
        self._save_users(users)
        logger.info(f"New user registered: {email}")
        
        return {
            "success": True,
            "user": {
                "email": email,
                "name": name.strip(),
                "created_at": now
            },
            "token": token
        }
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and return token.
        """
        email = EmailValidator.normalize(email)
        users = self._load_users()
        
        if email not in users:
            return {"success": False, "error": "Invalid email or password"}
        
        user = users[email]
        
        # Verify password
        if not self.password_service.verify_password(password, user.get("password", "")):
            return {"success": False, "error": "Invalid email or password"}
        
        # Generate new token
        token = self.token_service.generate_token()
        user["last_login"] = datetime.now().isoformat()
        user["token"] = token
        user["token_expires"] = self.token_service.get_token_expiry()
        
        users[email] = user
        self._save_users(users)
        
        return {
            "success": True,
            "user": {
                "email": email,
                "name": user.get("name", email.split("@")[0]),
                "created_at": user.get("created_at")
            },
            "token": token
        }
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify token and return user data if valid.
        """
        if not token:
            return None
        
        users = self._load_users()
        
        for email, user in users.items():
            if user.get("token") == token:
                # Check expiry
                if self.token_service.is_token_expired(user.get("token_expires")):
                    return None
                
                return {
                    "email": email,
                    "name": user.get("name", email.split("@")[0]),
                    "created_at": user.get("created_at")
                }
        
        return None
    
    def logout(self, token: str) -> bool:
        """
        Invalidate user token.
        """
        users = self._load_users()
        
        for email, user in users.items():
            if user.get("token") == token:
                user["token"] = None
                user["token_expires"] = None
                users[email] = user
                self._save_users(users)
                return True
        
        return False
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email (without sensitive data)"""
        email = EmailValidator.normalize(email)
        users = self._load_users()
        
        if email in users:
            user = users[email]
            return {
                "email": email,
                "name": user.get("name"),
                "created_at": user.get("created_at"),
                "last_login": user.get("last_login")
            }
        
        return None
