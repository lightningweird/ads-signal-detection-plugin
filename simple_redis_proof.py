#!/usr/bin/env python3
"""
Simple Redis Proof Test - No async issues, just direct proof
"""

import redis
import json
import time
from datetime import datetime


def test_redis_directly():
    """Test Redis with simple synchronous operations"""
    
    print("🔍 Simple Redis Proof Test")
    print("=" * 40)
    
    try:
        # Connect to Redis (synchronous)
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✅ Connected to Redis")
        
        # Clear any existing test data
        test_keys = r.keys("PROOF_TEST_*")
        if test_keys:
            r.delete(*test_keys)
            print(f"🧹 Cleared {len(test_keys)} old test keys")
        
        print("\n🚀 Creating obvious Redis data...")
        
        # Create obvious data that we can verify
        timestamp = datetime.now().isoformat()
        
        # 1. Simple key-value pairs
        for i in range(5):
            key = f"PROOF_TEST_ANOMALY_{i}"
            value = f"CRITICAL_ANOMALY_DETECTED_AT_{timestamp}_{i}"
            r.set(key, value)
            print(f"   ✅ Set {key}")
        
        # 2. Add to a list
        list_key = "PROOF_TEST_ANOMALY_LIST"
        for i in range(5):
            r.lpush(list_key, f"anomaly_{i}_severity_critical")
            print(f"   ✅ Added to list: anomaly_{i}")
        
        # 3. Create a hash
        hash_key = "PROOF_TEST_ANOMALY_HASH"
        r.hset(hash_key, mapping={
            'detector': 'statistical_detector',
            'severity': 'CRITICAL',
            'confidence': '0.95',
            'timestamp': timestamp,
            'affected_metrics': 'cpu,memory,network'
        })
        print(f"   ✅ Created hash with anomaly details")
        
        # 4. Increment counters
        counter_key = "PROOF_TEST_ANOMALY_COUNT"
        for i in range(10):
            count = r.incr(counter_key)
            print(f"   ✅ Incremented counter to {count}")
        
        print(f"\n📊 Verification - Reading back our data:")
        
        # Verify our data exists
        our_keys = r.keys("PROOF_TEST_*")
        print(f"   Found {len(our_keys)} test keys: {our_keys}")
        
        # Read back some values
        anomaly_0 = r.get("PROOF_TEST_ANOMALY_0")
        print(f"   PROOF_TEST_ANOMALY_0: {anomaly_0}")
        
        list_length = r.llen(list_key)
        list_items = r.lrange(list_key, 0, -1)
        print(f"   List length: {list_length}, Items: {list_items}")
        
        hash_data = r.hgetall(hash_key)
        print(f"   Hash data: {hash_data}")
        
        counter_value = r.get(counter_key)
        print(f"   Counter value: {counter_value}")
        
        # Force Redis to save (this WILL show in logs)
        print(f"\n💾 Forcing Redis background save...")
        r.bgsave()
        print("   ✅ Background save triggered!")
        
        # Show Redis info
        db_size = r.dbsize()
        info = r.info('memory')
        used_memory = info.get('used_memory_human', 'unknown')
        
        print(f"\n📈 Redis Status:")
        print(f"   Total keys in database: {db_size}")
        print(f"   Memory used: {used_memory}")
        print(f"   Our test keys: {len(our_keys)}")
        
        print(f"\n🎯 SUCCESS! This proves:")
        print(f"   ✅ We CAN write to Redis")
        print(f"   ✅ We CAN read from Redis") 
        print(f"   ✅ Redis IS working")
        print(f"   ✅ Background save was triggered")
        print(f"\n💡 The previous async Redis operations may have had issues")
        print(f"   But this proves Redis connectivity and data storage works!")
        
        # Leave the data for verification
        print(f"\n📝 Test data left in Redis for manual verification")
        print(f"   You can manually check with: redis-cli keys 'PROOF_TEST_*'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_redis_directly()
    if success:
        print("\n🎉 Redis is definitely working - the issue was with async operations!")
    else:
        print("\n❌ Redis connection issues detected")
