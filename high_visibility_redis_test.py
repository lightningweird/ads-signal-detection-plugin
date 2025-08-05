#!/usr/bin/env python3
"""
High-Visibility Redis Test - This WILL show up in Redis logs
"""

import asyncio
import redis.asyncio as redis
import time
from datetime import datetime


async def create_obvious_redis_activity():
    """Generate Redis activity that will definitely show in logs"""
    
    print("🔥 Creating HIGH-VISIBILITY Redis Activity")
    print("=" * 50)
    
    try:
        # Connect to Redis
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
        
        await redis_client.ping()
        print("✅ Connected to Redis")
        
        # Enable Redis slowlog (this will definitely log)
        await redis_client.config_set('slowlog-log-slower-than', '0')  # Log ALL commands
        print("✅ Enabled Redis command logging")
        
        # Clear existing slowlog
        await redis_client.slowlog_reset()
        
        print("\n🚀 Generating Redis commands that WILL appear in logs...")
        
        # Generate a bunch of obvious Redis operations
        for i in range(20):
            timestamp = datetime.now().isoformat()
            
            # 1. Set a key with obvious name
            key = f"SIGNAL_DETECTION_TEST_{i}"
            value = f"anomaly_detected_at_{timestamp}"
            await redis_client.set(key, value)
            
            # 2. Add to a list with obvious name
            await redis_client.lpush("SIGNAL_DETECTION_ANOMALIES", f"critical_anomaly_{i}")
            
            # 3. Increment a counter (this creates Redis operations)
            await redis_client.incr("SIGNAL_DETECTION_COUNTER")
            
            # 4. Set with expiration (more Redis ops)
            await redis_client.setex(f"TEMP_ANOMALY_{i}", 60, f"expires_in_60s_{i}")
            
            # 5. Publish to a channel (pub/sub activity)
            await redis_client.publish("SIGNAL_DETECTION_CHANNEL", f"TEST_MESSAGE_{i}")
            
            print(f"   Generated Redis operations #{i+1}")
            await asyncio.sleep(0.5)  # Half second between batches
        
        print("\n📊 Checking Redis slowlog (shows ALL executed commands):")
        slowlog = await redis_client.slowlog_get(30)  # Get last 30 commands
        
        print(f"   Found {len(slowlog)} recent Redis commands:")
        for entry in slowlog[:10]:  # Show first 10
            command = ' '.join(entry['command'])
            duration = entry['duration']
            print(f"     Command: {command} (took {duration}μs)")
        
        # Show current Redis info
        print(f"\n💾 Current Redis Database Status:")
        info = await redis_client.info('keyspace')
        print(f"   Keyspace info: {info}")
        
        dbsize = await redis_client.dbsize()
        print(f"   Total keys in database: {dbsize}")
        
        # Show our specific keys
        our_keys = await redis_client.keys("SIGNAL_DETECTION_*")
        print(f"   Our test keys created: {len(our_keys)}")
        
        # Show list length
        list_length = await redis_client.llen("SIGNAL_DETECTION_ANOMALIES")
        print(f"   Anomaly list length: {list_length}")
        
        # Show counter value
        counter_value = await redis_client.get("SIGNAL_DETECTION_COUNTER")
        print(f"   Detection counter: {counter_value}")
        
        # Force a Redis save (this will definitely show in logs)
        print(f"\n💾 Forcing Redis BGSAVE (this WILL appear in your logs)...")
        await redis_client.bgsave() 
        print("✅ Background save initiated - check your Redis logs!")
        
        # Reset slowlog config to normal
        await redis_client.config_set('slowlog-log-slower-than', '10000')  # Back to normal
        
        await redis_client.aclose()
        
        print(f"\n🎯 SUCCESS! Check your Redis logs now for:")
        print(f"   - Background save messages")
        print(f"   - Database operations")
        print(f"   - Memory usage changes")
        print(f"   - The slowlog captured {len(slowlog)} commands")
        
    except Exception as e:
        print(f"❌ Error: {e}")


# Let's also check if Redis logging is properly configured
async def check_redis_logging_config():
    """Check Redis logging configuration"""
    print("🔧 Checking Redis Logging Configuration")
    print("-" * 40)
    
    try:
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        await redis_client.ping()
        
        # Check logging settings
        log_level = await redis_client.config_get('loglevel')
        slowlog_slower = await redis_client.config_get('slowlog-log-slower-than')
        slowlog_max = await redis_client.config_get('slowlog-max-len')
        
        print(f"   Log level: {log_level}")
        print(f"   Slowlog threshold: {slowlog_slower} microseconds")
        print(f"   Slowlog max entries: {slowlog_max}")
        
        await redis_client.aclose()
        
    except Exception as e:
        print(f"❌ Error checking config: {e}")


async def main():
    await check_redis_logging_config()
    print()
    await create_obvious_redis_activity()


if __name__ == "__main__":
    asyncio.run(main())
