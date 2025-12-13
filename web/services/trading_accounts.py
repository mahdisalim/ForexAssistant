"""
Secure Trading Accounts Service
Handles connection to MT4/MT5/cTrader brokers and account management.
All sensitive operations are performed server-side for security.
"""

import os
import json
import hashlib
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrokerType(str, Enum):
    MT4 = "mt4"
    MT5 = "mt5"
    CTRADER = "ctrader"
    OTHER = "other"


class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"


@dataclass
class AccountInfo:
    """Trading account information retrieved from broker"""
    account_id: str
    broker: str
    login: str
    server: str
    balance: float
    equity: float
    margin: float
    free_margin: float
    leverage: int
    currency: str
    name: str
    company: str
    connected: bool
    last_updated: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TradingAccount:
    """Stored trading account configuration"""
    id: str
    user_id: str
    broker: BrokerType
    login: str
    server: str
    risk_percent: float
    nickname: str
    created_at: str
    last_connected: Optional[str] = None
    encrypted_password: Optional[str] = None
    
    def to_safe_dict(self) -> Dict[str, Any]:
        """Return dict without sensitive data"""
        return {
            "id": self.id,
            "broker": self.broker,
            "login": self.login,
            "server": self.server,
            "risk_percent": self.risk_percent,
            "nickname": self.nickname,
            "created_at": self.created_at,
            "last_connected": self.last_connected
        }


# Import the improved encryption service
from .encryption import EncryptionService


