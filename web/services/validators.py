"""
Input Validation Service
Provides secure input validation for all user inputs.
Prevents injection attacks and ensures data integrity.
"""

import re
import html
from typing import Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    error: Optional[str] = None
    sanitized_value: Optional[str] = None


class InputSanitizer:
    """Sanitize user inputs to prevent XSS and injection attacks"""
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Escape HTML special characters"""
        return html.escape(text)
    
    @staticmethod
    def sanitize_sql(text: str) -> str:
        """Remove potential SQL injection characters"""
        # Remove or escape dangerous characters
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
        result = text
        for char in dangerous_chars:
            result = result.replace(char, "")
        return result
    
    @staticmethod
    def strip_tags(text: str) -> str:
        """Remove all HTML tags from text"""
        return re.sub(r'<[^>]+>', '', text)
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace (single spaces, trim)"""
        return ' '.join(text.split())


class EmailValidator:
    """Email validation"""
    
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    MAX_LENGTH = 254
    
    @classmethod
    def validate(cls, email: str) -> ValidationResult:
        """Validate email format"""
        if not email:
            return ValidationResult(False, "Email is required")
        
        email = email.lower().strip()
        
        if len(email) > cls.MAX_LENGTH:
            return ValidationResult(False, f"Email must be less than {cls.MAX_LENGTH} characters")
        
        if not cls.EMAIL_REGEX.match(email):
            return ValidationResult(False, "Invalid email format")
        
        return ValidationResult(True, sanitized_value=email)


class PasswordValidator:
    """Password validation"""
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    
    @classmethod
    def validate(cls, password: str, require_special: bool = False) -> ValidationResult:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            require_special: Whether to require special characters
        """
        if not password:
            return ValidationResult(False, "Password is required")
        
        if len(password) < cls.MIN_LENGTH:
            return ValidationResult(False, f"Password must be at least {cls.MIN_LENGTH} characters")
        
        if len(password) > cls.MAX_LENGTH:
            return ValidationResult(False, f"Password must be less than {cls.MAX_LENGTH} characters")
        
        if require_special:
            if not re.search(r'[A-Z]', password):
                return ValidationResult(False, "Password must contain at least one uppercase letter")
            if not re.search(r'[a-z]', password):
                return ValidationResult(False, "Password must contain at least one lowercase letter")
            if not re.search(r'\d', password):
                return ValidationResult(False, "Password must contain at least one number")
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                return ValidationResult(False, "Password must contain at least one special character")
        
        return ValidationResult(True)


class NameValidator:
    """Name validation"""
    
    MIN_LENGTH = 1
    MAX_LENGTH = 100
    
    # Allow letters, spaces, hyphens, apostrophes
    NAME_REGEX = re.compile(r"^[\w\s\-'\.]+$", re.UNICODE)
    
    @classmethod
    def validate(cls, name: str) -> ValidationResult:
        """Validate name"""
        if not name:
            return ValidationResult(False, "Name is required")
        
        name = InputSanitizer.normalize_whitespace(name.strip())
        
        if len(name) < cls.MIN_LENGTH:
            return ValidationResult(False, f"Name must be at least {cls.MIN_LENGTH} character")
        
        if len(name) > cls.MAX_LENGTH:
            return ValidationResult(False, f"Name must be less than {cls.MAX_LENGTH} characters")
        
        # Sanitize for safety
        sanitized = InputSanitizer.sanitize_html(name)
        
        return ValidationResult(True, sanitized_value=sanitized)


class TradingAccountValidator:
    """Trading account input validation"""
    
    LOGIN_REGEX = re.compile(r'^\d{4,10}$')  # 4-10 digits
    SERVER_REGEX = re.compile(r'^[\w\-\.]+$')  # alphanumeric, hyphens, dots
    
    @classmethod
    def validate_login(cls, login: str) -> ValidationResult:
        """Validate trading account login/number"""
        if not login:
            return ValidationResult(False, "Account number is required")
        
        login = login.strip()
        
        if not cls.LOGIN_REGEX.match(login):
            return ValidationResult(False, "Account number must be 4-10 digits")
        
        return ValidationResult(True, sanitized_value=login)
    
    @classmethod
    def validate_server(cls, server: str) -> ValidationResult:
        """Validate broker server address"""
        if not server:
            return ValidationResult(False, "Server is required")
        
        server = server.strip()
        
        if len(server) > 100:
            return ValidationResult(False, "Server name too long")
        
        if not cls.SERVER_REGEX.match(server):
            return ValidationResult(False, "Invalid server format")
        
        return ValidationResult(True, sanitized_value=server)
    
    @classmethod
    def validate_risk_percent(cls, risk: float) -> ValidationResult:
        """Validate risk percentage"""
        if risk < 0.1:
            return ValidationResult(False, "Risk must be at least 0.1%")
        
        if risk > 100:
            return ValidationResult(False, "Risk cannot exceed 100%")
        
        # Warn for high risk
        if risk > 10:
            return ValidationResult(True, error="Warning: Risk above 10% is very aggressive")
        
        return ValidationResult(True)
    
    @classmethod
    def validate_broker(cls, broker: str) -> ValidationResult:
        """Validate broker type"""
        valid_brokers = ['mt4', 'mt5', 'ctrader', 'other']
        
        if not broker:
            return ValidationResult(False, "Broker type is required")
        
        broker = broker.lower().strip()
        
        if broker not in valid_brokers:
            return ValidationResult(False, f"Invalid broker type. Must be one of: {', '.join(valid_brokers)}")
        
        return ValidationResult(True, sanitized_value=broker)


class CurrencyPairValidator:
    """Currency pair validation"""
    
    PAIR_REGEX = re.compile(r'^[A-Z]{6}$')
    
    VALID_CURRENCIES = [
        'EUR', 'USD', 'GBP', 'JPY', 'CHF', 'AUD', 'NZD', 'CAD',
        'SEK', 'NOK', 'DKK', 'PLN', 'HUF', 'CZK', 'TRY', 'ZAR',
        'MXN', 'SGD', 'HKD', 'CNH', 'CNY', 'XAU', 'XAG'
    ]
    
    @classmethod
    def validate(cls, pair: str) -> ValidationResult:
        """Validate currency pair format"""
        if not pair:
            return ValidationResult(False, "Currency pair is required")
        
        pair = pair.upper().replace("/", "").replace("-", "").strip()
        
        if not cls.PAIR_REGEX.match(pair):
            return ValidationResult(False, "Invalid pair format. Use format like EURUSD")
        
        base = pair[:3]
        quote = pair[3:]
        
        if base not in cls.VALID_CURRENCIES:
            return ValidationResult(False, f"Unknown base currency: {base}")
        
        if quote not in cls.VALID_CURRENCIES:
            return ValidationResult(False, f"Unknown quote currency: {quote}")
        
        if base == quote:
            return ValidationResult(False, "Base and quote currency cannot be the same")
        
        return ValidationResult(True, sanitized_value=pair)


def validate_all(validations: List[Tuple[str, ValidationResult]]) -> Optional[str]:
    """
    Run multiple validations and return first error.
    
    Args:
        validations: List of (field_name, ValidationResult) tuples
        
    Returns:
        First error message or None if all valid
    """
    for field_name, result in validations:
        if not result.is_valid:
            return f"{field_name}: {result.error}"
    return None
