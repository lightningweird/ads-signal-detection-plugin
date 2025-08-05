from abc import ABC, abstractmethod
from typing import AsyncIterator, Protocol, runtime_checkable, Dict, Any, Optional, List, Union

from src.core.models import AnomalyEvent, DataPoint, ResourceRequirements


class BaseDetector(ABC):
    """Abstract base class for all anomaly detectors compatible with ads-anomaly-detection"""
    
    @property
    @abstractmethod
    def detector_id(self) -> str:
        """Unique detector identifier"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Detector version"""
        pass
    
    @property
    def detector_type(self) -> str:
        """Type of detector for categorization"""
        return "generic"
    
    @property
    def resource_requirements(self) -> ResourceRequirements:
        """Resource requirements for this detector"""
        return ResourceRequirements()
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize detector with configuration"""
        pass
    
    @abstractmethod
    async def detect(self, data: Any) -> Optional[AnomalyEvent]:
        """Detect anomalies in single data point"""
        pass
    
    async def detect_batch(self, data_batch: List[Any]) -> List[AnomalyEvent]:
        """Process batch of data - override for efficiency"""
        results = []
        for data in data_batch:
            result = await self.detect(data)
            if result:
                results.append(result)
        return results
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if detector is healthy"""
        pass
    
    async def cleanup(self) -> None:
        """Clean up resources - override if needed"""
        pass
    
    def get_supported_metrics(self) -> List[str]:
        """Return list of metrics this detector can process"""
        return []
    
    async def update_model(self, model_data: Any) -> None:
        """Update detector model with new data"""
        pass


@runtime_checkable
class DataSource(Protocol):
    """Protocol for all data sources"""
    
    async def connect(self) -> None:
        """Establish connection to data source"""
        ...
    
    async def disconnect(self) -> None:
        """Close connection to data source"""
        ...
    
    def stream(self) -> AsyncIterator[bytes]:
        """Stream data from source"""
        ...
    
    @property
    def name(self) -> str:
        """Data source name"""
        ...
    
    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        ...


@runtime_checkable
class Deserializer(Protocol):
    """Protocol for data deserializers"""
    
    async def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to Python object"""
        ...
    
    def can_deserialize(self, data: bytes) -> bool:
        """Check if this deserializer can handle the data"""
        ...


@runtime_checkable
class MemorySystemInterface(Protocol):
    """Protocol for ads-anomaly-detection memory system integration"""
    
    async def ingest_anomaly(self, anomaly: Dict[str, Any]) -> None:
        """Ingest single anomaly into memory system"""
        ...
    
    async def ingest_anomalies(self, anomalies: List[Dict[str, Any]]) -> None:
        """Ingest batch of anomalies into memory system"""
        ...
    
    async def query_recent(self, duration_seconds: int) -> List[Dict[str, Any]]:
        """Query recent anomalies from memory system"""
        ...
    
    async def get_baseline_stats(self, metric: str, window_seconds: int) -> Dict[str, float]:
        """Get baseline statistics for a metric"""
        ...


class DiskSpillBuffer(ABC):
    """Abstract base for disk spillover buffer"""
    
    @abstractmethod
    async def write(self, data: bytes) -> str:
        """Write data to disk buffer, return identifier"""
        pass
    
    @abstractmethod
    async def read(self, identifier: str) -> bytes:
        """Read data from disk buffer"""
        pass
    
    @abstractmethod
    async def delete(self, identifier: str) -> None:
        """Delete data from disk buffer"""
        pass
    
    @abstractmethod
    async def list_pending(self) -> List[str]:
        """List pending buffer identifiers"""
        pass
    
    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Clean up expired buffer entries, return count"""
        pass


class MetricsCollector(ABC):
    """Abstract base for metrics collection"""
    
    @abstractmethod
    async def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a metric value"""
        pass
    
    @abstractmethod
    async def increment_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric"""
        pass
    
    @abstractmethod
    async def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram value (for latency, etc.)"""
        pass
    
    @abstractmethod
    async def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        pass
    
    @abstractmethod
    async def reset(self) -> None:
        """Reset all metrics"""
        pass


@runtime_checkable
class ModelProvider(Protocol):
    """Protocol for ML model providers"""
    
    async def load_model(self, model_id: str) -> Any:
        """Load a model by ID"""
        ...
    
    async def save_model(self, model_id: str, model: Any) -> None:
        """Save a model with ID"""
        ...
    
    async def list_models(self) -> List[str]:
        """List available model IDs"""
        ...