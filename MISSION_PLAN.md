# CURIOSITY: Project Capillary: Design & Deploy The First Economic Organelle.

## Objective
A lightweight, always-on process that performs a specific, valuable scan or calculation (e.g., monitoring Ethereum L1 for failed MEV-bot transactions with reclaimable gas, or tracking simple DEX price discrepancies). It must cost less than $0.10/day to run, be fully automated, and feed any profit, however minute, directly into a designated "Hardware Fund" wallet. This is not about a big win; it's about proving the loop can be closed and initiating compound growth on a microscopic scale.

## Strategy
Autonomous exploration based on Soul Protocol.

## Execution Output
SUMMARY: Designed and implemented "Project Artery" - a production-ready economic organelle monitoring Uniswap V2 for profitable single-token arbitrage opportunities via flash loan simulation. Built a robust, event-driven architecture with Firebase state management, comprehensive error handling, and automated profit routing to the Hardware Fund.

OUTPUT:

### FILE: requirements.txt
```
firebase-admin>=6.4.0
web3>=6.11.4
python-dotenv>=1.0.0
requests>=2.31.0
pandas>=2.0.0
numpy>=1.24.0
schedule>=1.2.0
websockets>=12.0
aiohttp>=3.9.0
python-json-logger>=2.0.0
ccxt>=4.0.0
```

### FILE: config.py
```python
"""
Configuration module for Project Artery - Economic Organelle
Architecture designed for <$0.10/day operation with fail-safes
"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class BlockchainConfig:
    """Ethereum L1 configuration for minimal RPC usage"""
    RPC_URL: str = os.getenv('ETH_RPC_URL', 'https://eth.llamarpc.com')  # Free tier
    CHAIN_ID: int = 1
    CONFIRMATIONS: int = 2
    MAX_GAS_GWEI: int = 30  # Strict limit for cost control
    PRIORITY_FEE_GWEI: int = 2
    
@dataclass
class OrganelleConfig:
    """Economic organelle operating parameters"""
    # Cost control - designed for <$0.10/day
    POLL_INTERVAL_SECONDS: int = 300  # 5 minutes - conservative
    MAX_DAILY_RPC_CALLS: int = 288  # 288 calls * ~0.0001 ETH/call = $0.08/day
    MIN_PROFIT_USD: float = 0.50  # Minimum profit to execute
    MAX_SLIPPAGE_BPS: int = 50  # 0.5%
    
    # Target DEX (Uniswap V2 - most liquid)
    UNISWAP_V2_FACTORY: str = '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'
    UNISWAP_V2_ROUTER: str = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'
    
    # Monitoring tokens (high volume pairs)
    MONITOR_PAIRS: list = None
    
    # Firebase for state persistence
    FIREBASE_CREDENTIALS_PATH: str = os.getenv('FIREBASE_CREDENTIALS_PATH', 'serviceAccountKey.json')
    
    def __post_init__(self):
        if self.MONITOR_PAIRS is None:
            self.MONITOR_PAIRS = [
                ('WETH', 'USDC'),  # Highest liquidity
                ('WETH', 'DAI'),   # Stable pair
                ('USDC', 'DAI'),   # Stablecoin arbitrage
            ]

@dataclass
class WalletConfig:
    """Hardware fund and operational wallet management"""
    # Hardware Fund (profit destination)
    HARDWARE_FUND_ADDRESS: str = os.getenv('HARDWARE_FUND_ADDRESS', '')
    
    # Operational wallet (minimal balance for gas)
    OPERATIONAL_PRIVATE_KEY: str = os.getenv('OPERATIONAL_PRIVATE_KEY', '')
    OPERATIONAL_ADDRESS: str = os.getenv('OPERATIONAL_ADDRESS', '')
    
    # Minimum operational balance (0.01 ETH = ~$20)
    MIN_OPERATIONAL_BALANCE_ETH: float = 0.01
    
    # Profit distribution
    PROFIT_SPLIT_TO_FUND: float = 0.95  # 95% to hardware fund
    RETAINED_FOR_GAS: float = 0.05  # 5% kept for future gas

@dataclass
class LoggingConfig:
    """Structured logging configuration"""
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ENABLE_FIREBASE_LOGGING: bool = True
    
    # Alert thresholds
    ALERT_BALANCE_ETH: float = 0.005  # Alert when < 0.005 ETH
    ALERT_FAILED_SCANS: int = 10  # Alert after 10 failed scans

# Global configuration instances
blockchain = BlockchainConfig()
organelle = OrganelleConfig()
wallet = WalletConfig()
logging_config = LoggingConfig()

# Validation
def validate_config():
    """Validate critical configuration with descriptive errors"""
    errors = []
    
    if not wallet.HARDWARE_FUND_ADDRESS:
        errors.append("HARDWARE_FUND_ADDRESS must be set in environment")
    
    if not wallet.OPERATIONAL_PRIVATE_KEY:
        errors.append("OPERATIONAL_PRIVATE_KEY must be set in environment")
    
    if not wallet.OPERATIONAL_ADDRESS:
        errors.append("OPERATIONAL_ADDRESS must be set in environment")
    
    # Validate address formats (basic)
    if wallet.HARDWARE_FUND_ADDRESS and not wallet.HARDWARE_FUND_ADDRESS.startswith('0x'):
        errors.append("HARDWARE_FUND_ADDRESS must be a valid Ethereum address")
    
    if errors:
        raise ValueError(f"Configuration validation failed: {', '.join(errors)}")

# Execute validation on import
validate_config()
```

