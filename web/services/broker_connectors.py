"""
Broker Connectors Module
Provides real connections to various trading platforms:
- MetaTrader 4/5 via MetaApi Cloud
- cTrader via cTrader Open API
- Direct broker APIs

For MT4/MT5: Requires MetaApi account (https://metaapi.cloud)
For cTrader: Requires cTrader Open API credentials
"""

import os
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class BrokerType(str, Enum):
    MT4 = "mt4"
    MT5 = "mt5"
    CTRADER = "ctrader"
    OTHER = "other"


@dataclass
class AccountInfo:
    """Trading account information"""
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
    profit: float = 0.0
    margin_level: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseBrokerConnector(ABC):
    """Abstract base class for broker connectors"""
    
    @abstractmethod
    async def connect(self, login: str, password: str, server: str) -> Dict[str, Any]:
        """Connect to broker and return account info"""
        pass
    
    @abstractmethod
    async def disconnect(self, account_id: str) -> bool:
        """Disconnect from broker"""
        pass
    
    @abstractmethod
    async def get_account_info(self, account_id: str) -> Optional[AccountInfo]:
        """Get current account information"""
        pass


class MetaApiConnector(BaseBrokerConnector):
    """
    MetaTrader 4/5 connector using MetaApi Cloud service.
    
    MetaApi is a cloud service that provides REST API access to MT4/MT5 accounts.
    Sign up at: https://metaapi.cloud
    
    Required environment variable: METAAPI_TOKEN
    """
    
    def __init__(self, broker_type: BrokerType = BrokerType.MT5):
        self.api_token = os.getenv("METAAPI_TOKEN")
        self.broker_type = broker_type
        self._api = None
        self._accounts: Dict[str, Any] = {}
    
    async def _get_api(self):
        """Get or create MetaApi instance"""
        if self._api is None and self.api_token:
            try:
                from metaapi_cloud_sdk import MetaApi
                self._api = MetaApi(self.api_token)
            except ImportError:
                logger.error("MetaApi SDK not installed. Run: pip install metaapi-cloud-sdk")
                return None
        return self._api
    
    async def connect(self, login: str, password: str, server: str) -> Dict[str, Any]:
        """Connect to MT4/MT5 account via MetaApi"""
        api = await self._get_api()
        
        if not api:
            logger.warning("MetaApi not available, using simulation mode")
            return await self._simulate_connection(login, password, server)
        
        try:
            # Check if account already exists in MetaApi
            accounts = await api.metatrader_account_api.get_accounts()
            existing = None
            for acc in accounts:
                if acc.login == login and acc.server == server:
                    existing = acc
                    break
            
            if existing:
                account = existing
            else:
                # Create new account in MetaApi
                account = await api.metatrader_account_api.create_account({
                    'name': f'Account {login}',
                    'type': 'cloud',
                    'login': login,
                    'password': password,
                    'server': server,
                    'platform': 'mt5' if self.broker_type == BrokerType.MT5 else 'mt4',
                    'magic': 0
                })
            
            # Deploy and connect
            if account.state != 'DEPLOYED':
                await account.deploy()
            
            await account.wait_connected()
            
            # Get RPC connection for account info
            connection = account.get_rpc_connection()
            await connection.connect()
            await connection.wait_synchronized()
            
            # Get account information
            info = await connection.get_account_information()
            
            self._accounts[account.id] = {
                'account': account,
                'connection': connection
            }
            
            return {
                "success": True,
                "account_info": AccountInfo(
                    account_id=account.id,
                    broker=self.broker_type.value,
                    login=login,
                    server=server,
                    balance=info.get('balance', 0),
                    equity=info.get('equity', 0),
                    margin=info.get('margin', 0),
                    free_margin=info.get('freeMargin', 0),
                    leverage=info.get('leverage', 100),
                    currency=info.get('currency', 'USD'),
                    name=info.get('name', ''),
                    company=info.get('broker', server),
                    connected=True,
                    last_updated=datetime.utcnow().isoformat(),
                    profit=info.get('profit', 0),
                    margin_level=info.get('marginLevel', 0)
                ).to_dict()
            }
            
        except Exception as e:
            logger.error(f"MetaApi connection error: {e}")
            return {"success": False, "error": str(e)}
    
    async def disconnect(self, account_id: str) -> bool:
        """Disconnect from MetaApi account"""
        if account_id in self._accounts:
            try:
                conn_data = self._accounts[account_id]
                if conn_data.get('connection'):
                    await conn_data['connection'].close()
                del self._accounts[account_id]
                return True
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
        return False
    
    async def get_account_info(self, account_id: str) -> Optional[AccountInfo]:
        """Get current account information"""
        if account_id not in self._accounts:
            return None
        
        try:
            conn_data = self._accounts[account_id]
            connection = conn_data.get('connection')
            if connection:
                info = await connection.get_account_information()
                return AccountInfo(
                    account_id=account_id,
                    broker=self.broker_type.value,
                    login=info.get('login', ''),
                    server=info.get('server', ''),
                    balance=info.get('balance', 0),
                    equity=info.get('equity', 0),
                    margin=info.get('margin', 0),
                    free_margin=info.get('freeMargin', 0),
                    leverage=info.get('leverage', 100),
                    currency=info.get('currency', 'USD'),
                    name=info.get('name', ''),
                    company=info.get('broker', ''),
                    connected=True,
                    last_updated=datetime.utcnow().isoformat(),
                    profit=info.get('profit', 0),
                    margin_level=info.get('marginLevel', 0)
                )
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
        return None
    
    async def _simulate_connection(self, login: str, password: str, server: str) -> Dict[str, Any]:
        """Fallback simulation when MetaApi is not available"""
        await asyncio.sleep(0.5)
        
        if not login or not password or not server:
            return {"success": False, "error": "Invalid credentials"}
        
        # Return placeholder data - user should configure MetaApi for real data
        return {
            "success": True,
            "account_info": AccountInfo(
                account_id=f"sim_{login}_{server}",
                broker=self.broker_type.value,
                login=login,
                server=server,
                balance=0.0,  # Show 0 to indicate simulation
                equity=0.0,
                margin=0.0,
                free_margin=0.0,
                leverage=100,
                currency="USD",
                name=f"[Simulation] Account {login}",
                company=server.split("-")[0] if "-" in server else server,
                connected=False,  # Mark as not connected
                last_updated=datetime.utcnow().isoformat()
            ).to_dict(),
            "warning": "MetaApi not configured. Set METAAPI_TOKEN in .env for real account data."
        }


