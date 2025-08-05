import numpy as np
import structlog
from collections import deque
from typing import Optional, Dict, Any, List
from scipy import stats

from src.detectors.base import EnhancedBaseDetector
from src.core.models import AnomalyEvent, Severity, ResourceRequirements

logger = structlog.get_logger()


class StatisticalAnomalyDetector(EnhancedBaseDetector):
    """Statistical anomaly detector compatible with ads-anomaly-detection"""
    
    @property
    def detector_id(self) -> str:
        return "statistical_detector"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def detector_type(self) -> str:
        return "statistical"
    
    @property
    def resource_requirements(self) -> ResourceRequirements:
        return ResourceRequirements(
            requires_gpu=False,
            min_memory_gb=0.5,
            preferred_batch_size=50,
            is_blocking=False,
            max_latency_ms=100
        )
    
    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize statistical detector"""
        self.window_size = config.get('window_size', 100)
        self.std_dev_threshold = config.get('std_dev_threshold', 3.0)
        self.min_samples = config.get('min_samples', 10)
        self.metrics = config.get('metrics', [])
        
        # Enhanced configuration for ads-anomaly-detection
        self.use_iqr = config.get('use_iqr', False)
        self.iqr_multiplier = config.get('iqr_multiplier', 1.5)
        self.use_mad = config.get('use_mad', False)  # Median Absolute Deviation
        self.mad_threshold = config.get('mad_threshold', 3.0)
        
        # Sliding windows for each metric
        self.windows = {
            metric: deque(maxlen=self.window_size)
            for metric in self.metrics
        }
        
        # EMA (Exponential Moving Average) state
        self.ema_alpha = config.get('ema_alpha', 0.1)
        self.ema_values = {}
        self.ema_variance = {}
        
        logger.info(f"Statistical detector initialized with {len(self.metrics)} metrics")
    
    async def _detect(self, data: Dict[str, Any]) -> Optional[AnomalyEvent]:
        """Detect statistical anomalies"""
        anomalies = []
        z_scores = {}
        raw_values = {}
        predicted_values = {}
        
        for metric in self.metrics:
            if metric not in data:
                continue
            
            value = float(data[metric])
            raw_values[metric] = value
            
            # Add to sliding window
            self.windows[metric].append(value)
            
            if len(self.windows[metric]) < self.min_samples:
                continue
            
            # Calculate anomaly scores using different methods
            anomaly_info = self._detect_anomaly_for_metric(metric, value)
            
            if anomaly_info:
                anomalies.append(anomaly_info)
                z_scores[metric] = anomaly_info['z_score']
                predicted_values[metric] = anomaly_info['predicted']
        
        # Update baseline statistics
        self._update_baseline_stats()
        
        if anomalies:
            severity = self._calculate_severity(anomalies)
            confidence = self._calculate_confidence(anomalies)
            
            return AnomalyEvent(
                detector_id=self.detector_id,
                timestamp=data.get('timestamp', time.time()),
                severity=severity,
                confidence=confidence,
                data=data,
                anomaly_type="statistical_outlier",
                affected_metrics=list(z_scores.keys()),
                z_scores=z_scores,
                raw_values=raw_values,
                predicted_values=predicted_values,
                metadata={
                    'detection_methods': [a['method'] for a in anomalies],
                    'window_size': self.window_size,
                    'min_samples': self.min_samples
                }
            )
        
        return None
    
    def _detect_anomaly_for_metric(self, metric: str, value: float) -> Optional[Dict[str, Any]]:
        """Detect anomaly for a specific metric using multiple methods"""
        window_data = np.array(self.windows[metric])
        
        # Z-score method
        if self._detect_zscore_anomaly(window_data, value):
            mean_val = np.mean(window_data[:-1])  # Exclude current value
            std_val = np.std(window_data[:-1])
            z_score = abs((value - mean_val) / std_val) if std_val > 0 else 0
            
            return {
                'metric': metric,
                'method': 'zscore',
                'z_score': z_score,
                'threshold': self.std_dev_threshold,
                'predicted': mean_val,
                'actual': value
            }
        
        # IQR method
        if self.use_iqr and self._detect_iqr_anomaly(window_data, value):
            q1, q3 = np.percentile(window_data[:-1], [25, 75])
            iqr = q3 - q1
            median_val = np.median(window_data[:-1])
            
            return {
                'metric': metric,
                'method': 'iqr',
                'z_score': abs(value - median_val) / iqr if iqr > 0 else 0,
                'threshold': self.iqr_multiplier,
                'predicted': median_val,
                'actual': value
            }
        
        # MAD method
        if self.use_mad and self._detect_mad_anomaly(window_data, value):
            median_val = np.median(window_data[:-1])
            mad = np.median(np.abs(window_data[:-1] - median_val))
            mad_score = abs(value - median_val) / mad if mad > 0 else 0
            
            return {
                'metric': metric,
                'method': 'mad',
                'z_score': mad_score,
                'threshold': self.mad_threshold,
                'predicted': median_val,
                'actual': value
            }
        
        return None
    
    def _detect_zscore_anomaly(self, window_data: np.ndarray, value: float) -> bool:
        """Detect anomaly using Z-score method"""
        if len(window_data) < 2:
            return False
        
        mean_val = np.mean(window_data[:-1])
        std_val = np.std(window_data[:-1])
        
        if std_val == 0:
            return False
        
        z_score = abs((value - mean_val) / std_val)
        return z_score > self.std_dev_threshold
    
    def _detect_iqr_anomaly(self, window_data: np.ndarray, value: float) -> bool:
        """Detect anomaly using IQR method"""
        if len(window_data) < 4:  # Need at least 4 points for quartiles
            return False
        
        q1, q3 = np.percentile(window_data[:-1], [25, 75])
        iqr = q3 - q1
        
        if iqr == 0:
            return False
        
        lower_bound = q1 - self.iqr_multiplier * iqr
        upper_bound = q3 + self.iqr_multiplier * iqr
        
        return value < lower_bound or value > upper_bound
    
    def _detect_mad_anomaly(self, window_data: np.ndarray, value: float) -> bool:
        """Detect anomaly using Median Absolute Deviation method"""
        if len(window_data) < 3:
            return False
        
        median_val = np.median(window_data[:-1])
        mad = np.median(np.abs(window_data[:-1] - median_val))
        
        if mad == 0:
            return False
        
        mad_score = abs(value - median_val) / mad
        return mad_score > self.mad_threshold
    
    def _calculate_severity(self, anomalies: List[Dict]) -> Severity:
        """Calculate severity based on z-scores"""
        max_z_score = max(a['z_score'] for a in anomalies)
        
        if max_z_score > 5:
            return Severity.CRITICAL
        elif max_z_score > 4:
            return Severity.HIGH
        elif max_z_score > 3.5:
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    def _calculate_confidence(self, anomalies: List[Dict]) -> float:
        """Calculate confidence based on multiple factors"""
        # Base confidence on z-score
        max_z_score = max(a['z_score'] for a in anomalies)
        base_confidence = min(max_z_score / 5.0, 1.0)  # Normalize to 0-1
        
        # Boost confidence if multiple methods agree
        if len(anomalies) > 1:
            base_confidence = min(base_confidence * 1.2, 1.0)
        
        # Reduce confidence if we have few samples
        sample_factor = min(len(self.windows[anomalies[0]['metric']]) / self.window_size, 1.0)
        
        return base_confidence * sample_factor
    
    def _update_baseline_stats(self):
        """Update baseline statistics for each metric"""
        for metric, window in self.windows.items():
            if len(window) >= self.min_samples:
                data = np.array(window)
                self.update_baseline_stats(metric, {
                    'mean': float(np.mean(data)),
                    'std': float(np.std(data)),
                    'min': float(np.min(data)),
                    'max': float(np.max(data)),
                    'median': float(np.median(data)),
                    'count': len(data)
                })
    
    def get_supported_metrics(self) -> List[str]:
        """Return list of metrics this detector can process"""
        return self.metrics
    
    async def update_model(self, model_data: Any) -> None:
        """Update statistical model with new baseline data"""
        if isinstance(model_data, dict) and 'baseline_stats' in model_data:
            for metric, stats in model_data['baseline_stats'].items():
                if metric in self.metrics:
                    self.update_baseline_stats(metric, stats)
                    logger.info(f"Updated baseline stats for metric {metric}")


import time