"""
Test Script for Freqtrade Execution Plugin
==========================================

This script demonstrates how to:
1. Send trading signals from ads-anomaly-detection to Freqtrade
2. Test the execution pipeline
3. Validate the integration

Run this BEFORE starting Freqtrade to send test signals
"""

import sys
import logging
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from signal_sender import FreqtradeSignalSender, AdsFreqtradeInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_signal_transmission():
    """Test basic signal transmission to Freqtrade"""
    print("🧪 Testing Freqtrade Signal Transmission")
    print("=" * 50)
    
    try:
        # Initialize signal sender
        sender = FreqtradeSignalSender()
        
        # Test 1: Random signals
        print("\n📡 Test 1: Sending random signals...")
        sender.send_random_signal("BTC/USDT", "buy")
        sender.send_random_signal("ETH/USDT", "buy")
        print("✅ Random signals sent")
        
        # Test 2: Test signals
        print("\n📡 Test 2: Sending test signals...")
        sender.send_test_signal("BTC/USDT", "sell", "integration_test_exit")
        print("✅ Test signals sent")
        
        # Test 3: Anomaly signals
        print("\n📡 Test 3: Sending anomaly signals...")
        sender.send_anomaly_signal(
            pair="BTC/USDT",
            action="buy",
            anomaly_severity="HIGH",
            detector="statistical_detector",
            confidence=0.95,
            affected_metrics="cpu,memory,network",
            reason="Critical spike detected in system metrics"
        )
        print("✅ Anomaly signals sent")
        
        # Test 4: Custom stoploss
        print("\n📡 Test 4: Setting custom stoploss...")
        sender.set_custom_stoploss("BTC/USDT", -0.05)  # 5% stoploss
        print("✅ Custom stoploss set")
        
        # Check status
        print("\n📊 Signal Status:")
        status = sender.get_signal_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        print("\n🎉 All tests completed successfully!")
        print("\n💡 Now start Freqtrade to see the signals being processed:")
        print("   freqtrade trade --config freqtrade_execution_plugin/config.json --strategy AdsExecutionStrategy")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


def test_ads_integration():
    """Test ads-anomaly-detection integration"""
    print("\n🔗 Testing ads-anomaly-detection Integration")
    print("=" * 50)
    
    try:
        # Initialize ADS interface
        ads_interface = AdsFreqtradeInterface()
        
        # Simulate anomaly detection results
        anomaly_data = {
            "severity": "CRITICAL",
            "confidence": 0.95,
            "detector": "statistical_detector",
            "affected_metrics": "cpu_usage,memory_usage",
            "timestamp": "2025-08-06T00:30:00Z",
            "anomaly_type": "spike_detection"
        }
        
        print("🚨 Processing simulated anomaly for trading...")
        success = ads_interface.process_anomaly_for_trading(anomaly_data)
        
        if success:
            print("✅ Anomaly processed and trading signal generated")
        else:
            print("❌ Failed to process anomaly")
        
        # Run test sequence
        print("\n🧪 Running comprehensive test sequence...")
        success = ads_interface.run_test_sequence()
        
        if success:
            print("✅ Test sequence completed successfully")
        else:
            print("❌ Test sequence failed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ADS integration test failed: {e}")
        return False


def continuous_signal_test(duration: int = 60):
    """Send continuous signals for testing"""
    print(f"\n⚡ Running continuous signal test for {duration} seconds")
    print("=" * 50)
    
    try:
        sender = FreqtradeSignalSender()
        
        start_time = time.time()
        signal_count = 0
        
        while time.time() - start_time < duration:
            # Alternate between buy and sell signals
            action = "buy" if signal_count % 2 == 0 else "sell"
            pair = ["BTC/USDT", "ETH/USDT"][signal_count % 2]
            
            sender.send_random_signal(pair, action)
            signal_count += 1
            
            print(f"📡 Sent signal #{signal_count}: {action} {pair}")
            
            # Wait 5 seconds between signals
            time.sleep(5)
        
        print(f"\n✅ Continuous test completed: {signal_count} signals sent")
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Continuous test stopped by user")
        return True
    except Exception as e:
        logger.error(f"❌ Continuous test failed: {e}")
        return False


def clear_all_signals():
    """Clear all pending signals"""
    print("\n🧹 Clearing all pending signals")
    print("=" * 30)
    
    try:
        sender = FreqtradeSignalSender()
        sender.clear_signals()
        print("✅ All signals cleared")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to clear signals: {e}")
        return False


def show_menu():
    """Show test menu"""
    print("\n" + "=" * 60)
    print("FREQTRADE EXECUTION PLUGIN - TEST MENU")
    print("=" * 60)
    print("1. Test Signal Transmission")
    print("2. Test ads-anomaly-detection Integration")
    print("3. Continuous Signal Test (60 seconds)")
    print("4. Clear All Signals")
    print("5. Show Signal Status")
    print("6. Exit")
    print("=" * 60)


def show_signal_status():
    """Show current signal status"""
    try:
        sender = FreqtradeSignalSender()
        status = sender.get_signal_status()
        
        print("\n📊 Current Signal Status:")
        print("-" * 30)
        for key, value in status.items():
            print(f"{key}: {value}")
        
    except Exception as e:
        logger.error(f"❌ Failed to get signal status: {e}")


def main():
    """Main test interface"""
    print("🚀 Freqtrade Execution Plugin Test Suite")
    
    while True:
        show_menu()
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            test_signal_transmission()
        elif choice == "2":
            test_ads_integration()
        elif choice == "3":
            continuous_signal_test()
        elif choice == "4":
            clear_all_signals()
        elif choice == "5":
            show_signal_status()
        elif choice == "6":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option, please try again")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
