# Signal Detection Plugin for ads-anomaly-detection

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Integration](https://img.shields.io/badge/integrates-ads--anomaly--detection-orange.svg)](https://github.com/lightningweird/ads-anomaly-detection)

A modular, high-performance signal detection plugin designed for seamless integration with the [ads-anomaly-detection](https://github.com/lightningweird/ads-anomaly-detection) system. This plugin provides advanced anomaly detection capabilities with multi-source data ingestion, real-time processing, and intelligent resource management.

## 🌟 Key Features

- **🔗 Direct Integration**: Built specifically for ads-anomaly-detection system
- **📊 Multi-Algorithm Detection**: Statistical, ML-based, and transformer-based detectors
- **🚀 High Performance**: Async processing with batch optimization
- **🔄 Hot-Swappable Components**: Plugin architecture for dynamic loading
- **📈 Advanced Metrics**: Comprehensive monitoring and health checks
- **💾 Memory Integration**: Direct function calls or Redis pub/sub with ads-anomaly-detection
- **🛡️ Robust Error Handling**: Circuit breakers and graceful degradation

## 📋 System Requirements

- **Python**: 3.8+ (tested with 3.12)
- **Memory**: 2GB+ RAM recommended
- **Storage**: 500MB+ free space
- **Dependencies**: ads-anomaly-detection system

## 🛠 Installation

### 1. Prerequisites

First, ensure you have the ads-anomaly-detection system installed and running:

```bash
# Clone ads-anomaly-detection
git clone https://github.com/lightningweird/ads-anomaly-detection.git
cd ads-anomaly-detection

# Install and setup ads-anomaly-detection
python -m venv ads_env
source ads_env/bin/activate  # On Windows: ads_env\Scripts\activate
pip install -r requirements.txt
```

### 2. Install Signal Detection Plugin

```bash
# Clone this plugin
git clone <this-repository-url>
cd signal-detection-plugin

# Use the same virtual environment as ads-anomaly-detection
source ../ads-anomaly-detection/ads_env/bin/activate  # On Windows: ..\ads-anomaly-detection\ads_env\Scripts\activate

# Install plugin dependencies
pip install -r requirements.txt

# Install plugin in development mode
pip install -e .
```

### 3. Configure Integration

```bash
# Copy example configuration
cp config.yaml.example config.yaml

# Edit configuration for your environment
nano config.yaml
```

## ⚙️ Configuration

The plugin uses YAML configuration with environment variable overrides:

```yaml
# Detection Plugins Configuration
detectors:
  statistical_detector:
    enabled: true
    config:
      window_size: 100
      std_dev_threshold: 3.0
      metrics: ["cpu_usage", "memory_usage", "network_io"]

# Memory System Integration
memory_system:
  interface: "direct_call"  # Direct integration with ads-anomaly-detection
  config:
    batch_mode: true
    max_batch_size: 500

# Pipeline Configuration
pipeline:
  max_workers: 4
  batch_size: 100
```

### Environment Variables

```bash
# ads-anomaly-detection integration
ADS_MEMORY_HOST=localhost
ADS_MEMORY_PORT=6379

# Performance tuning
MAX_WORKERS=4
BATCH_SIZE=100
LOG_LEVEL=INFO

# Resource management
GPU_ENABLED=false
MAX_MEMORY_GB=8
```

## 🚀 Usage

### Basic Usage

```python
import asyncio
from src.main import SignalDetectionPlugin

async def main():
    # Initialize plugin with ads-anomaly-detection integration
    plugin = SignalDetectionPlugin('config.yaml')
    
    await plugin.initialize()
    await plugin.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Command Line

```bash
# Run with default configuration
python -m src.main

# Run with custom configuration
CONFIG_PATH=/path/to/config.yaml python -m src.main

# Run with environment overrides
MAX_WORKERS=8 BATCH_SIZE=200 python -m src.main
```

### Docker Deployment

```bash
# Build container
docker build -t signal-detection-plugin .

# Run with ads-anomaly-detection
docker-compose up -d
```

## 🔧 Integration with ads-anomaly-detection

The plugin provides two integration modes:

### 1. Direct Function Calls

```python
# Plugin automatically detects ads-anomaly-detection DataIngestionService
memory_system:
  interface: "direct_call"
  config:
    batch_mode: true
    max_batch_size: 500
```

### 2. Redis Pub/Sub

```python
# For distributed deployments
memory_system:
  interface: "redis_pubsub"
  config:
    host: "localhost"
    port: 6379
    channel: "ads_anomaly_events"
```

## 📊 Detector Types

### Statistical Detector

```python
# Advanced statistical anomaly detection
detectors:
  statistical_detector:
    config:
      window_size: 100
      std_dev_threshold: 3.0
      use_iqr: true        # Interquartile Range
      use_mad: true        # Median Absolute Deviation
      ema_alpha: 0.1       # Exponential Moving Average
```

### ML Detector (Coming Soon)

```python
# Machine learning based detection
detectors:
  ml_isolation_forest:
    config:
      contamination: 0.1
      n_estimators: 100
```

## 📈 Monitoring

### Health Checks

```bash
# Check plugin health
curl http://localhost:8080/health

# Response
{
  "status": "healthy",
  "detectors": {
    "statistical_detector": true
  },
  "memory_interface": true,
  "uptime": 3600
}
```

### Metrics

```bash
# Prometheus metrics
curl http://localhost:9090/metrics

# Key metrics
signal_detector_processed_total
signal_detector_anomalies_total
signal_detector_latency_seconds
signal_detector_errors_total
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Signal Detection Plugin                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Statistical │  │ ML Detector │  │ Transformer │         │
│  │ Detector    │  │             │  │ Detector    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Plugin Manager                              │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌─────────────────────────────────────┐  │
│  │ Memory       │  │     ads-anomaly-detection           │  │
│  │ Interface    │──┤  DataIngestionService               │  │
│  └──────────────┘  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run integration tests
pytest tests/test_integration.py

# Test ads-anomaly-detection integration
pytest tests/test_ads_integration.py
```

## 🔄 Development

### Adding New Detectors

1. Create detector class inheriting from `BaseDetector`:

```python
from src.detectors.base import EnhancedBaseDetector

class MyCustomDetector(EnhancedBaseDetector):
    @property
    def detector_id(self) -> str:
        return "my_custom_detector"
    
    async def _detect(self, data: Any) -> Optional[AnomalyEvent]:
        # Your detection logic here
        pass
```

2. Register in configuration:

```yaml
detectors:
  my_custom_detector:
    enabled: true
    config:
      threshold: 0.8
```

### Plugin Architecture

The plugin supports dynamic loading of:
- **Detectors**: Anomaly detection algorithms
- **Data Sources**: Input stream handlers
- **Memory Interfaces**: Integration backends
- **Metrics Collectors**: Monitoring systems

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Integration Details

### Data Flow

```
Data Input → Statistical Analysis → Anomaly Detection → ads-anomaly-detection Memory System
```

### Event Format

```python
# AnomalyEvent compatible with ads-anomaly-detection
{
    "detector_id": "statistical_detector",
    "timestamp": 1691234567.0,
    "severity": "HIGH",
    "confidence": 0.95,
    "anomaly_type": "statistical_outlier",
    "affected_metrics": ["cpu_usage"],
    "z_scores": {"cpu_usage": 4.2},
    "raw_values": {"cpu_usage": 95.5},
    "predicted_values": {"cpu_usage": 45.0}
}
```

### Performance Characteristics

- **Latency**: <50ms per detection
- **Throughput**: 1000+ events/second
- **Memory Usage**: <2GB typical
- **CPU Usage**: Multi-core aware with worker pools

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: [Wiki](https://github.com/your-repo/wiki)
- **Integration Help**: See [ads-anomaly-detection docs](https://github.com/lightningweird/ads-anomaly-detection)

---

**Ready to detect anomalies with precision and speed! 🚀**