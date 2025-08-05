# Signal Detection Plugin - Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.12+ 
- ads-anomaly-detection system (optional but recommended)
- Redis server (for distributed deployments)

### Installation

1. **Setup Virtual Environment**
   ```bash
   cd signal-detection-plugin
   python -m venv ads_env
   
   # Windows
   .\ads_env\Scripts\activate
   
   # Linux/Mac  
   source ads_env/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the Plugin**
   ```bash
   # Edit config.yaml to match your environment
   notepad config.yaml  # Windows
   nano config.yaml     # Linux
   ```

## 🔧 Configuration

### Basic Configuration (`config.yaml`)
```yaml
# Core plugin settings
plugin:
  name: "signal-detection-plugin"
  version: "1.0.0"
  
# Data sources - configure your inputs
data_sources:
  - type: "kafka"
    config:
      bootstrap_servers: ["localhost:9092"]
      topics: ["system_metrics", "application_logs"]
  
# Anomaly detectors to enable
detectors:
  statistical:
    enabled: true
    config:
      window_size: 50
      std_dev_threshold: 2.5

# Integration with ads-anomaly-detection
ads_integration:
  enabled: true
  batch_size: 100
  flush_interval: 5.0
```

## 🏃‍♂️ Running the Plugin

### Development Mode
```bash
python test_integration.py
```

### Production Mode
```bash
python run_production.py
```

### Docker Deployment
```bash
docker-compose up -d
```

## 📊 Testing

### Integration Test
The integration test demonstrates:
- Statistical anomaly detection on CPU, memory, and network metrics
- Mock data generation with baseline establishment
- Anomaly injection and detection
- Integration with ads-anomaly-detection (when available)

**Expected Output:**
```
🚀 Signal Detection Plugin Integration Test
🔍 Testing Statistical Anomaly Detector
✅ Initialized detector: statistical_detector v1.0.0
📊 Building baseline with normal data...
🚨 Injecting anomalous data...
   🔥 Anomaly detected in: cpu_usage
   🔥 Anomaly detected in: memory_usage  
   🔥 Anomaly detected in: network_io
📈 Final Statistics:
   Total processed: 18
   Anomalies detected: 8
   Average latency: 0.45ms
```

### Unit Tests
```bash
python -m pytest tests/ -v
```

## 🔌 ads-anomaly-detection Integration

### Installation
1. Clone ads-anomaly-detection in the same parent directory:
   ```bash
   cd ..
   git clone https://github.com/your-org/ads-anomaly-detection.git
   cd signal-detection-plugin
   ```

2. Update Python path in your deployment scripts to include ads system

3. Configure memory interface in `config.yaml`:
   ```yaml
   memory:
     type: "ads"  # or "redis" for distributed
     ads_integration:
       enabled: true
   ```

## 📈 Monitoring & Metrics

### Health Checks
- HTTP endpoint: `http://localhost:8080/health`
- Returns plugin status, detector states, and system metrics

### Prometheus Metrics
- `anomalies_detected_total`: Counter of total anomalies
- `detection_latency_seconds`: Histogram of detection latency
- `plugin_uptime_seconds`: Plugin uptime gauge

### Logging
- Structured JSON logging with configurable levels
- Automatic log rotation and retention
- Integration with ELK stack or similar

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t signal-detection-plugin:latest .
```

### Run Container
```bash
docker run -d \
  --name signal-detection \
  -p 8080:8080 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  signal-detection-plugin:latest
```

### Docker Compose
```bash
docker-compose up -d
```

## 🔧 Advanced Configuration

### Custom Detectors
Create custom detectors by extending `BaseDetector`:
```python
from src.detectors.base import BaseDetector

class MyCustomDetector(BaseDetector):
    async def detect(self, data):
        # Your detection logic here
        pass
```

### Data Source Plugins
Add new data sources by implementing `DataSource` interface:
```python
from src.core.interfaces import DataSource

class MyDataSource(DataSource):
    async def connect(self):
        # Connection logic
        pass
```

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure virtual environment is activated
   .\ads_env\Scripts\activate  # Windows
   
   # Check Python path
   python -c "import sys; print(sys.path)"
   ```

2. **Memory Interface Issues**
   ```bash
   # Test Redis connection
   redis-cli ping
   
   # Check ads-anomaly-detection installation
   python -c "from ads_plugin import DataIngestionService"
   ```

3. **Performance Issues**
   - Increase `worker_count` in config
   - Tune detector `window_size` and thresholds
   - Enable Redis for distributed processing

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python run_production.py
```

## 📝 API Reference

### Core Classes
- `SignalDetectionPlugin`: Main orchestrator
- `StatisticalAnomalyDetector`: Statistical anomaly detection
- `AdsMemoryInterface`: Integration with ads-anomaly-detection
- `AnomalyEvent`: Core anomaly data structure

### Configuration Schema
See `config.yaml` for complete configuration options and examples.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `python -m pytest`
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**Status**: ✅ **READY FOR PRODUCTION**

The signal detection plugin is fully implemented with:
- ✅ Complete statistical anomaly detection
- ✅ ads-anomaly-detection integration 
- ✅ Configurable data sources and detectors
- ✅ Production-ready deployment options
- ✅ Comprehensive testing and monitoring
- ✅ Docker containerization support
