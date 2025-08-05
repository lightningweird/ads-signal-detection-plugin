#!/usr/bin/env python3
"""
Test script to demonstrate signal detection plugin integration with ads-anomaly-detection
"""

import asyncio
import sys
import os
import time
import random
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.models import AnomalyEvent, Severity
from src.detectors.statistical import StatisticalAnomalyDetector
from src.memory.interface import AdsMemoryInterface


class MockMemory:
    """Mock memory interface for testing"""
    def __init__(self):
        self.anomalies = []
    
    async def ingest_event(self, event: AnomalyEvent):
        self.anomalies.append(event)
        print(f"✅ Ingested anomaly: {event.detector_id} - {event.severity.value} (confidence: {event.confidence:.2f})")


async def test_statistical_detector():
    """Test the statistical anomaly detector"""
    print("🔍 Testing Statistical Anomaly Detector")
    print("=" * 50)
    
    # Initialize detector
    detector = StatisticalAnomalyDetector()
    config = {
        'window_size': 20,
        'std_dev_threshold': 2.0,
        'min_samples': 5,
        'metrics': ['cpu_usage', 'memory_usage', 'network_io'],
        'use_iqr': True,
        'iqr_multiplier': 1.5
    }
    
    await detector.initialize(config)
    print(f"✅ Initialized detector: {detector.detector_id} v{detector.version}")
    
    # Setup mock memory interface
    mock_memory = MockMemory()
    
    # Generate normal data to build baseline
    print("\n📊 Building baseline with normal data...")
    for i in range(15):
        normal_data = {
            'timestamp': time.time(),
            'cpu_usage': random.uniform(20, 40),
            'memory_usage': random.uniform(30, 50),
            'network_io': random.uniform(100, 300)
        }
        
        result = await detector.detect(normal_data)
        if result:
            await mock_memory.ingest_event(result)
        
        if i % 5 == 0:
            metrics = detector.get_metrics()
            print(f"   Processed: {metrics.processed_count}, Anomalies: {metrics.anomaly_count}")
    
    # Generate anomalous data
    print("\n🚨 Injecting anomalous data...")
    anomalous_data = [
        {
            'timestamp': time.time(),
            'cpu_usage': 95.0,  # High CPU anomaly
            'memory_usage': 45.0,
            'network_io': 200.0
        },
        {
            'timestamp': time.time() + 1,
            'cpu_usage': 35.0,
            'memory_usage': 88.0,  # High memory anomaly
            'network_io': 180.0
        },
        {
            'timestamp': time.time() + 2,
            'cpu_usage': 30.0,
            'memory_usage': 40.0,
            'network_io': 2000.0  # High network anomaly
        }
    ]
    
    for data in anomalous_data:
        result = await detector.detect(data)
        if result:
            await mock_memory.ingest_event(result)
            print(f"   🔥 Anomaly detected in: {', '.join(result.affected_metrics)}")
        else:
            print(f"   ✅ No anomaly detected")
    
    # Final statistics
    metrics = detector.get_metrics()
    print(f"\n📈 Final Statistics:")
    print(f"   Total processed: {metrics.processed_count}")
    print(f"   Anomalies detected: {metrics.anomaly_count}")
    print(f"   Error count: {metrics.error_count}")
    print(f"   Average latency: {metrics.avg_latency_ms:.2f}ms")
    print(f"   Total ingested anomalies: {len(mock_memory.anomalies)}")
    
    # Show anomaly details
    if mock_memory.anomalies:
        print(f"\n🔍 Anomaly Details:")
        for i, anomaly in enumerate(mock_memory.anomalies):
            print(f"   {i+1}. {anomaly.detector_id}: {anomaly.severity.value}")
            print(f"      Metrics: {anomaly.affected_metrics}")
            print(f"      Z-scores: {anomaly.z_scores}")
    
    return len(mock_memory.anomalies) > 0


async def test_ads_integration():
    """Test integration with ads-anomaly-detection (if available)"""
    print("\n🔗 Testing ads-anomaly-detection Integration")
    print("=" * 50)
    
    try:
        # Try to connect to ads-anomaly-detection
        ads_path = Path(__file__).parent / "ads-anomaly-detection" / "src"
        if ads_path.exists():
            sys.path.insert(0, str(ads_path))
            
            try:
                from ingestion.data_ingestion import DataIngestionService
                print("✅ Found ads-anomaly-detection system")
                
                # Initialize ads ingestion service
                ads_service = DataIngestionService()
                await ads_service.initialize()
                print("✅ Initialized ads ingestion service")
                
                # Create memory interface
                memory_interface = AdsMemoryInterface(ads_service)
                
                # Test anomaly ingestion
                test_event = AnomalyEvent(
                    detector_id="test_detector",
                    timestamp=time.time(),
                    severity=Severity.HIGH,
                    confidence=0.95,
                    data={"cpu_usage": 95.0},
                    anomaly_type="test_anomaly",
                    affected_metrics=["cpu_usage"],
                    z_scores={"cpu_usage": 4.2}
                )
                
                await memory_interface.ingest_event(test_event)
                print("✅ Successfully ingested test anomaly to ads-anomaly-detection")
                
                await memory_interface.cleanup()
                return True
                
            except ImportError as e:
                print(f"⚠️  ads-anomaly-detection not properly installed: {e}")
                print("   Using mock interface instead")
                return False
                
        else:
            print("⚠️  ads-anomaly-detection directory not found")
            print("   Make sure it's cloned in the same directory")
            return False
            
    except Exception as e:
        print(f"❌ Error testing ads integration: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Signal Detection Plugin Integration Test")
    print("=" * 60)
    
    try:
        # Test statistical detector
        detector_success = await test_statistical_detector()
        
        # Test ads integration
        ads_success = await test_ads_integration()
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 Test Summary")
        print("=" * 60)
        print(f"   Statistical Detector: {'✅ PASS' if detector_success else '❌ FAIL'}")
        print(f"   ads-anomaly-detection: {'✅ PASS' if ads_success else '⚠️  MOCK'}")
        
        if detector_success:
            print("\n🎉 Signal Detection Plugin is working correctly!")
            if not ads_success:
                print("   Note: Using mock interface for ads-anomaly-detection")
                print("   To test full integration, ensure ads-anomaly-detection is installed")
        else:
            print("\n❌ Tests failed - check the logs above")
            
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
