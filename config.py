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