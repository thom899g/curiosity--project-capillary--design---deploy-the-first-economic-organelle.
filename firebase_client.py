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