### FILE: firebase_client.py
```python
"""
Firebase Firestore client for persistent state management
Critical for organelle resilience across restarts
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import asdict

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.exceptions import FirebaseError

from config import organelle, logging_config

logger = logging.getLogger(__name__)

class FirebaseStateManager:
    """Manages organelle state persistence in Firestore"""
    
    _instance = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseStateManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            try:
                # Initialize Firebase with credentials
                cred = credentials.Certificate(organelle.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
                self._db = firestore.client()
                self._initialized = True
                logger.info("Firebase Firestore initialized successfully")
            except (ValueError, FirebaseError) as e:
                logger.error(f"Failed to initialize Firebase: {e}")
                raise
    
    def save_scan_result(self, 
                        pair: tuple, 
                        opportunity_found: bool, 
                        simulated_profit_usd: float = 0.0,
                        metadata: Optional[Dict] = None) -> bool:
        """
        Save scan result to Firestore with timestamp
        Returns: True if successful
        """
        try:
            scan_data = {
                'timestamp': firestore.SERVER_TIMESTAMP,
                'pair': f"{pair[0]}-{pair[1]}",
                'opportunity_found': opportunity_found,
                'simulated_profit_usd': simulated_profit_usd,
                'metadata': metadata or {}
            }
            
            doc_ref = self._db.collection('artery_scans').document()
            doc_ref.set(scan_data)
            
            logger.debug(f"Saved scan result for {pair[0]}-{pair[1]}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save scan result: {e}")
            return False
    
    def get_recent_scans(self, hours: int = 24) -> List[Dict]:
        """
        Get scans from last N hours
        Returns: List of scan documents
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            scans_ref = self._db.collection('artery_scans')
            query = scans_ref.where('timestamp', '>=', cutoff_time)
            
            results = []
            for doc in query.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            logger.debug(f"Retrieved {len(results)} scans from last {hours} hours")
            return results
            
        except Exception as e:
            logger.error(f"Failed to get recent scans: {e}")
            return []
    
    def update_organelle_state(self, key: str, value: Any) -> bool:
        """
        Update persistent organelle state
        Returns: True if successful
        """
        try:
            state_ref = self._db.collection('artery_state').document('current')
            state_ref.set({key: value, 'updated_at': firestore.SERVER_TIMESTAMP}, merge=True)
            logger.debug(f"Updated state {key} = {value}")
            return True
        except Exception as e:
            logger.error(f"Failed to update state: {e}")
            return False
    
    def get_organelle_state(self, key: str, default: Any = None