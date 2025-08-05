# Freqtrade Execution Plugin for ads-anomaly-detection

A **minimal, execution-only** Freqtrade strategy plugin that acts as a pure trigger mechanism for the ads-anomaly-detection system. This plugin contains **NO internal trading logic** - all intelligence comes from the external strategy and memory system.

## 🎯 Purpose

This Freqtrade bot is designed to be **the trigger, not the brain**:
- ✅ Receives pre-tagged trading decisions from ads-anomaly-detection
- ✅ Executes trades within Freqtrade's framework  
- ✅ Supports random, test, and confirmed anomaly trades
- ✅ Paper trading mode for safe testing
- ❌ NO internal indicators, filters, or trading logic

## 🏗️ Architecture

```
ads-anomaly-detection System
         ↓ (Redis signals)
Freqtrade Execution Plugin
         ↓ (Market orders)
    Exchange/Paper Trading
```

## 📁 Files Structure

```
freqtrade_execution_plugin/
├── ads_execution_strategy.py    # Minimal Freqtrade strategy (execution only)
├── signal_sender.py             # Interface for sending signals from ads system
├── config.json                  # Freqtrade configuration (paper trading)
├── test_integration.py          # Test script for signal transmission
├── setup.py                     # Setup and installation script
├── start_freqtrade.bat         # Windows convenience script
├── start_freqtrade.ps1         # PowerShell convenience script
└── README.md                   # This file
```

## 🚀 Quick Start

### 1. Setup
```bash
cd signal-detection-plugin/freqtrade_execution_plugin
python setup.py
```

### 2. Start Redis (if not already running)
```bash
docker run -d -p 6379:6379 redis/redis-stack
```

### 3. Test Signal Transmission
```bash
python test_integration.py
```

### 4. Start Freqtrade (in paper trading mode)
```bash
python -m freqtrade trade --config config.json --strategy AdsExecutionStrategy --dry-run
```

## 📡 Signal Format

The plugin expects signals in this Redis format:

```json
{
    "action": "buy|sell|hold",
    "pair": "BTC/USDT", 
    "signal_type": "random|test|anomaly",
    "confidence": 0.95,
    "timestamp": "2025-08-06T00:30:00Z",
    "metadata": {
        "anomaly_severity": "CRITICAL",
        "detector": "statistical_detector", 
        "reason": "spike_detected"
    }
}
```

## 🔗 Integration with ads-anomaly-detection

### From ads-anomaly-detection system:

```python
from freqtrade_execution_plugin.signal_sender import AdsFreqtradeInterface

# Initialize interface
ads_interface = AdsFreqtradeInterface()

# Process anomaly and generate trading signal
anomaly_data = {
    "severity": "CRITICAL",
    "confidence": 0.95,
    "detector": "statistical_detector",
    "affected_metrics": "cpu_usage,memory_usage"
}

ads_interface.process_anomaly_for_trading(anomaly_data)
```

### Direct signal sending:

```python
from freqtrade_execution_plugin.signal_sender import FreqtradeSignalSender

sender = FreqtradeSignalSender()

# Send anomaly-based trading signal
sender.send_anomaly_signal(
    pair="BTC/USDT",
    action="buy", 
    anomaly_severity="HIGH",
    detector="statistical_detector",
    confidence=0.95,
    affected_metrics="cpu,memory,network",
    reason="Critical system anomaly detected"
)
```

## 🧪 Testing

### Interactive Test Menu
```bash
python test_integration.py
```

Options:
1. **Test Signal Transmission** - Basic signal sending
2. **Test ads-anomaly-detection Integration** - Full integration test
3. **Continuous Signal Test** - 60-second continuous testing
4. **Clear All Signals** - Reset pending signals
5. **Show Signal Status** - View current signal queue

### Manual Testing
```python
# Send test signals
sender = FreqtradeSignalSender()
sender.send_test_signal("BTC/USDT", "buy", "manual_test")
sender.send_random_signal("ETH/USDT", "sell")
```

## ⚙️ Configuration

### Freqtrade Config (config.json)
- **Paper Trading**: `"dry_run": true` 
- **Wallet**: $10,000 virtual balance
- **Pairs**: BTC/USDT, ETH/USDT, ADA/USDT, DOT/USDT, SOL/USDT
- **Orders**: Market orders for immediate execution
- **API**: Enabled on localhost:8080

### Strategy Parameters
- **Timeframe**: 1m (minimal for execution)
- **Stoploss**: -10% (safety net, external system controls exits)
- **ROI**: Disabled (external system controls exits)
- **Startup Candles**: 1 (no historical analysis needed)

## 🔧 Customization

### Adding New Trading Pairs
Edit `config.json`:
```json
"pair_whitelist": [
    "BTC/USDT",
    "ETH/USDT", 
    "YOUR/PAIR"
]
```

