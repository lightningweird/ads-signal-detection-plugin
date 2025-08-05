import asyncio
import time
import structlog
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

from src.core.interfaces import BaseDetector
from src.core.models import AnomalyEvent, ResourceRequirements, DetectorMetrics

logger = structlog.get_logger()


class EnhancedBaseDetector(BaseDetector):
    """Enhanced base detector with metrics and ads-anomaly-detection integration"""
    
    def __init__(self):
        self._initialized = False
        self._config = {}
        self._metrics = DetectorMetrics(detector_id=self.detector_id)
        self._baseline_stats = {}
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize detector with configuration"""
        self._config = config
        await self._initialize(config)
        self._initialized = True
        logger.info(f"Initialized detector: {self.detector_id}")
    
    @abstractmethod
    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Detector-specific initialization"""
        pass
    
    async def detect(self, data: Any) -> Optional[AnomalyEvent]:
        """Detect anomalies with metrics tracking"""
        if not self._initialized:
            raise RuntimeError(f"Detector {self.detector_id} not initialized")
        
        start_time = time.time()
        self._metrics.processed_count += 1
        
        try:
            # Preprocess data
            preprocessed_data = await self._preprocess_data(data)
            
            # Run detection
            result = await self._detect(preprocessed_data)
            
            # Postprocess result
            if result:
                result = await self._postprocess_result(result, data)
                self._metrics.anomaly_count += 1
                self._metrics.last_detection = time.time()
            
            # Update latency
            latency_ms = (time.time() - start_time) * 1000
            self._metrics.update_latency(latency_ms)
            
            return result
            
        except Exception as e:
            self._metrics.error_count += 1
            logger.error(
                f"Detection error in {self.detector_id}",
                error=str(e),
                data_sample=str(data)[:100]
            )
            raise
    
    async def _preprocess_data(self, data: Any) -> Any:
        """Preprocess data before detection - override if needed"""
        return data
    
    async def _postprocess_result(self, result: AnomalyEvent, original_data: Any) -> AnomalyEvent:
        """Postprocess detection result - override if needed"""
        return result
    
    @abstractmethod
    async def _detect(self, data: Any) -> Optional[AnomalyEvent]:
        """Detector-specific detection logic"""
        pass
    
    async def detect_batch(self, data_batch: List[Any]) -> List[AnomalyEvent]:
        """Process batch of data - override for efficiency"""
        results = []
        for data in data_batch:
            result = await self.detect(data)
            if result:
                results.append(result)
        return results
    
    async def health_check(self) -> bool:
        """Default health check implementation"""
        if not self._initialized:
            return False
        
        # Generate test data and try detection
        try:
            test_data = self._generate_test_data()
            if test_data is not None:
                await self._detect(test_data)
            return True
        except Exception as e:
            logger.warning(f"Health check failed for {self.detector_id}: {e}")
            return False
    
    def _generate_test_data(self) -> Optional[Any]:
        """Generate test data for health check - override if needed"""
        return {"test": 1.0, "value": 0.5}
    
    def get_metrics(self) -> DetectorMetrics:
        """Get detector metrics"""
        return self._metrics
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        await self._cleanup()
        self._initialized = False
        logger.info(f"Cleaned up detector: {self.detector_id}")
    
    async def _cleanup(self) -> None:
        """Override for detector-specific cleanup"""
        pass
    
    def get_baseline_stats(self, metric: str) -> Dict[str, float]:
        """Get baseline statistics for a metric"""
        return self._baseline_stats.get(metric, {"mean": 0.0, "std": 1.0})
    
    def update_baseline_stats(self, metric: str, stats: Dict[str, float]):
        """Update baseline statistics for a metric"""
        self._baseline_stats[metric] = stats


