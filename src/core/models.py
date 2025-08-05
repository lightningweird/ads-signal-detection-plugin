from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, List, Union
from datetime import datetime
import uuid
import json


class Severity(Enum):
    """Anomaly severity levels matching ads-anomaly-detection"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DataFormat(Enum):
    """Supported data formats"""
    JSON = "json"
    MSGPACK = "msgpack"
    PROTOBUF = "protobuf"
    AUTO = "auto"


@dataclass
class AnomalyEvent:
    """Core event structure compatible with ads-anomaly-detection"""
    detector_id: str
    timestamp: float
    severity: Severity
    confidence: float
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Additional fields for ads-anomaly-detection compatibility
    anomaly_type: Optional[str] = None
    affected_metrics: List[str] = field(default_factory=list)
    z_scores: Optional[Dict[str, float]] = None
    raw_values: Optional[Dict[str, float]] = None
    predicted_values: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'detector_id': self.detector_id,
            'timestamp': self.timestamp,
            'severity': self.severity.value,
            'confidence': self.confidence,
            'data': self.data,
            'metadata': self.metadata or {},
            'correlation_id': self.correlation_id,
            'event_id': self.event_id,
            'anomaly_type': self.anomaly_type,
            'affected_metrics': self.affected_metrics,
            'z_scores': self.z_scores,
            'raw_values': self.raw_values,
            'predicted_values': self.predicted_values
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnomalyEvent':
        """Create from dictionary"""
        return cls(
            detector_id=data['detector_id'],
            timestamp=data['timestamp'],
            severity=Severity(data['severity']),
            confidence=data['confidence'],
            data=data['data'],
            metadata=data.get('metadata'),
            correlation_id=data.get('correlation_id'),
            event_id=data.get('event_id', str(uuid.uuid4())),
            anomaly_type=data.get('anomaly_type'),
            affected_metrics=data.get('affected_metrics', []),
            z_scores=data.get('z_scores'),
            raw_values=data.get('raw_values'),
            predicted_values=data.get('predicted_values')
        )
    
    def to_ads_format(self) -> Dict[str, Any]:
        """Convert to ads-anomaly-detection format"""
        return {
            'timestamp': datetime.fromtimestamp(self.timestamp),
            'source_id': self.detector_id,
            'values': self.raw_values or self.data,
            'metadata': {
                'detector_id': self.detector_id,
                'confidence': self.confidence,
                'severity': self.severity.value,
                'anomaly_type': self.anomaly_type,
                'affected_metrics': self.affected_metrics,
                'z_scores': self.z_scores,
                'correlation_id': self.correlation_id,
                'event_id': self.event_id,
                **(self.metadata or {})
            }
        }


@dataclass
class DataPoint:
    """Incoming data point structure"""
    source: str
    timestamp: float
    raw_data: bytes
    format: DataFormat = DataFormat.AUTO
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Additional fields for metric tracking
    metrics: Optional[Dict[str, float]] = None
    
    @property
    def size_bytes(self) -> int:
        """Get size of raw data in bytes"""
        return len(self.raw_data)
    
    def extract_metrics(self) -> Dict[str, float]:
        """Extract numeric metrics from the data point"""
        if self.metrics:
            return self.metrics
        
        # Try to parse and extract metrics from raw_data
        try:
            if self.format == DataFormat.JSON or self.format == DataFormat.AUTO:
                parsed = json.loads(self.raw_data.decode('utf-8'))
                if isinstance(parsed, dict):
                    return {k: float(v) for k, v in parsed.items() if isinstance(v, (int, float))}
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            pass
        
        return {}


@dataclass
class DetectorMetrics:
    """Metrics for detector performance"""
    detector_id: str
    processed_count: int = 0
    anomaly_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0
    last_detection: Optional[float] = None
    
    def update_latency(self, latency_ms: float):
        """Update average latency with new measurement"""
        if self.processed_count == 0:
            self.avg_latency_ms = latency_ms
        else:
            # Simple moving average
            self.avg_latency_ms = (self.avg_latency_ms * (self.processed_count - 1) + latency_ms) / self.processed_count


@dataclass
class ResourceRequirements:
    """Resource requirements for detectors"""
    requires_gpu: bool = False
    min_memory_gb: float = 1.0
    preferred_batch_size: int = 1
    is_blocking: bool = False
    max_latency_ms: Optional[float] = None
    
    def validate_system(self, available_resources: Dict[str, Any]) -> bool:
        """Validate if system meets requirements"""
        if self.requires_gpu and not available_resources.get('gpu_available', False):
            return False
        if self.min_memory_gb > available_resources.get('memory_gb', 0):
            return False
        return True


@dataclass
class StreamMetrics:
    """Metrics for stream processing"""
    source: str
    messages_received: int = 0
    messages_processed: int = 0
    messages_dropped: int = 0
    messages_spilled: int = 0
    queue_depth: int = 0
    last_message_time: Optional[float] = None


@dataclass
class BatchResult:
    """Result from batch processing"""
    anomalies: List[AnomalyEvent]
    processed_count: int
    error_count: int
    batch_latency_ms: float