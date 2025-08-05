import asyncio
import os
import sys
import yaml
import structlog
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.core.models import AnomalyEvent, DataFormat
from src.memory.interface import AdsMemoryInterface

# Set up structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class SignalDetectionPlugin:
    """Main signal detection plugin for ads-anomaly-detection integration"""
    
    def __init__(self, config_path: str, ads_memory_module: Optional[Any] = None):
        self.config_path = config_path
        self.config = self._load_config()
        self.ads_memory_module = ads_memory_module
        
        # Core components
        self.detectors = {}
        self.memory_interface = None
        self.running = False
        
        # Performance tracking
        self.start_time = None
        self.processed_count = 0
        self.anomaly_count = 0
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Apply environment variable overrides
            config = self._apply_env_overrides(config)
            
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            raise
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration"""
        # Common environment overrides
        env_overrides = {
            'REDIS_HOST': ['memory_system', 'config', 'host'],
            'REDIS_PORT': ['memory_system', 'config', 'port'],
            'LOG_LEVEL': ['observability', 'logging', 'level'],
            'MAX_WORKERS': ['pipeline', 'max_workers'],
            'BATCH_SIZE': ['pipeline', 'batch_size'],
            'GPU_ENABLED': ['resource_management', 'gpu', 'enabled']
        }
        
        for env_var, path in env_overrides.items():
            if env_var in os.environ:
                # Navigate to the nested config location
                current = config
                for key in path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # Set the value (with type conversion)
                value = os.environ[env_var]
                if env_var in ['REDIS_PORT', 'MAX_WORKERS', 'BATCH_SIZE']:
                    value = int(value)
                elif env_var in ['GPU_ENABLED']:
                    value = value.lower() in ('true', '1', 'yes', 'on')
                
                current[path[-1]] = value
                logger.info(f"Applied environment override: {env_var}={value}")
        
        return config
    
    async def initialize(self) -> None:
        """Initialize the signal detection plugin"""
        logger.info("Initializing Signal Detection Plugin")
        
        try:
            # Setup ads-anomaly-detection integration
            await self._setup_memory_interface()
            
            # Initialize detectors
            await self._initialize_detectors()
            
            logger.info("Signal Detection Plugin initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize plugin: {e}")
            raise
    
    async def _initialize_detectors(self) -> None:
        """Initialize configured detectors"""
        detector_configs = self.config.get('detectors', {})
        
        for detector_name, detector_config in detector_configs.items():
            if not detector_config.get('enabled', True):
                continue
            
            try:
                if detector_name == 'statistical_detector':
                    from src.detectors.statistical import StatisticalAnomalyDetector
                    detector = StatisticalAnomalyDetector()
                    await detector.initialize(detector_config.get('config', {}))
                    self.detectors[detector_name] = detector
                    logger.info(f"Initialized detector: {detector_name}")
                
                # Add more detector types here as needed
                
            except Exception as e:
                logger.error(f"Failed to initialize detector {detector_name}: {e}")
    
    async def _setup_memory_interface(self) -> None:
        """Setup memory interface for ads-anomaly-detection integration"""
        memory_config = self.config.get('memory_system', {})
        interface_type = memory_config.get('interface', 'direct_call')
        
        try:
            if interface_type == 'direct_call':
                # Try to import and use ads-anomaly-detection directly
                if self.ads_memory_module is None:
                    # Import ads-anomaly-detection ingestion service
                    ads_path = os.path.join(os.path.dirname(__file__), '..', 'ads-anomaly-detection', 'src')
                    if ads_path not in sys.path:
                        sys.path.insert(0, ads_path)
                    
                    try:
                        from ingestion.data_ingestion import DataIngestionService
                        self.ads_memory_module = DataIngestionService()
                        await self.ads_memory_module.initialize()
                        logger.info("Connected to ads-anomaly-detection ingestion service")
                    except ImportError as e:
                        logger.warning(f"Could not import ads-anomaly-detection: {e}")
                        self.ads_memory_module = None
                
                if self.ads_memory_module:
                    self.memory_interface = AdsMemoryInterface(
                        self.ads_memory_module,
                        batch_mode=memory_config.get('config', {}).get('batch_mode', True),
                        max_batch_size=memory_config.get('config', {}).get('max_batch_size', 500)
                    )
                    logger.info("Setup ads-anomaly-detection memory interface")
                else:
                    logger.warning("No ads memory module available, using mock interface")
                    self.memory_interface = MockMemoryInterface()
            
            elif interface_type == 'redis_pubsub':
                # Redis pub/sub integration
                import redis.asyncio as redis
                redis_config = memory_config.get('config', {})
                redis_client = redis.Redis(
                    host=redis_config.get('host', 'localhost'),
                    port=redis_config.get('port', 6379),
                    decode_responses=True
                )
                
                from src.memory.interface import RedisMemoryInterface
                self.memory_interface = RedisMemoryInterface(
                    redis_client,
                    channel=redis_config.get('channel', 'anomaly_events')
                )
                logger.info("Setup Redis memory interface")
            
        except Exception as e:
            logger.error(f"Failed to setup memory interface: {e}")
            # Fallback to mock interface
            self.memory_interface = MockMemoryInterface()
    
    async def run(self) -> None:
        """Run the signal detection plugin"""
        if not self.detectors:
            logger.error("No detectors initialized, cannot run")
            return
        
        self.running = True
        self.start_time = asyncio.get_event_loop().time()
        
        logger.info("Starting Signal Detection Plugin")
        
        try:
            # Start processing tasks
            tasks = []
            max_workers = self.config.get('pipeline', {}).get('max_workers', 4)
            
            for worker_id in range(max_workers):
                task = asyncio.create_task(self._process_worker(worker_id))
                tasks.append(task)
            
            # Wait for all workers
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Error in main processing loop: {e}")
        finally:
            self.running = False
            logger.info("Signal Detection Plugin stopped")
    
    async def _process_worker(self, worker_id: int) -> None:
        """Worker process for signal detection"""
        logger.info(f"Started worker {worker_id}")
        
        # For demo purposes, generate some test data
        # In real implementation, this would read from data sources
        
        import time
        import random
        
        while self.running:
            try:
                # Generate test data
                test_data = {
                    'timestamp': time.time(),
                    'cpu_usage': random.uniform(0, 100),
                    'memory_usage': random.uniform(0, 100),
                    'network_io': random.uniform(0, 1000),
                    'disk_io': random.uniform(0, 500)
                }
                
                # Add some anomalies occasionally
                if random.random() < 0.1:  # 10% chance of anomaly
                    test_data['cpu_usage'] = random.uniform(90, 100)
                
                # Process with all detectors
                for detector_name, detector in self.detectors.items():
                    try:
                        result = await detector.detect(test_data)
                        
                        if result:
                            self.anomaly_count += 1
                            logger.info(f"Anomaly detected by {detector_name}: {result.severity.value}")
                            
                            # Send to ads-anomaly-detection
                            if self.memory_interface:
                                await self.memory_interface.ingest_event(result)
                        
                        self.processed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error in detector {detector_name}: {e}")
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in worker {worker_id}: {e}")
                await asyncio.sleep(1)
    
    async def shutdown(self) -> None:
        """Graceful shutdown"""
        logger.info("Shutting down Signal Detection Plugin")
        
        self.running = False
        
        # Cleanup detectors
        for detector_name, detector in self.detectors.items():
            try:
                await detector.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up detector {detector_name}: {e}")
        
        # Cleanup memory interface
        if self.memory_interface and hasattr(self.memory_interface, 'cleanup'):
            try:
                await self.memory_interface.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up memory interface: {e}")
        
        # Log final stats
        if self.start_time:
            runtime = asyncio.get_event_loop().time() - self.start_time
            logger.info(f"Final stats: {self.processed_count} processed, {self.anomaly_count} anomalies in {runtime:.1f}s")


class MockMemoryInterface:
    """Mock memory interface for testing when ads-anomaly-detection is not available"""
    
    async def ingest_event(self, event: AnomalyEvent) -> None:
        logger.info(f"Mock: Would ingest anomaly {event.event_id} with severity {event.severity.value}")
    
    async def cleanup(self) -> None:
        logger.info("Mock memory interface cleaned up")


async def main():
    """Main entry point"""
    # Setup configuration path
    config_path = os.environ.get('CONFIG_PATH', 'config.yaml')
    
    # Initialize plugin
    plugin = SignalDetectionPlugin(config_path)
    
    try:
        await plugin.initialize()
        await plugin.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await plugin.shutdown()


if __name__ == "__main__":
    asyncio.run(main())