#!/usr/bin/env python3
"""
Docker Logs Simulator - Shows what you'd see in Docker Desktop logs
"""

import json
import time
from datetime import datetime
from pathlib import Path


def simulate_docker_logs():
    """Simulate Docker Desktop style logging output"""
    
    print("🐳 Docker Desktop - signal-detection-plugin Container Logs")
    print("=" * 70)
    print("Container: signal-detection-plugin")
    print("Image: signal-detection-plugin:latest")
    print("Status: Running")
    print("=" * 70)
    
    # Read our storage results
    results_file = Path("storage_visualization_results.json")
    if not results_file.exists():
        print("❌ No storage results found. Run mock_storage_test.py first!")
        return
    
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    print(f"📊 Showing {len(data['recent_events'])} recent anomaly detections:")
    print("-" * 70)
    
    # Show recent events in Docker log format
    for i, event in enumerate(data['recent_events'][-10:], 1):
        timestamp = datetime.fromtimestamp(event['timestamp'])
        
        # Docker log entry format
        docker_timestamp = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        severity_emoji = {
            'low': '🟡',
            'medium': '🟠', 
            'high': '🔴',
            'critical': '🚨'
        }.get(event['severity'], '⚪')
        
        confidence_pct = f"{event['confidence']:.1%}"
        metrics_str = ', '.join(event['affected_metrics'][:2]) + ('...' if len(event['affected_metrics']) > 2 else '')
        max_z_score = max(event['z_scores'].values()) if event['z_scores'] else 0
        
        # Format like Docker Desktop
        print(f"{docker_timestamp} {severity_emoji} [{event['severity'].upper():8}] "
              f"ANOMALY DETECTED: {confidence_pct} confidence in {metrics_str} "
              f"(z-score: {max_z_score:.2f})")
    
    print("-" * 70)
    print("📈 Container Summary:")
    print(f"   Total Anomalies Detected: {data['total_anomalies']}")
    print(f"   Detection Rate: {data['total_anomalies']/3:.1f} anomalies/minute")
    print(f"   Critical Issues: {data['statistics']['by_severity'].get('critical', 0)}")
    print(f"   High Priority: {data['statistics']['by_severity'].get('high', 0)}")
    
    # Show top affected metrics
    print(f"\n🎯 Top Affected Metrics:")
    metrics = sorted(data['statistics']['by_metric'].items(), key=lambda x: x[1], reverse=True)
    for metric, count in metrics[:3]:
        percentage = (count / data['total_anomalies']) * 100
        print(f"   {metric}: {count} occurrences ({percentage:.1f}%)")
    
    print(f"\n⏰ Detection Window: {data['statistics']['time_range']['first'][:19]} to {data['statistics']['time_range']['last'][:19]}")
    
    print("\n" + "=" * 70)
    print("✅ Container is actively detecting and storing anomalies!")
    print("💡 This is what you'd see in Docker Desktop logs")


if __name__ == "__main__":
    simulate_docker_logs()