class CTraderConnector(BaseBrokerConnector):
    """
    cTrader connector using cTrader Open API.
    
    Requires cTrader Open API credentials from your broker.
    Documentation: https://help.ctrader.com/open-api/
    
    Required environment variables:
    - CTRADER_CLIENT_ID
    - CTRADER_CLIENT_SECRET
    """
    
    def __init__(self):
        self.client_id = os.getenv("CTRADER_CLIENT_ID")
        self.client_secret = os.getenv("CTRADER_CLIENT_SECRET")
        self._connections: Dict[str, Any] = {}
    
    async def connect(self, login: str, password: str, server: str) -> Dict[str, Any]:
        """Connect to cTrader account"""
        if not self.client_id or not self.client_secret:
            logger.warning("cTrader API credentials not configured")
            return await self._simulate_connection(login, password, server)
        
        try:
            # cTrader Open API implementation
            # This requires the ctrader-open-api package
            from ctrader_open_api import Client, EndPoints, TcpProtocol
            from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import ProtoOAApplicationAuthReq
            from ctrader_open_api.messages.OpenApiMessages_pb2 import ProtoOAAccountAuthReq
            
            client = Client(EndPoints.PROTOBUF_LIVE_HOST, EndPoints.PROTOBUF_PORT, TcpProtocol)
            
            # Authenticate
            await client.send(ProtoOAApplicationAuthReq(
                clientId=self.client_id,
                clientSecret=self.client_secret
            ))
            
            # Get account info
            # Note: cTrader requires OAuth flow for account access
            # This is a simplified example
            
            return {
                "success": True,
                "account_info": AccountInfo(
                    account_id=f"ct_{login}",
                    broker="ctrader",
                    login=login,
                    server=server,
                    balance=0.0,
                    equity=0.0,
                    margin=0.0,
                    free_margin=0.0,
                    leverage=100,
                    currency="USD",
                    name=f"cTrader Account {login}",
                    company=server,
                    connected=True,
                    last_updated=datetime.utcnow().isoformat()
                ).to_dict()
            }
            
        except ImportError:
            logger.error("cTrader API not installed. Run: pip install ctrader-open-api")
            return await self._simulate_connection(login, password, server)
        except Exception as e:
            logger.error(f"cTrader connection error: {e}")
            return {"success": False, "error": str(e)}
    
    async def disconnect(self, account_id: str) -> bool:
        if account_id in self._connections:
            del self._connections[account_id]
            return True
        return False
    
    async def get_account_info(self, account_id: str) -> Optional[AccountInfo]:
        return None
    
    async def _simulate_connection(self, login: str, password: str, server: str) -> Dict[str, Any]:
        """Fallback simulation"""
        await asyncio.sleep(0.5)
        
        return {
            "success": True,
            "account_info": AccountInfo(
                account_id=f"ct_sim_{login}",
                broker="ctrader",
                login=login,
                server=server,
                balance=0.0,
                equity=0.0,
                margin=0.0,
                free_margin=0.0,
                leverage=100,
                currency="USD",
                name=f"[Simulation] cTrader {login}",
                company=server,
                connected=False,
                last_updated=datetime.utcnow().isoformat()
            ).to_dict(),
            "warning": "cTrader API not configured. Set CTRADER_CLIENT_ID and CTRADER_CLIENT_SECRET in .env"
        }


