#!/usr/bin/env python3
"""
Real-time Graph Data Visualizer
Shows live anomaly detection with random graph data
"""

import asyncio
import json
import time
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta
import math

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.models import AnomalyEvent, Severity
from src.detectors.statistical import StatisticalAnomalyDetector


class GraphDataVisualizer:
    """Real-time graph data visualization"""
    
    def __init__(self):
        self.detector = None
        self.data_history = []
        self.anomaly_history = []
        self.graph_width = 60
        self.start_time = time.time()
        
    async def initialize(self):
        """Initialize the detector"""
        self.detector = StatisticalAnomalyDetector()
        config = {
            'window_size': 20,
            'std_dev_threshold': 2.0,
            'metrics': ['cpu_usage', 'memory_usage', 'network_io'],
            'use_iqr': True
        }
        await self.detector.initialize(config)
        print("✅ Graph Data Detector initialized")
    
    def generate_realistic_data(self, t: int) -> dict:
        """Generate realistic system metrics over time"""
        # Base values with realistic patterns
        hour_cycle = math.sin(t * 0.02) * 10  # Daily usage pattern
        noise = random.uniform(-3, 3)
        
        # CPU usage (20-80% normal range)
        cpu_base = 35 + hour_cycle + noise
        cpu_spike = random.uniform(0, 60) if random.random() < 0.05 else 0  # 5% chance of spike
        cpu_usage = max(5, min(100, cpu_base + cpu_spike))
        
        # Memory usage (30-70% normal range)
        memory_base = 45 + hour_cycle * 0.5 + noise * 0.8
        memory_leak = random.uniform(0, 40) if random.random() < 0.03 else 0  # 3% chance of leak
        memory_usage = max(10, min(95, memory_base + memory_leak))
        
        # Network IO (100-500 MB/s normal range)
        network_base = 250 + hour_cycle * 20 + noise * 10
        network_burst = random.uniform(0, 800) if random.random() < 0.04 else 0  # 4% chance of burst
        network_io = max(50, network_base + network_burst)
        
        return {
            'timestamp': self.start_time + t,
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'network_io': network_io
        }
    
    def draw_ascii_graph(self, metric_name: str, values: list, anomalies: list) -> list:
        """Draw ASCII graph for a metric"""
        if not values:
            return []
            
        # Scale values to graph height (20 lines)
        min_val = min(values)
        max_val = max(values)
        scale = 19 / (max_val - min_val) if max_val > min_val else 1
        
        graph_lines = []
        
        # Draw from top to bottom
        for row in range(19, -1, -1):
            line = f"{metric_name:12} │"
            
            for i, val in enumerate(values[-self.graph_width:]):
                scaled_val = int((val - min_val) * scale)
                
                if i < len(anomalies) and anomalies[-(len(values) - i)]:
                    # Anomaly point
                    if scaled_val >= row:
                        line += "🔥"
                    else:
                        line += " "
                else:
                    # Normal point
                    if scaled_val >= row:
                        line += "█"
                    elif scaled_val >= row - 1:
                        line += "▄"
                    else:
                        line += " "
            
            # Add scale
            scale_val = min_val + (row / 19) * (max_val - min_val)
            line += f"│ {scale_val:6.1f}"
            graph_lines.append(line)
        
        # Add bottom border and time axis
        graph_lines.append("─" * 12 + "┼" + "─" * self.graph_width + "┼" + "─" * 8)
        
        # Time labels
        time_line = " " * 13
        for i in range(0, self.graph_width, 10):
            seconds_ago = self.graph_width - i
            time_line += f"{seconds_ago:2d}s".ljust(10)
        graph_lines.append(time_line + " (ago)")
        
        return graph_lines
    
    def clear_screen(self):
        """Clear the terminal screen"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
    
    async def run_visualization(self, duration_seconds: int = 180):
        """Run the real-time visualization"""
        print("🚀 Starting Real-time Graph Data Visualization")
        print("📊 Generating random system metrics with anomaly detection")
        print("🔥 Anomalies will appear as fire symbols in the graphs")
        print("\nPress Ctrl+C to stop\n")
        
        await asyncio.sleep(2)
        
        try:
            for t in range(duration_seconds):
                # Generate new data point
                data_point = self.generate_realistic_data(t)
                self.data_history.append(data_point)
                
                # Detect anomalies
                if self.detector:
                    anomaly = await self.detector.detect(data_point)
                    self.anomaly_history.append(anomaly is not None)
                else:
                    self.anomaly_history.append(False)
                
                # Keep only recent data
                if len(self.data_history) > self.graph_width * 2:
                    self.data_history = self.data_history[-self.graph_width * 2:]
                    self.anomaly_history = self.anomaly_history[-self.graph_width * 2:]
                
                # Update display every 2 seconds
                if t % 2 == 0:
                    self.clear_screen()
                    
                    print("🔍 Real-time Signal Detection - Graph Data Visualization")
                    print("=" * 80)
                    print(f"⏰ Runtime: {t//60:02d}:{t%60:02d}   "
                          f"📊 Data Points: {len(self.data_history)}   "
                          f"🚨 Anomalies: {sum(self.anomaly_history)}")
                    print()
                    
                    # Draw graphs for each metric
                    metrics = ['cpu_usage', 'memory_usage', 'network_io']
                    colors = ['CPU', 'Memory', 'Network']
                    
                    for metric, color in zip(metrics, colors):
                        values = [d[metric] for d in self.data_history]
                        graph_lines = self.draw_ascii_graph(f"{color} %", values, self.anomaly_history)
                        
                        for line in graph_lines:
                            print(line)
                        print()
                    
                    # Show recent anomalies
                    recent_anomalies = []
                    for i, (data, is_anomaly) in enumerate(zip(self.data_history[-10:], self.anomaly_history[-10:])):
                        if is_anomaly:
                            timestamp = datetime.fromtimestamp(data['timestamp'])
                            recent_anomalies.append(f"   🔥 {timestamp.strftime('%H:%M:%S')} - Anomaly detected")
                    
                    if recent_anomalies:
                        print("🚨 Recent Anomalies (Last 10 data points):")
                        for anomaly_msg in recent_anomalies[-5:]:  # Show last 5
                            print(anomaly_msg)
                    else:
                        print("✅ No recent anomalies detected")
                    
                    print("\n" + "=" * 80)
                    print("Legend: █ = Normal data, 🔥 = Anomaly detected")
                    print("Real-time anomaly detection with statistical analysis")
                
                await asyncio.sleep(1)  # 1 second per data point
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Visualization stopped by user")
        
        # Final summary
        total_anomalies = sum(self.anomaly_history)
        print(f"\n📈 Final Summary:")
        print(f"   Total Data Points: {len(self.data_history)}")
        print(f"   Total Anomalies: {total_anomalies}")
        print(f"   Anomaly Rate: {(total_anomalies/len(self.data_history)*100):.1f}%")
        
        # Save visualization data
        viz_data = {
            'timestamp': datetime.now().isoformat(),
            'total_points': len(self.data_history),
            'total_anomalies': total_anomalies,
            'anomaly_rate': total_anomalies/len(self.data_history)*100,
            'data_sample': self.data_history[-20:],  # Last 20 points
            'anomaly_flags': self.anomaly_history[-20:]
        }
        
        with open('realtime_graph_data.json', 'w') as f:
            json.dump(viz_data, f, indent=2)
        
        print(f"💾 Visualization data saved to realtime_graph_data.json")


async def main():
    """Main function"""
    visualizer = GraphDataVisualizer()
    await visualizer.initialize()
    await visualizer.run_visualization(120)  # Run for 2 minutes


if __name__ == "__main__":
    asyncio.run(main())
