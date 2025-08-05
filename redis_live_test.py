#!/usr/bin/env python3
"""
Redis Integration Test - Connect to your actual Redis instance and stream anomalies
"""

import asyncio
import json
import time
import random
import sys
from pathlib import Path
from datetime import datetime
import redis.asyncio as redis

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.models import AnomalyEvent, Severity
from src.detectors.statistical import StatisticalAnomalyDetector


class RedisAnomalyStreamer:
    """Stream anomalies to your actual Redis instance"""
    
    def __init__(self):
        self.detector = None
        self.redis_client = None
        self.anomaly_count = 0
        
    async def connect_to_redis(self):
        """Connect to your Redis instance"""
        try:
            # Connect to Redis (adjust host/port if needed)
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            print("✅ Connected to Redis successfully!")
            
            # Set up Redis streams for anomalies
            stream_name = "anomaly_stream"
            try:
                await self.redis_client.xgroup_create(stream_name, "anomaly_processors", "0", mkstream=True)
                print("✅ Created Redis stream group for anomaly processing")
            except Exception as e:
                if "BUSYGROUP" in str(e):
                    print("✅ Redis stream group already exists")
                else:
                    print(f"⚠️  Warning creating stream group: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            print("💡 Make sure Redis is running on localhost:6379")
            return False
    
    async def initialize_detector(self):
        """Initialize the anomaly detector"""
        self.detector = StatisticalAnomalyDetector()
        config = {
            'window_size': 15,
            'std_dev_threshold': 2.0,
            'metrics': ['cpu_usage', 'memory_usage', 'network_io', 'response_time'],
            'use_iqr': True
        }
        await self.detector.initialize(config)
        print("✅ Statistical anomaly detector initialized")
    
    async def stream_anomaly_to_redis(self, anomaly: AnomalyEvent):
        """Stream anomaly to Redis with multiple storage methods"""
        if not self.redis_client:
            return
            
        timestamp = datetime.fromtimestamp(anomaly.timestamp)
        self.anomaly_count += 1
        
        # 1. Add to Redis Stream (for real-time processing)
        stream_data = {
            'anomaly_id': f"anomaly_{self.anomaly_count}",
            'detector_id': anomaly.detector_id,
            'timestamp': timestamp.isoformat(),
            'severity': anomaly.severity.value,
            'confidence': f"{anomaly.confidence:.3f}",
            'affected_metrics': json.dumps(anomaly.affected_metrics),
            'z_scores': json.dumps(anomaly.z_scores),
            'raw_values': json.dumps(anomaly.raw_values)
        }
        
        stream_id = await self.redis_client.xadd("anomaly_stream", stream_data)
        
        # 2. Store in Redis Hash (for quick lookup)
        hash_key = f"anomaly:{self.anomaly_count}"
        self.redis_client.hset(hash_key, mapping=stream_data)
        await self.redis_client.expire(hash_key, 3600)  # Expire in 1 hour
        
        # 3. Add to sorted set by severity (for priority processing)
        severity_score = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}.get(anomaly.severity.value, 1)
        await self.redis_client.zadd("anomalies_by_severity", {hash_key: severity_score})
        
        # 4. Publish to Redis pub/sub for real-time notifications
        notification = {
            'type': 'anomaly_detected',
            'anomaly_id': f"anomaly_{self.anomaly_count}",
            'severity': anomaly.severity.value,
            'confidence': anomaly.confidence,
            'metrics': anomaly.affected_metrics,
            'timestamp': timestamp.isoformat()
        }
        
        await self.redis_client.publish("anomaly_notifications", json.dumps(notification))
        
        # Log to console (will show in Docker logs)
        severity_emoji = {'low': '🟡', 'medium': '🟠', 'high': '🔴', 'critical': '🚨'}
        emoji = severity_emoji.get(anomaly.severity.value, '⚪')
        
        print(f"🔥 REDIS ANOMALY #{self.anomaly_count}: {emoji} {anomaly.severity.value.upper()}")
        print(f"   Stream ID: {stream_id}")
        print(f"   Confidence: {anomaly.confidence:.1%}")
        print(f"   Metrics: {', '.join(anomaly.affected_metrics)}")
        print(f"   Z-scores: {anomaly.z_scores}")
        print(f"   Stored in Redis hash: {hash_key}")
        print()
    
    def generate_realistic_data(self, t: int) -> dict:
        """Generate realistic system data"""
        import math
        
        # Simulate daily patterns
        hour_cycle = math.sin(t * 0.01) * 15
        noise = random.uniform(-5, 5)
        
        # CPU with occasional spikes
        cpu_base = 35 + hour_cycle + noise
        if random.random() < 0.08:  # 8% chance of CPU spike
            cpu_base += random.uniform(40, 60)
            
        # Memory with potential leaks
        memory_base = 45 + hour_cycle * 0.7 + noise * 0.6
        if random.random() < 0.05:  # 5% chance of memory leak
            memory_base += random.uniform(30, 50)
            
        # Network with burst traffic
        network_base = 150 + hour_cycle * 10 + noise * 5
        if random.random() < 0.06:  # 6% chance of network burst
            network_base += random.uniform(200, 500)
            
        # Response time with timeout issues
        response_base = 120 + abs(hour_cycle) * 5 + abs(noise) * 2
        if random.random() < 0.04:  # 4% chance of timeout spike
            response_base += random.uniform(500, 2000)
        
        return {
            'timestamp': time.time() + t,
            'cpu_usage': max(5, min(100, cpu_base)),
            'memory_usage': max(10, min(95, memory_base)),
            'network_io': max(50, network_base),
            'response_time': max(10, response_base)
        }
    
    async def run_real_time_detection(self, duration_minutes: int = 5):
        """Run real-time anomaly detection and stream to Redis"""
        print(f"🚀 Starting {duration_minutes}-minute real-time anomaly detection")
        print("📡 Streaming anomalies to your Redis instance...")
        print("🔍 Check Redis logs for activity!")
        print()
        
        duration_seconds = duration_minutes * 60
        
        try:
            for t in range(duration_seconds):
                # Generate realistic data
                data = self.generate_realistic_data(t)
                
                # Detect anomalies
                if self.detector:
                    anomaly = await self.detector.detect(data)
                    
                    if anomaly:
                        await self.stream_anomaly_to_redis(anomaly)
                
                # Progress update every 30 seconds
                if t > 0 and t % 30 == 0:
                    print(f"⏰ Runtime: {t//60:02d}:{t%60:02d} - Anomalies detected: {self.anomaly_count}")
                
                await asyncio.sleep(1)  # 1 second between data points
                
        except KeyboardInterrupt:
            print("\n🛑 Detection stopped by user")
        
        # Final Redis statistics
        if self.redis_client:
            try:
                stream_length = await self.redis_client.xlen("anomaly_stream")
                hash_count = len(await self.redis_client.keys("anomaly:*"))
                severity_count = await self.redis_client.zcard("anomalies_by_severity")
                
                print(f"\n📊 Final Redis Statistics:")
                print(f"   Stream entries: {stream_length}")
                print(f"   Hash entries: {hash_count}")
                print(f"   Severity index entries: {severity_count}")
                print(f"   Total anomalies processed: {self.anomaly_count}")
                
            except Exception as e:
                print(f"⚠️  Error getting Redis stats: {e}")
    
    async def cleanup(self):
        """Clean up Redis connection"""
        if self.redis_client:
            await self.redis_client.aclose()
            print("✅ Redis connection closed")


async def main():
    """Main function"""
    print("🔗 Redis Integration Test - Live Anomaly Streaming")
    print("=" * 60)
    
    streamer = RedisAnomalyStreamer()
    
    # Connect to Redis
    if not await streamer.connect_to_redis():
        print("❌ Cannot proceed without Redis connection")
        return
    
    # Initialize detector
    await streamer.initialize_detector()
    
    print("\n🎯 This will:")
    print("   1. Generate realistic system metrics")
    print("   2. Detect anomalies in real-time")
    print("   3. Stream results to your Redis instance")
    print("   4. Create multiple Redis data structures")
    print("   5. Publish notifications via pub/sub")
    print("\n🐳 You should see activity in your Redis logs!")
    print("📊 The anomalies will be stored in Redis for your ads-anomaly-detection system")
    
    # Run detection
    try:
        await streamer.run_real_time_detection(3)  # Run for 3 minutes
    finally:
        await streamer.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
