"""
Freqtrade Signal Sender for ads-anomaly-detection
================================================

This module provides the interface for the ads-anomaly-detection system
to send trading signals to the Freqtrade execution strategy.

Signal Types:
- random: Random testing signals
- test: Validation testing signals  
- anomaly: Production anomaly-based trading signals
"""

import redis
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Literal

logger = logging.getLogger(__name__)

SignalType = Literal["random", "test", "anomaly"]
ActionType = Literal["buy", "sell", "hold"]


class FreqtradeSignalSender:
    """Interface for sending trading signals to Freqtrade execution strategy"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 0):
        """Initialize Redis connection for signal transmission"""
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        
        # Test connection
        try:
            self.redis_client.ping()
            logger.info("✅ Connected to Redis for Freqtrade signal transmission")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    def send_trading_signal(self, 
                          pair: str,
                          action: ActionType,
                          signal_type: SignalType,
                          confidence: float = 1.0,
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a trading signal to Freqtrade execution strategy
        
        Args:
            pair: Trading pair (e.g., "BTC/USDT")
            action: Trading action ("buy", "sell", "hold")
            signal_type: Type of signal ("random", "test", "anomaly")
            confidence: Signal confidence (0.0-1.0)
            metadata: Additional signal metadata
            
        Returns:
            bool: True if signal sent successfully
        """
        try:
            signal = {
                "action": action,
                "pair": pair,
                "signal_type": signal_type,
                "confidence": confidence,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {}
            }
            
            # Send signal to Redis
            signal_key = f"freqtrade_signal:{pair}"
            self.redis_client.set(signal_key, json.dumps(signal), ex=60)  # Expire in 60 seconds
            
            logger.info(f"📡 Sent {signal_type} {action} signal for {pair} (confidence: {confidence})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send trading signal: {e}")
            return False
    
    def send_anomaly_signal(self,
                          pair: str,
                          action: ActionType,
                          anomaly_severity: str,
                          detector: str,
                          confidence: float,
                          affected_metrics: str,
                          reason: str) -> bool:
        """
        Send an anomaly-based trading signal
        
        Args:
            pair: Trading pair
            action: Trading action
            anomaly_severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
            detector: Detector that generated the anomaly
            confidence: Detection confidence
            affected_metrics: Affected system metrics
            reason: Anomaly reason/description
            
        Returns:
            bool: True if signal sent successfully
        """
        metadata = {
            "anomaly_severity": anomaly_severity,
            "detector": detector,
            "affected_metrics": affected_metrics,
            "reason": reason
        }
        
        return self.send_trading_signal(
            pair=pair,
            action=action,
            signal_type="anomaly",
            confidence=confidence,
            metadata=metadata
        )
    
    def send_test_signal(self, pair: str, action: ActionType, test_scenario: str) -> bool:
        """
        Send a test trading signal
        
        Args:
            pair: Trading pair
            action: Trading action
            test_scenario: Test scenario description
            
        Returns:
            bool: True if signal sent successfully
        """
        metadata = {
            "test_scenario": test_scenario,
            "test_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return self.send_trading_signal(
            pair=pair,
            action=action,
            signal_type="test",
            confidence=1.0,
            metadata=metadata
        )
    
    def send_random_signal(self, pair: str, action: ActionType) -> bool:
        """
        Send a random trading signal for testing
        
        Args:
            pair: Trading pair
            action: Trading action
            
        Returns:
            bool: True if signal sent successfully
        """
        import random
        
        metadata = {
            "random_seed": random.randint(1, 1000),
            "test_mode": True
        }
        
        return self.send_trading_signal(
            pair=pair,
            action=action,
            signal_type="random",
            confidence=random.uniform(0.5, 1.0),
            metadata=metadata
        )
    
    def set_custom_stoploss(self, pair: str, stoploss_percentage: float) -> bool:
        """
        Set custom stoploss for a trading pair
        
        Args:
            pair: Trading pair
            stoploss_percentage: Stoploss percentage (negative value, e.g., -0.05 for 5%)
            
        Returns:
            bool: True if stoploss set successfully
        """
        try:
            stoploss_key = f"freqtrade_stoploss:{pair}"
            self.redis_client.set(stoploss_key, str(stoploss_percentage), ex=3600)  # Expire in 1 hour
            
            logger.info(f"🛑 Set custom stoploss for {pair}: {stoploss_percentage}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set custom stoploss: {e}")
            return False
    
    def clear_signals(self, pair: Optional[str] = None) -> bool:
        """
        Clear pending signals
        
        Args:
            pair: Specific pair to clear, or None to clear all
            
        Returns:
            bool: True if signals cleared successfully
        """
        try:
            if pair:
                # Clear specific pair
                signal_key = f"freqtrade_signal:{pair}"
                self.redis_client.delete(signal_key)
                logger.info(f"🧹 Cleared signals for {pair}")
            else:
                # Clear all signals
                pattern = "freqtrade_signal:*"
                keys = self.redis_client.keys(pattern)
                if keys and isinstance(keys, list):
                    self.redis_client.delete(*keys)
                    logger.info(f"🧹 Cleared {len(keys)} pending signals")
                else:
                    logger.info("🧹 No pending signals to clear")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to clear signals: {e}")
            return False
    
    def get_signal_status(self) -> Dict[str, Any]:
        """
        Get status of pending signals
        
        Returns:
            dict: Signal status information
        """
        try:
            signal_keys = self.redis_client.keys("freqtrade_signal:*")
            stoploss_keys = self.redis_client.keys("freqtrade_stoploss:*")
            
            # Handle Redis response types
            signal_list = signal_keys if isinstance(signal_keys, list) else []
            stoploss_list = stoploss_keys if isinstance(stoploss_keys, list) else []
            
            status = {
                "pending_signals": len(signal_list),
                "active_stoplosses": len(stoploss_list),
                "signal_pairs": [key.split(":")[-1] for key in signal_list],
                "stoploss_pairs": [key.split(":")[-1] for key in stoploss_list],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Failed to get signal status: {e}")
            return {"error": str(e)}


# Integration with ads-anomaly-detection memory system
class AdsFreqtradeInterface:
    """Interface for ads-anomaly-detection system to control Freqtrade"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 0):
        self.signal_sender = FreqtradeSignalSender(redis_host, redis_port, redis_db)
        self.trading_pairs = [
            "BTC/USDT", "ETH/USDT", "ADA/USDT", "DOT/USDT", "SOL/USDT",
            "MATIC/USDT", "LINK/USDT", "AVAX/USDT", "UNI/USDT", "ATOM/USDT",
            "FTM/USDT", "ALGO/USDT", "XRP/USDT", "LTC/USDT", "BCH/USDT",
            "ETC/USDT", "XLM/USDT", "VET/USDT", "TRX/USDT", "DOGE/USDT"
        ]
    
    def process_anomaly_for_trading(self, anomaly_data: Dict[str, Any]) -> bool:
        """
        Process anomaly detection result and generate trading signal
        
        Args:
            anomaly_data: Anomaly data from ads-anomaly-detection system
            
        Returns:
            bool: True if trading signal generated successfully
        """
        try:
            # Extract anomaly information
            severity = anomaly_data.get('severity', 'MEDIUM')
            confidence = anomaly_data.get('confidence', 0.0)
            detector = anomaly_data.get('detector', 'unknown')
            affected_metrics = anomaly_data.get('affected_metrics', 'unknown')
            
            # Simple trading logic based on anomaly
            # This is where more sophisticated trading logic would go
            
            if severity in ['HIGH', 'CRITICAL'] and confidence > 0.8:
                # High severity anomaly - potential buy signal (system stress might indicate opportunity)
                action = "buy"
                pair = "BTC/USDT"  # Default to BTC for now
                
                success = self.signal_sender.send_anomaly_signal(
                    pair=pair,
                    action=action,
                    anomaly_severity=severity,
                    detector=detector,
                    confidence=confidence,
                    affected_metrics=affected_metrics,
                    reason=f"High severity anomaly detected by {detector}"
                )
                
                if success:
                    logger.info(f"🚨 Generated {action} signal for {pair} based on {severity} anomaly")
                
                return success
            
            return True  # No action needed for low severity anomalies
            
        except Exception as e:
            logger.error(f"❌ Failed to process anomaly for trading: {e}")
            return False
    
    def run_test_sequence(self) -> bool:
        """Run a test sequence of trading signals"""
        try:
            logger.info("🧪 Starting Freqtrade test sequence...")
            
            # Test 1: Random signals
            for pair in self.trading_pairs[:2]:  # Test with first 2 pairs
                self.signal_sender.send_random_signal(pair, "buy")
                logger.info(f"✅ Sent random buy signal for {pair}")
            
            # Test 2: Test signals
            self.signal_sender.send_test_signal("BTC/USDT", "sell", "test_exit_scenario")
            logger.info("✅ Sent test sell signal for BTC/USDT")
            
            # Test 3: Custom stoploss
            self.signal_sender.set_custom_stoploss("BTC/USDT", -0.03)  # 3% stoploss
            logger.info("✅ Set custom stoploss for BTC/USDT")
            
            # Check status
            status = self.signal_sender.get_signal_status()
            logger.info(f"📊 Signal status: {status}")
            
            logger.info("🎉 Test sequence completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Test sequence failed: {e}")
            return False