### Custom Signal Processing
Modify `ads_execution_strategy.py`:
```python
def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
    # Your custom signal processing logic here
    signal = self.get_external_signal(metadata['pair'])
    # ... rest of execution logic
```

### Risk Management
```python
# Custom stoploss via Redis
sender.set_custom_stoploss("BTC/USDT", -0.03)  # 3% stoploss

# In strategy
def custom_stoploss(self, pair: str, trade, current_time: datetime, 
                   current_rate: float, current_profit: float, **kwargs) -> float:
    # External system can control stoploss dynamically
```

## 📊 Monitoring

### Real-time Status
```python
sender = FreqtradeSignalSender()
status = sender.get_signal_status()
print(status)
# {
#   "pending_signals": 2,
#   "active_stoplosses": 1, 
#   "signal_pairs": ["BTC/USDT", "ETH/USDT"],
#   "stoploss_pairs": ["BTC/USDT"]
# }
```

### Freqtrade API
- **Endpoint**: http://localhost:8080
- **Username**: freqtrade
- **Password**: password

### Logs
- Freqtrade logs: Terminal output
- Strategy logs: Include signal reception and execution details
- Redis logs: Use `redis-cli monitor` for real-time signal flow

## 🚨 Safety Features

### Paper Trading
- Default configuration uses dry-run mode
- $10,000 virtual balance for testing
- No real money at risk

### Risk Management
- 10% safety net stoploss (can be overridden by external system)
- Market orders for immediate execution
- Signal expiration (60 seconds)
- Redis connection failure handling

### Error Handling
- Graceful degradation when Redis is unavailable
- Signal validation and type checking
- Comprehensive logging for debugging

## 🔄 Production Deployment

### Switch to Live Trading
1. Update `config.json`:
   ```json
   "dry_run": false
   ```

2. Add exchange credentials:
   ```json
   "exchange": {
       "name": "binance",
       "key": "your-api-key",
       "secret": "your-secret-key"
   }
   ```

3. Adjust stake amounts and risk parameters

### Monitoring Setup
- Enable Telegram notifications
- Set up Prometheus metrics collection
- Configure alerting for failed signals

## 🐛 Troubleshooting

### Common Issues

**Redis Connection Failed**
```bash
# Check Redis is running
docker ps | grep redis

# Start Redis if needed
docker run -d -p 6379:6379 redis/redis-stack
```

**No Signals Received**
```python
# Check signal status
sender = FreqtradeSignalSender()
print(sender.get_signal_status())

# Clear stuck signals
sender.clear_signals()
```

**Strategy Not Loading**
```bash
# Verify strategy file location
ls freqtrade_execution_plugin/ads_execution_strategy.py

# Check Freqtrade can find strategy
python -m freqtrade list-strategies --strategy-path ./freqtrade_execution_plugin/
```

**Import Errors**
```bash
# Install missing dependencies
pip install freqtrade[plot] redis pandas numpy

# Verify installation
python -c "import freqtrade; print('Freqtrade OK')"
```

## 📈 Performance Notes

- **Latency**: ~100ms from signal to order placement
- **Throughput**: Can handle multiple signals per second
- **Memory**: Minimal footprint (~50MB base + Freqtrade overhead)
- **CPU**: Low usage (signal processing is lightweight)

## 🔒 Security

- Redis should be secured in production (authentication, SSL)
- API server has basic authentication
- No sensitive data in strategy code
- Signal expiration prevents stale orders

## 📞 Integration Examples

### From Statistical Detector
```python
# In your ads-anomaly-detection statistical detector
if anomaly_severity == "CRITICAL" and confidence > 0.8:
    ads_interface.process_anomaly_for_trading({
        "severity": anomaly_severity,
        "confidence": confidence,
        "detector": "statistical_detector",
        "affected_metrics": "cpu,memory"
    })
```

### From Memory System
```python 
# Integration with memory interface
def process_memory_anomaly(self, memory_data):
    if self.should_trigger_trade(memory_data):
        self.freqtrade_interface.send_anomaly_signal(
            pair="BTC/USDT",
            action="buy",
            anomaly_severity=memory_data["severity"],
            detector="memory_detector", 
            confidence=memory_data["confidence"],
            affected_metrics="memory_usage",
            reason=f"Memory anomaly: {memory_data['pattern']}"
        )
```

---

## 🎯 Key Principles

1. **Execution Only**: This plugin is purely an execution layer
2. **External Intelligence**: All trading logic comes from ads-anomaly-detection  
3. **Minimal Footprint**: Keep Freqtrade logic as thin as possible
4. **Paper Trading First**: Always test with virtual money
5. **Signal-Driven**: React only to external signals, no internal analysis

This plugin serves as the **trigger mechanism** for your ads-anomaly-detection system's trading decisions. The brain resides in your anomaly detection and memory systems - this is just the reliable execution arm.