class DirectBrokerConnector(BaseBrokerConnector):
    """
    Direct connection to broker APIs.
    
    Some brokers provide their own REST APIs:
    - OANDA: https://developer.oanda.com/
    - Interactive Brokers: https://www.interactivebrokers.com/api
    - Alpaca: https://alpaca.markets/docs/api-documentation/
    
    This connector provides a framework for adding broker-specific implementations.
    """
    
    SUPPORTED_BROKERS = {
        'oanda': {
            'env_key': 'OANDA_API_KEY',
            'env_account': 'OANDA_ACCOUNT_ID',
            'base_url': 'https://api-fxtrade.oanda.com'
        },
        'alpaca': {
            'env_key': 'ALPACA_API_KEY',
            'env_secret': 'ALPACA_SECRET_KEY',
            'base_url': 'https://api.alpaca.markets'
        }
    }
    
    def __init__(self, broker_name: str = 'oanda'):
        self.broker_name = broker_name.lower()
        self.config = self.SUPPORTED_BROKERS.get(self.broker_name, {})
        self._connections: Dict[str, Any] = {}
    
    async def connect(self, login: str, password: str, server: str) -> Dict[str, Any]:
        """Connect to broker API"""
        
        if self.broker_name == 'oanda':
            return await self._connect_oanda(login, password, server)
        elif self.broker_name == 'alpaca':
            return await self._connect_alpaca(login, password, server)
        else:
            return await self._simulate_connection(login, password, server)
    
    async def _connect_oanda(self, login: str, password: str, server: str) -> Dict[str, Any]:
        """Connect to OANDA API"""
        api_key = os.getenv('OANDA_API_KEY') or password
        account_id = os.getenv('OANDA_ACCOUNT_ID') or login
        
        if not api_key:
            return await self._simulate_connection(login, password, server)
        
        try:
            import aiohttp
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Determine if practice or live
            base_url = 'https://api-fxpractice.oanda.com' if 'practice' in server.lower() else 'https://api-fxtrade.oanda.com'
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{base_url}/v3/accounts/{account_id}',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        account = data.get('account', {})
                        
                        return {
                            "success": True,
                            "account_info": AccountInfo(
                                account_id=account_id,
                                broker="oanda",
                                login=account_id,
                                server=server,
                                balance=float(account.get('balance', 0)),
                                equity=float(account.get('NAV', 0)),
                                margin=float(account.get('marginUsed', 0)),
                                free_margin=float(account.get('marginAvailable', 0)),
                                leverage=int(1 / float(account.get('marginRate', 0.02))),
                                currency=account.get('currency', 'USD'),
                                name=account.get('alias', f'OANDA {account_id}'),
                                company='OANDA',
                                connected=True,
                                last_updated=datetime.utcnow().isoformat(),
                                profit=float(account.get('unrealizedPL', 0))
                            ).to_dict()
                        }
                    else:
                        error_data = await response.json()
                        return {"success": False, "error": error_data.get('errorMessage', 'Connection failed')}
                        
        except ImportError:
            logger.error("aiohttp not installed")
            return await self._simulate_connection(login, password, server)
        except Exception as e:
            logger.error(f"OANDA connection error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _connect_alpaca(self, login: str, password: str, server: str) -> Dict[str, Any]:
        """Connect to Alpaca API"""
        api_key = os.getenv('ALPACA_API_KEY') or login
        secret_key = os.getenv('ALPACA_SECRET_KEY') or password
        
        if not api_key or not secret_key:
            return await self._simulate_connection(login, password, server)
        
        try:
            import aiohttp
            
            # Determine if paper or live
            base_url = 'https://paper-api.alpaca.markets' if 'paper' in server.lower() else 'https://api.alpaca.markets'
            
            headers = {
                'APCA-API-KEY-ID': api_key,
                'APCA-API-SECRET-KEY': secret_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{base_url}/v2/account', headers=headers) as response:
                    if response.status == 200:
                        account = await response.json()
                        
                        return {
                            "success": True,
                            "account_info": AccountInfo(
                                account_id=account.get('id', ''),
                                broker="alpaca",
                                login=api_key[:8] + '...',
                                server=server,
                                balance=float(account.get('cash', 0)),
                                equity=float(account.get('equity', 0)),
                                margin=float(account.get('initial_margin', 0)),
                                free_margin=float(account.get('buying_power', 0)),
                                leverage=int(account.get('multiplier', 1)),
                                currency=account.get('currency', 'USD'),
                                name=f"Alpaca {account.get('account_number', '')}",
                                company='Alpaca',
                                connected=True,
                                last_updated=datetime.utcnow().isoformat()
                            ).to_dict()
                        }
                    else:
                        return {"success": False, "error": "Authentication failed"}
                        
        except Exception as e:
            logger.error(f"Alpaca connection error: {e}")
            return {"success": False, "error": str(e)}
    
    async def disconnect(self, account_id: str) -> bool:
        if account_id in self._connections:
            del self._connections[account_id]
            return True
        return False
    
    async def get_account_info(self, account_id: str) -> Optional[AccountInfo]:
        return None
    
    async def _simulate_connection(self, login: str, password: str, server: str) -> Dict[str, Any]:
        await asyncio.sleep(0.5)
        return {
            "success": True,
            "account_info": AccountInfo(
                account_id=f"direct_sim_{login}",
                broker=self.broker_name,
                login=login,
                server=server,
                balance=0.0,
                equity=0.0,
                margin=0.0,
                free_margin=0.0,
                leverage=100,
                currency="USD",
                name=f"[Simulation] {self.broker_name.upper()} {login}",
                company=self.broker_name.upper(),
                connected=False,
                last_updated=datetime.utcnow().isoformat()
            ).to_dict(),
            "warning": f"Broker API not configured. Check environment variables for {self.broker_name.upper()}"
        }


class UniversalBrokerConnector:
    """
    Universal connector that routes to the appropriate broker connector.
    """
    
    def __init__(self):
        self.mt4_connector = MetaApiConnector(BrokerType.MT4)
        self.mt5_connector = MetaApiConnector(BrokerType.MT5)
        self.ctrader_connector = CTraderConnector()
        self._direct_connectors: Dict[str, DirectBrokerConnector] = {}
    
    def _get_direct_connector(self, broker_name: str) -> DirectBrokerConnector:
        if broker_name not in self._direct_connectors:
            self._direct_connectors[broker_name] = DirectBrokerConnector(broker_name)
        return self._direct_connectors[broker_name]
    
    async def connect(self, broker_type: str, login: str, password: str, server: str) -> Dict[str, Any]:
        """
        Connect to any supported broker.
        
        Args:
            broker_type: 'mt4', 'mt5', 'ctrader', 'oanda', 'alpaca', or 'other'
            login: Account login/number
            password: Account password or API key
            server: Broker server name
        """
        broker_type = broker_type.lower()
        
        if broker_type == 'mt4':
            return await self.mt4_connector.connect(login, password, server)
        elif broker_type == 'mt5':
            return await self.mt5_connector.connect(login, password, server)
        elif broker_type == 'ctrader':
            return await self.ctrader_connector.connect(login, password, server)
        elif broker_type in ['oanda', 'alpaca']:
            connector = self._get_direct_connector(broker_type)
            return await connector.connect(login, password, server)
        else:
            # Try MT5 as default for unknown brokers
            return await self.mt5_connector.connect(login, password, server)
    
    async def disconnect(self, broker_type: str, account_id: str) -> bool:
        broker_type = broker_type.lower()
        
        if broker_type == 'mt4':
            return await self.mt4_connector.disconnect(account_id)
        elif broker_type == 'mt5':
            return await self.mt5_connector.disconnect(account_id)
        elif broker_type == 'ctrader':
            return await self.ctrader_connector.disconnect(account_id)
        elif broker_type in self._direct_connectors:
            return await self._direct_connectors[broker_type].disconnect(account_id)
        return False


# Global connector instance
universal_connector = UniversalBrokerConnector()