class ProcessPoolDetector(BaseDetector):
    """Wrapper for CPU-intensive detectors using process pool"""
    
    def __init__(self, detector: BaseDetector, executor: ProcessPoolExecutor):
        self.detector = detector
        self.executor = executor
        self._loop = asyncio.get_event_loop()
    
    @property
    def detector_id(self) -> str:
        return f"process_pool_{self.detector.detector_id}"
    
    @property
    def version(self) -> str:
        return self.detector.version
    
    @property
    def detector_type(self) -> str:
        return f"process_pool_{self.detector.detector_type}"
    
    @property
    def resource_requirements(self) -> ResourceRequirements:
        reqs = self.detector.resource_requirements
        reqs.is_blocking = True  # Process pool operations are blocking
        return reqs
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the wrapped detector"""
        # Initialize in the process pool
        await self._loop.run_in_executor(
            self.executor, 
            lambda: asyncio.run(self.detector.initialize(config))
        )
    
    async def detect(self, data: Any) -> Optional[AnomalyEvent]:
        """Run detection in process pool"""
        return await self._loop.run_in_executor(
            self.executor, 
            self._detect_sync, 
            data
        )
    
    def _detect_sync(self, data: Any) -> Optional[AnomalyEvent]:
        """Synchronous wrapper for detection"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.detector.detect(data))
        finally:
            loop.close()
    
    async def health_check(self) -> bool:
        """Run health check in process pool"""
        return await self._loop.run_in_executor(
            self.executor,
            lambda: asyncio.run(self.detector.health_check())
        )
    
    async def cleanup(self) -> None:
        """Cleanup the wrapped detector"""
        await self._loop.run_in_executor(
            self.executor,
            lambda: asyncio.run(self.detector.cleanup())
        )


class ThreadPoolDetector(BaseDetector):
    """Wrapper for IO-intensive detectors using thread pool"""
    
    def __init__(self, detector: BaseDetector, executor: ThreadPoolExecutor):
        self.detector = detector
        self.executor = executor
        self._loop = asyncio.get_event_loop()
    
    @property
    def detector_id(self) -> str:
        return f"thread_pool_{self.detector.detector_id}"
    
    @property
    def version(self) -> str:
        return self.detector.version
    
    @property
    def detector_type(self) -> str:
        return f"thread_pool_{self.detector.detector_type}"
    
    @property
    def resource_requirements(self) -> ResourceRequirements:
        return self.detector.resource_requirements
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the wrapped detector"""
        await self._loop.run_in_executor(
            self.executor,
            lambda: asyncio.run(self.detector.initialize(config))
        )
    
    async def detect(self, data: Any) -> Optional[AnomalyEvent]:
        """Run detection in thread pool"""
        return await self._loop.run_in_executor(
            self.executor,
            lambda: asyncio.run(self.detector.detect(data))
        )
    
    async def health_check(self) -> bool:
        """Run health check in thread pool"""
        return await self._loop.run_in_executor(
            self.executor,
            lambda: asyncio.run(self.detector.health_check())
        )
    
    async def cleanup(self) -> None:
        """Cleanup the wrapped detector"""
        await self._loop.run_in_executor(
            self.executor,
            lambda: asyncio.run(self.detector.cleanup())
        )


class BatchOptimizedDetector(EnhancedBaseDetector):
    """Base class for detectors that are optimized for batch processing"""
    
    def __init__(self, preferred_batch_size: int = 100):
        super().__init__()
        self.preferred_batch_size = preferred_batch_size
    
    @property
    def resource_requirements(self) -> ResourceRequirements:
        reqs = super().resource_requirements
        reqs.preferred_batch_size = self.preferred_batch_size
        return reqs
    
    async def detect_batch(self, data_batch: List[Any]) -> List[AnomalyEvent]:
        """Optimized batch processing - override this method"""
        if len(data_batch) <= self.preferred_batch_size:
            return await self._detect_batch_optimized(data_batch)
        
        # Split large batches into smaller chunks
        results = []
        for i in range(0, len(data_batch), self.preferred_batch_size):
            chunk = data_batch[i:i + self.preferred_batch_size]
            chunk_results = await self._detect_batch_optimized(chunk)
            results.extend(chunk_results)
        
        return results
    
    @abstractmethod
    async def _detect_batch_optimized(self, data_batch: List[Any]) -> List[AnomalyEvent]:
        """Optimized batch detection - implement in subclass"""
        pass