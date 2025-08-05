#!/usr/bin/env python3
"""
Simple monitoring dashboard for Signal Detection Plugin
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.models import AnomalyEvent, Severity


class MonitoringDashboard:
    """Simple text-based monitoring dashboard"""
    
    def __init__(self):
        self.start_time = time.time()
        self.anomaly_stats = {
            'total': 0,
            'by_severity': {s.value: 0 for s in Severity},
            'by_detector': {},
            'recent': []
        }
        
    def update_stats(self, event: AnomalyEvent):
        """Update dashboard statistics"""
        self.anomaly_stats['total'] += 1
        self.anomaly_stats['by_severity'][event.severity.value] += 1
        
        detector_id = event.detector_id
        if detector_id not in self.anomaly_stats['by_detector']:
            self.anomaly_stats['by_detector'][detector_id] = 0
        self.anomaly_stats['by_detector'][detector_id] += 1
        
        # Keep last 10 events
        self.anomaly_stats['recent'].append({
            'timestamp': datetime.fromtimestamp(event.timestamp).strftime('%H:%M:%S'),
            'detector': detector_id,
            'severity': event.severity.value,
            'confidence': event.confidence,
            'metrics': event.affected_metrics
        })
        
        if len(self.anomaly_stats['recent']) > 10:
            self.anomaly_stats['recent'].pop(0)
    
    def clear_screen(self):
        """Clear terminal screen"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_dashboard(self):
        """Display the monitoring dashboard"""
        self.clear_screen()
        
        uptime = time.time() - self.start_time
        uptime_str = f"{int(uptime//3600):02d}:{int((uptime%3600)//60):02d}:{int(uptime%60):02d}"
        
        print("🔍 Signal Detection Plugin - Monitoring Dashboard")
        print("=" * 60)
        print(f"⏰ Uptime: {uptime_str}")
        print(f"📊 Total Anomalies: {self.anomaly_stats['total']}")
        print()
        
        # Severity breakdown
        print("📈 Anomalies by Severity:")
        for severity, count in self.anomaly_stats['by_severity'].items():
            if count > 0:
                bar = "█" * min(count, 20)
                print(f"   {severity.upper():8} │{bar:<20}│ {count}")
        print()
        
        # Detector breakdown
        if self.anomaly_stats['by_detector']:
            print("🔧 Anomalies by Detector:")
            for detector, count in self.anomaly_stats['by_detector'].items():
                bar = "█" * min(count, 20)
                print(f"   {detector[:15]:15} │{bar:<20}│ {count}")
            print()
        
        # Recent anomalies
        if self.anomaly_stats['recent']:
            print("🚨 Recent Anomalies (Last 10):")
            print("   Time     Detector          Severity   Conf  Metrics")
            print("   ────────────────────────────────────────────────────")
            for event in reversed(self.anomaly_stats['recent'][-10:]):
                metrics_str = ', '.join(event['metrics'][:2]) + ('...' if len(event['metrics']) > 2 else '')
                print(f"   {event['timestamp']} {event['detector'][:15]:15} {event['severity']:8} {event['confidence']:.2f}  {metrics_str}")
        else:
            print("🟢 No recent anomalies detected")
        
        print("\n" + "=" * 60)
        print("Press Ctrl+C to exit")


async def simulate_data_flow(dashboard):
    """Simulate data flow for demonstration"""
    import random
    
    detectors = ["statistical_detector", "ml_detector", "network_detector"]
    metrics = ["cpu_usage", "memory_usage", "network_io", "disk_usage", "response_time"]
    
    while True:
        # Simulate random anomaly detection
        if random.random() < 0.3:  # 30% chance of anomaly
            detector = random.choice(detectors)
            severity = random.choice(list(Severity))
            affected = random.sample(metrics, random.randint(1, 3))
            
            event = AnomalyEvent(
                detector_id=detector,
                timestamp=time.time(),
                severity=severity,
                confidence=random.uniform(0.5, 0.95),
                data={m: random.uniform(50, 100) for m in affected},
                anomaly_type="simulated",
                affected_metrics=affected,
                z_scores={m: random.uniform(2.0, 5.0) for m in affected}
            )
            
            dashboard.update_stats(event)
        
        await asyncio.sleep(2)  # Update every 2 seconds


async def main():
    """Main dashboard function"""
    dashboard = MonitoringDashboard()
    
    print("Starting Signal Detection Plugin Dashboard...")
    print("This is a simulation - replace with real plugin integration")
    await asyncio.sleep(2)
    
    # Start data simulation
    data_task = asyncio.create_task(simulate_data_flow(dashboard))
    
    try:
        while True:
            dashboard.display_dashboard()
            await asyncio.sleep(3)  # Refresh every 3 seconds
            
    except KeyboardInterrupt:
        print("\nShutting down dashboard...")
        data_task.cancel()
        try:
            await data_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