class MetaTraderConnector:
    """Connector for MetaTrader 4/5 accounts"""
    
    def __init__(self):
        self.api_token = os.getenv("METAAPI_TOKEN")
        self._connections: Dict[str, Any] = {}
    
    async def connect(self, login: str, password: str, server: str, broker_type: BrokerType) -> Dict[str, Any]:
        """Connect to MT4/MT5 account and retrieve account information"""
        logger.info(f"Attempting to connect to {broker_type.value} account {login} on {server}")
        
        if self.api_token:
            return await self._connect_via_metaapi(login, password, server, broker_type)
        else:
            logger.warning("MetaApi token not configured. Using simulation mode.")
            return await self._simulate_connection(login, password, server, broker_type)
    
    async def _connect_via_metaapi(self, login: str, password: str, server: str, broker_type: BrokerType) -> Dict[str, Any]:
        """Connect using MetaApi Cloud service"""
        try:
            from metaapi_cloud_sdk import MetaApi
            
            api = MetaApi(self.api_token)
            
            account = await api.metatrader_account_api.create_account({
                'name': f'Account {login}',
                'type': 'cloud',
                'login': login,
                'password': password,
                'server': server,
                'platform': 'mt5' if broker_type == BrokerType.MT5 else 'mt4',
                'magic': 0
            })
            
            await account.deploy()
            await account.wait_connected()
            
            connection = account.get_rpc_connection()
            await connection.connect()
            await connection.wait_synchronized()
            
            account_info = await connection.get_account_information()
            
            return {
                "success": True,
                "account_info": AccountInfo(
                    account_id=account.id,
                    broker=broker_type.value,
                    login=login,
                    server=server,
                    balance=account_info.get('balance', 0),
                    equity=account_info.get('equity', 0),
                    margin=account_info.get('margin', 0),
                    free_margin=account_info.get('freeMargin', 0),
                    leverage=account_info.get('leverage', 100),
                    currency=account_info.get('currency', 'USD'),
                    name=account_info.get('name', ''),
                    company=account_info.get('broker', ''),
                    connected=True,
                    last_updated=datetime.utcnow().isoformat()
                ).to_dict()
            }
            
        except ImportError:
            logger.error("MetaApi SDK not installed. Install with: pip install metaapi-cloud-sdk")
            return await self._simulate_connection(login, password, server, broker_type)
        except Exception as e:
            logger.error(f"MetaApi connection error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _simulate_connection(self, login: str, password: str, server: str, broker_type: BrokerType) -> Dict[str, Any]:
        """Simulate connection for development/testing"""
        await asyncio.sleep(1)
        
        if not login or not password or not server:
            return {"success": False, "error": "Invalid credentials. Please check login, password, and server."}
        
        import random
        
        mock_balance = round(random.uniform(1000, 50000), 2)
        mock_equity = round(mock_balance * random.uniform(0.95, 1.05), 2)
        mock_margin = round(mock_balance * random.uniform(0.01, 0.1), 2)
        
        return {
            "success": True,
            "account_info": AccountInfo(
                account_id=f"sim_{login}_{server}",
                broker=broker_type.value,
                login=login,
                server=server,
                balance=mock_balance,
                equity=mock_equity,
                margin=mock_margin,
                free_margin=round(mock_equity - mock_margin, 2),
                leverage=100,
                currency="USD",
                name=f"Demo Account {login}",
                company=server.split("-")[0] if "-" in server else server,
                connected=True,
                last_updated=datetime.utcnow().isoformat()
            ).to_dict()
        }
    
    async def disconnect(self, account_id: str) -> bool:
        """Disconnect from trading account"""
        if account_id in self._connections:
            del self._connections[account_id]
        return True


class TradingAccountsService:
    """Main service for managing trading accounts"""
    
    def __init__(self, db_path: str = "data/trading_accounts.json"):
        self.db_path = db_path
        self.encryption = EncryptionService()
        self.mt_connector = MetaTraderConnector()
        self._accounts: Dict[str, List[TradingAccount]] = {}
        self._account_info_cache: Dict[str, AccountInfo] = {}
        self._ensure_db_exists()
        self._load_accounts()
    
    def _ensure_db_exists(self):
        """Ensure database directory and file exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w') as f:
                json.dump({}, f)
    
    def _load_accounts(self):
        """Load accounts from database"""
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                for user_id, accounts in data.items():
                    self._accounts[user_id] = [TradingAccount(**acc) for acc in accounts]
        except Exception as e:
            logger.error(f"Error loading accounts: {e}")
            self._accounts = {}
    
    def _save_accounts(self):
        """Save accounts to database"""
        try:
            data = {}
            for user_id, accounts in self._accounts.items():
                data[user_id] = [
                    {
                        "id": acc.id,
                        "user_id": acc.user_id,
                        "broker": acc.broker.value if isinstance(acc.broker, BrokerType) else acc.broker,
                        "login": acc.login,
                        "server": acc.server,
                        "risk_percent": acc.risk_percent,
                        "nickname": acc.nickname,
                        "created_at": acc.created_at,
                        "last_connected": acc.last_connected,
                        "encrypted_password": acc.encrypted_password
                    }
                    for acc in accounts
                ]
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving accounts: {e}")
    
    async def add_account(
        self,
        user_id: str,
        broker: str,
        login: str,
        password: str,
        server: str,
        risk_percent: float,
        nickname: str
    ) -> Dict[str, Any]:
        """Add a new trading account and attempt to connect"""
        try:
            broker_type = BrokerType(broker.lower())
        except ValueError:
            broker_type = BrokerType.OTHER
        
        connection_result = await self.mt_connector.connect(
            login=login,
            password=password,
            server=server,
            broker_type=broker_type
        )
        
        if not connection_result.get("success"):
            return {"success": False, "error": connection_result.get("error", "Failed to connect to trading account")}
        
        account_id = hashlib.md5(f"{user_id}:{login}:{server}".encode()).hexdigest()
        
        account = TradingAccount(
            id=account_id,
            user_id=user_id,
            broker=broker_type,
            login=login,
            server=server,
            risk_percent=risk_percent,
            nickname=nickname or f"Account {login}",
            created_at=datetime.utcnow().isoformat(),
            last_connected=datetime.utcnow().isoformat(),
            encrypted_password=self.encryption.encrypt(password)
        )
        
        if user_id not in self._accounts:
            self._accounts[user_id] = []
        
        existing = next((a for a in self._accounts[user_id] if a.login == login and a.server == server), None)
        if existing:
            return {"success": False, "error": "This account is already added"}
        
        self._accounts[user_id].append(account)
        self._save_accounts()
        
        account_info = connection_result.get("account_info", {})
        self._account_info_cache[account_id] = account_info
        
        return {"success": True, "account": account.to_safe_dict(), "account_info": account_info}
    
    async def get_user_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all accounts for a user with their current info"""
        accounts = self._accounts.get(user_id, [])
        result = []
        
        for account in accounts:
            account_data = account.to_safe_dict()
            if account.id in self._account_info_cache:
                account_data["account_info"] = self._account_info_cache[account.id]
            result.append(account_data)
        
        return result
    
    async def refresh_account(self, user_id: str, account_id: str) -> Dict[str, Any]:
        """Refresh account information by reconnecting"""
        accounts = self._accounts.get(user_id, [])
        account = next((a for a in accounts if a.id == account_id), None)
        
        if not account:
            return {"success": False, "error": "Account not found"}
        
        password = self.encryption.decrypt(account.encrypted_password)
        broker_type = BrokerType(account.broker) if isinstance(account.broker, str) else account.broker
        
        connection_result = await self.mt_connector.connect(
            login=account.login,
            password=password,
            server=account.server,
            broker_type=broker_type
        )
        
        if connection_result.get("success"):
            account.last_connected = datetime.utcnow().isoformat()
            self._save_accounts()
            self._account_info_cache[account_id] = connection_result.get("account_info", {})
        
        return connection_result
    
    async def delete_account(self, user_id: str, account_id: str) -> Dict[str, Any]:
        """Delete a trading account"""
        if user_id not in self._accounts:
            return {"success": False, "error": "User not found"}
        
        original_count = len(self._accounts[user_id])
        self._accounts[user_id] = [a for a in self._accounts[user_id] if a.id != account_id]
        
        if len(self._accounts[user_id]) < original_count:
            self._save_accounts()
            if account_id in self._account_info_cache:
                del self._account_info_cache[account_id]
            return {"success": True}
        
        return {"success": False, "error": "Account not found"}
    
    async def update_risk(self, user_id: str, account_id: str, risk_percent: float) -> Dict[str, Any]:
        """Update risk percentage for an account"""
        accounts = self._accounts.get(user_id, [])
        account = next((a for a in accounts if a.id == account_id), None)
        
        if not account:
            return {"success": False, "error": "Account not found"}
        
        account.risk_percent = risk_percent
        self._save_accounts()
        
        return {"success": True, "account": account.to_safe_dict()}


# Global service instance
trading_accounts_service = TradingAccountsService()
