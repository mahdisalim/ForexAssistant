"""
Secure Encryption Service
Handles encryption and decryption of sensitive data.
Uses Fernet symmetric encryption when available, falls back to XOR for development.
"""

import os
import base64
import hashlib
import secrets
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import cryptography library for production-grade encryption
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    logger.warning("cryptography library not installed. Using fallback encryption.")


class EncryptionService:
    """
    Secure encryption service for storing sensitive data.
    Uses Fernet (AES-128-CBC) when cryptography library is available.
    Falls back to XOR encryption for development environments.
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize encryption service.
        
        Args:
            secret_key: Secret key for encryption. If not provided, uses ENCRYPTION_KEY env var.
        """
        self.secret_key = secret_key or os.getenv(
            "ENCRYPTION_KEY", 
            "default-dev-key-change-in-production-" + secrets.token_hex(16)
        )
        
        if CRYPTOGRAPHY_AVAILABLE:
            self._init_fernet()
        else:
            self._fernet = None
    
    def _init_fernet(self):
        """Initialize Fernet encryption with derived key"""
        try:
            # Derive a proper key from the secret
            salt = hashlib.sha256(b"forex-assistant-salt").digest()[:16]
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.secret_key.encode()))
            self._fernet = Fernet(key)
        except Exception as e:
            logger.error(f"Failed to initialize Fernet: {e}")
            self._fernet = None
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: Plain text data to encrypt
            
        Returns:
            Encrypted data as string
        """
        if not data:
            return ""
        
        if self._fernet:
            return self._encrypt_fernet(data)
        else:
            return self._encrypt_xor(data)
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted data.
        
        Args:
            encrypted_data: Encrypted data string
            
        Returns:
            Decrypted plain text
        """
        if not encrypted_data:
            return ""
        
        # Detect encryption method by prefix
        if encrypted_data.startswith("fernet:"):
            return self._decrypt_fernet(encrypted_data[7:])
        elif encrypted_data.startswith("xor:"):
            return self._decrypt_xor(encrypted_data[4:])
        elif ":" in encrypted_data:
            # Legacy format
            _, data = encrypted_data.split(":", 1)
            return self._decrypt_xor(data)
        else:
            # Try Fernet first, then XOR
            if self._fernet:
                try:
                    return self._decrypt_fernet(encrypted_data)
                except:
                    pass
            return self._decrypt_xor(encrypted_data)
    
    def _encrypt_fernet(self, data: str) -> str:
        """Encrypt using Fernet (AES)"""
        try:
            encrypted = self._fernet.encrypt(data.encode())
            return "fernet:" + encrypted.decode()
        except Exception as e:
            logger.error(f"Fernet encryption failed: {e}")
            return self._encrypt_xor(data)
    
    def _decrypt_fernet(self, encrypted_data: str) -> str:
        """Decrypt using Fernet (AES)"""
        try:
            decrypted = self._fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Fernet decryption failed: {e}")
            raise ValueError("Failed to decrypt data")
    
    def _encrypt_xor(self, data: str) -> str:
        """
        Encrypt using XOR (fallback for development).
        NOT recommended for production use.
        """
        key = self.secret_key
        encrypted = []
        for i, char in enumerate(data):
            encrypted.append(chr(ord(char) ^ ord(key[i % len(key)])))
        
        # Add integrity hash
        integrity = hashlib.sha256(data.encode()).hexdigest()[:8]
        encoded = ''.join(encrypted).encode('unicode_escape').decode('ascii')
        
        return f"xor:{integrity}:{encoded}"
    
    def _decrypt_xor(self, encrypted_data: str) -> str:
        """Decrypt XOR encrypted data"""
        try:
            # Check for integrity hash
            if encrypted_data.count(":") >= 1:
                parts = encrypted_data.split(":", 1)
                if len(parts[0]) == 8:  # Integrity hash
                    integrity_hash = parts[0]
                    encoded_data = parts[1]
                else:
                    integrity_hash = None
                    encoded_data = encrypted_data
            else:
                integrity_hash = None
                encoded_data = encrypted_data
            
            # Decode and decrypt
            data = encoded_data.encode('ascii').decode('unicode_escape')
            key = self.secret_key
            decrypted = []
            for i, char in enumerate(data):
                decrypted.append(chr(ord(char) ^ ord(key[i % len(key)])))
            
            result = ''.join(decrypted)
            
            # Verify integrity if hash present
            if integrity_hash:
                expected_hash = hashlib.sha256(result.encode()).hexdigest()[:8]
                if expected_hash != integrity_hash:
                    logger.warning("Data integrity check failed")
            
            return result
            
        except Exception as e:
            logger.error(f"XOR decryption failed: {e}")
            raise ValueError("Failed to decrypt data")
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new random encryption key"""
        return secrets.token_urlsafe(32)
    
    def is_using_strong_encryption(self) -> bool:
        """Check if strong encryption (Fernet) is being used"""
        return self._fernet is not None


# Global instance for convenience
_default_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get or create the default encryption service instance"""
    global _default_encryption_service
    if _default_encryption_service is None:
        _default_encryption_service = EncryptionService()
    return _default_encryption_service
