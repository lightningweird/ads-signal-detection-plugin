#!/usr/bin/env python3
"""
Mock Storage Test - Visual proof that anomalies are being stored
Generates random graph data and shows storage in action with detailed logging
"""

import asyncio
import json
import time
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import List, Dict, Any
import math

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.models import AnomalyEvent, Severity, DataPoint
from src.detectors.statistical import StatisticalAnomalyDetector
from src.memory.interface import AdsMemoryInterface


class MockDataStorage:
    """Mock storage system that logs everything for visibility"""
    
    def __init__(self):
        self.stored_events: List[AnomalyEvent] = []
        self.raw_data_points: List[DataPoint] = []
        self.storage_log = []
        
        # Setup detailed logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('storage_test.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("MockStorage")
        
    async def store_anomaly(self, event: AnomalyEvent):
        """Store anomaly with detailed logging"""
        timestamp = datetime.fromtimestamp(event.timestamp)
        
        # Log the storage event
        self.logger.info(f"🔥 ANOMALY STORED: {event.detector_id}")
        self.logger.info(f"   Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"   Severity: {event.severity.value.upper()}")
        self.logger.info(f"   Confidence: {event.confidence:.2%}")
        self.logger.info(f"   Affected Metrics: {', '.join(event.affected_metrics)}")
        self.logger.info(f"   Z-scores: {event.z_scores}")
        self.logger.info(f"   Raw Values: {event.raw_values}")
        
        # Store the event
        self.stored_events.append(event)
        
        # Add to storage log for visualization
        log_entry = {
            'timestamp': event.timestamp,
            'severity': event.severity.value,
            'confidence': event.confidence,
            'metrics': event.affected_metrics,
            'z_scores': event.z_scores,
            'raw_values': event.raw_values
        }
        self.storage_log.append(log_entry)
        
        # Simulate Docker-style JSON logging
        docker_log = {
            "time": timestamp.isoformat(),
            "level": "info",
            "msg": "anomaly_detected",
            "service": "signal-detection-plugin",
            "detector_id": event.detector_id,
            "severity": event.severity.value,
            "confidence": event.confidence,
            "affected_metrics": event.affected_metrics,
            "anomaly_score": max(event.z_scores.values()) if event.z_scores else 0
        }
        print(f"DOCKER_LOG: {json.dumps(docker_log)}")
        
    def get_storage_stats(self):
        """Get comprehensive storage statistics"""
        total_events = len(self.stored_events)
        if total_events == 0:
            return {
                "total": 0,
                "by_severity": {},
                "by_detector": {},
                "by_metric": {},
                "time_range": None
            }
            
        severity_counts = {}
        detector_counts = {}
        metric_counts = {}
        
        for event in self.stored_events:
            # Count by severity
            severity = event.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count by detector
            detector = event.detector_id
            detector_counts[detector] = detector_counts.get(detector, 0) + 1
            
            # Count by affected metrics
            for metric in event.affected_metrics:
                metric_counts[metric] = metric_counts.get(metric, 0) + 1
        
        return {
            "total": total_events,
            "by_severity": severity_counts,
            "by_detector": detector_counts,
            "by_metric": metric_counts,
            "time_range": {
                "first": datetime.fromtimestamp(self.stored_events[0].timestamp).isoformat(),
                "last": datetime.fromtimestamp(self.stored_events[-1].timestamp).isoformat()
            }
        }


class GraphDataGenerator:
    """Generate realistic graph data with controllable anomalies"""
    
    def __init__(self):
        self.time_base = time.time()
        self.cpu_baseline = 30.0
        self.memory_baseline = 45.0
        self.network_baseline = 200.0
        self.disk_baseline = 15.0
        
    def generate_normal_data(self, timestamp_offset: int = 0) -> Dict[str, Any]:
        """Generate normal system metrics"""
        current_time = self.time_base + timestamp_offset
        
        # Add some natural variation
        cpu_noise = random.uniform(-5, 5)
        memory_noise = random.uniform(-8, 8)
        network_noise = random.uniform(-50, 50)
        disk_noise = random.uniform(-3, 3)
        
        # Add some cyclical patterns (like daily usage patterns)
        time_factor = math.sin(timestamp_offset * 0.01) * 5
        
        return {
            'timestamp': current_time,
            'cpu_usage': max(0, self.cpu_baseline + cpu_noise + time_factor),
            'memory_usage': max(0, self.memory_baseline + memory_noise + time_factor * 0.5),
            'network_io': max(0, self.network_baseline + network_noise + time_factor * 10),
            'disk_usage': max(0, self.disk_baseline + disk_noise + time_factor * 0.2),
            'response_time': max(10, 100 + random.uniform(-20, 20)),
            'error_rate': max(0, random.uniform(0, 2))
        }
    
    def generate_anomaly_data(self, anomaly_type: str, timestamp_offset: int = 0) -> Dict[str, Any]:
        """Generate anomalous system metrics"""
        base_data = self.generate_normal_data(timestamp_offset)
        
        if anomaly_type == "cpu_spike":
            base_data['cpu_usage'] = random.uniform(85, 98)
        elif anomaly_type == "memory_leak":
            base_data['memory_usage'] = random.uniform(82, 95)
        elif anomaly_type == "network_flood":
            base_data['network_io'] = random.uniform(800, 1500)
        elif anomaly_type == "disk_full":
            base_data['disk_usage'] = random.uniform(88, 98)
        elif anomaly_type == "response_timeout":
            base_data['response_time'] = random.uniform(5000, 15000)
        elif anomaly_type == "error_storm":
            base_data['error_rate'] = random.uniform(15, 45)
        elif anomaly_type == "multi_metric":
            # Multiple metrics affected
            base_data['cpu_usage'] = random.uniform(80, 95)
            base_data['memory_usage'] = random.uniform(80, 92)
            base_data['network_io'] = random.uniform(600, 1200)
        
        return base_data
    
    def generate_scenario_data(self, scenario: str = "normal_with_spikes") -> List[Dict[str, Any]]:
        """Generate a complete scenario of data"""
        data_points = []
        
        if scenario == "normal_with_spikes":
            # 100 normal points with 5 anomalies injected
            for i in range(100):
                if i in [20, 35, 50, 70, 85]:  # Inject anomalies at specific points
                    anomaly_types = ["cpu_spike", "memory_leak", "network_flood", "response_timeout", "multi_metric"]
                    anomaly_type = random.choice(anomaly_types)
                    data_points.append(self.generate_anomaly_data(anomaly_type, i))
                else:
                    data_points.append(self.generate_normal_data(i))
        
        elif scenario == "gradual_degradation":
            # Gradual performance degradation
            for i in range(80):
                base_data = self.generate_normal_data(i)
                
                # Gradual increase in resource usage
                degradation_factor = i / 80.0
                base_data['cpu_usage'] += degradation_factor * 40
                base_data['memory_usage'] += degradation_factor * 30
                base_data['response_time'] += degradation_factor * 2000
                
                data_points.append(base_data)
        
        elif scenario == "burst_traffic":
            # Normal → Traffic burst → Recovery
            for i in range(120):
                if 40 <= i <= 80:  # Burst period
                    burst_data = self.generate_normal_data(i)
                    burst_data['network_io'] *= 3 + random.uniform(0, 2)
                    burst_data['cpu_usage'] += 20 + random.uniform(0, 15)
                    burst_data['response_time'] += 500 + random.uniform(0, 1000)
                    data_points.append(burst_data)
                else:
                    data_points.append(self.generate_normal_data(i))
        
        return data_points


async def run_storage_visualization_test():
    """Run comprehensive storage test with visualization"""
    print("🚀 Starting Mock Storage Visualization Test")
    print("=" * 60)
    
    # Initialize components
    storage = MockDataStorage()
    detector = StatisticalAnomalyDetector()
    generator = GraphDataGenerator()
    
    # Configure detector
    config = {
        'window_size': 20,
        'std_dev_threshold': 2.5,
        'metrics': ['cpu_usage', 'memory_usage', 'network_io', 'disk_usage', 'response_time', 'error_rate'],
        'use_iqr': True,
        'iqr_multiplier': 1.5,
        'use_mad': True
    }
    
    await detector.initialize(config)
    print(f"✅ Initialized detector: {detector.detector_id}")
    
    # Test different scenarios
    scenarios = [
        ("normal_with_spikes", "Normal operation with random spikes"),
        ("gradual_degradation", "Gradual system degradation"),
        ("burst_traffic", "Traffic burst scenario")
    ]
    
    for scenario_name, description in scenarios:
        print(f"\n📊 Testing Scenario: {description}")
        print("-" * 50)
        
        # Generate scenario data
        scenario_data = generator.generate_scenario_data(scenario_name)
        storage.logger.info(f"🎯 Starting scenario: {scenario_name}")
        storage.logger.info(f"   Description: {description}")
        storage.logger.info(f"   Data points: {len(scenario_data)}")
        
        anomaly_count = 0
        for i, data_point in enumerate(scenario_data):
            # Run detection
            result = await detector.detect(data_point)
            
            if result:
                await storage.store_anomaly(result)
                anomaly_count += 1
                
                # Show progress for major anomalies
                if result.severity in [Severity.HIGH, Severity.CRITICAL]:
                    print(f"   🚨 {result.severity.value.upper()} anomaly at point {i}: {result.affected_metrics}")
            
            # Progress indicator
            if i % 20 == 0:
                print(f"   Processed: {i}/{len(scenario_data)} points, Anomalies: {anomaly_count}")
        
        print(f"   ✅ Scenario complete: {anomaly_count} anomalies detected")
    
    # Generate final statistics
    stats = storage.get_storage_stats()
    print(f"\n📈 FINAL STORAGE STATISTICS")
    print("=" * 60)
    print(f"Total Anomalies Stored: {stats['total']}")
    
    if stats['total'] > 0:
        if stats['by_severity']:
            print(f"\n🎯 By Severity:")
            for severity, count in stats['by_severity'].items():
                percentage = (count / stats['total']) * 100
                bar = "█" * min(int(percentage / 5), 20)
                print(f"   {severity.upper():8} │{bar:<20}│ {count:3d} ({percentage:5.1f}%)")
        
        if stats['by_detector']:
            print(f"\n🔧 By Detector:")
            for detector_name, count in stats['by_detector'].items():
                percentage = (count / stats['total']) * 100
                bar = "█" * min(int(percentage / 5), 20)
                print(f"   {detector_name[:15]:15} │{bar:<20}│ {count:3d} ({percentage:5.1f}%)")
        
        if stats['by_metric']:
            print(f"\n📊 By Affected Metric:")
            for metric, count in stats['by_metric'].items():
                percentage = (count / stats['total']) * 100
                bar = "█" * min(int(percentage / 5), 20)
                print(f"   {metric[:15]:15} │{bar:<20}│ {count:3d} ({percentage:5.1f}%)")
        
        if stats['time_range']:
            print(f"\n⏰ Time Range:")
            print(f"   First: {stats['time_range']['first']}")
            print(f"   Last:  {stats['time_range']['last']}")
    
    # Show recent anomalies in detail
    if len(storage.stored_events) > 0:
        print(f"\n🔍 Recent Anomalies (Last 5):")
        print("-" * 60)
        recent_events = storage.stored_events[-5:]
        for i, event in enumerate(recent_events, 1):
            timestamp = datetime.fromtimestamp(event.timestamp)
            print(f"{i}. {timestamp.strftime('%H:%M:%S')} - {event.severity.value.upper()}")
            print(f"   Detector: {event.detector_id}")
            print(f"   Confidence: {event.confidence:.1%}")
            print(f"   Metrics: {', '.join(event.affected_metrics)}")
            if event.z_scores:
                max_z = max(event.z_scores.values())
                print(f"   Max Z-Score: {max_z:.2f}")
            print()
    
    # Create visualization data file
    viz_data = {
        "test_timestamp": datetime.now().isoformat(),
        "total_anomalies": stats['total'],
        "statistics": stats,
        "recent_events": [
            {
                "timestamp": event.timestamp,
                "severity": event.severity.value,
                "confidence": event.confidence,
                "affected_metrics": event.affected_metrics,
                "z_scores": event.z_scores
            }
            for event in storage.stored_events[-10:]  # Last 10 events
        ]
    }
    
    with open("storage_visualization_results.json", "w") as f:
        json.dump(viz_data, f, indent=2)
    
    print(f"\n💾 Results saved to:")
    print(f"   📋 storage_test.log - Detailed logs")
    print(f"   📊 storage_visualization_results.json - Visualization data")
    
    print(f"\n🎉 Storage test complete! {stats['total']} anomalies successfully stored and logged.")
    
    return stats['total'] > 0


if __name__ == "__main__":
    asyncio.run(run_storage_visualization_test())
