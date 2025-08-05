import asyncio
import structlog
from typing import List, Any, Optional, Dict
from datetime import datetime

from src.core.models import AnomalyEvent
from src.core.interfaces import MemorySystemInterface

logger = structlog.get_logger()


class AdsMemoryInterface(MemorySystemInterface):
    """Direct integration with ads-anomaly-detection memory system"""
    
    def __init__(self, 
                 ads_ingestion_service: Any,
                 batch_mode: bool = True,
                 max_batch_size: int = 500,
                 flush_interval: float = 5.0):
        """
        Initialize with ads-anomaly-detection ingestion service
        
        Args:
            ads_ingestion_service: Instance of DataIngestionService from ads-anomaly-detection
            batch_mode: Whether to batch anomalies before sending
            max_batch_size: Maximum batch size before forcing flush
            flush_interval: Maximum time between flushes (seconds)
        """
        self.ingestion_service = ads_ingestion_service
        self.batch_mode = batch_mode
        self.max_batch_size = max_batch_size
        self.flush_interval = flush_interval
        
        self._batch_buffer: List[Dict[str, Any]] = []
        self._last_flush = asyncio.get_event_loop().time()
        self._flush_task: Optional[asyncio.Task] = None
        
        if batch_mode:
            self._flush_task = asyncio.create_task(self._periodic_flush())
    
    async def ingest_anomaly(self, anomaly: Dict[str, Any]) -> None:
        """Ingest single anomaly into ads-anomaly-detection system"""
        if self.batch_mode:
            self._batch_buffer.append(anomaly)
            
            # Check if we should flush immediately
            if len(self._batch_buffer) >= self.max_batch_size:
                await self._flush_batch()
        else:
            # Send immediately
            await self._send_to_ads(anomaly)
    
    async def ingest_anomalies(self, anomalies: List[Dict[str, Any]]) -> None:
        """Ingest batch of anomalies into ads-anomaly-detection system"""
        if self.batch_mode:
            self._batch_buffer.extend(anomalies)
            
            # Check if we should flush
            if len(self._batch_buffer) >= self.max_batch_size:
                await self._flush_batch()
        else:
            # Send all immediately
            for anomaly in anomalies:
                await self._send_to_ads(anomaly)
    
    async def ingest_event(self, event: AnomalyEvent) -> None:
        """Ingest AnomalyEvent into ads-anomaly-detection system"""
        ads_format = self._format_event_for_ads(event)
        await self.ingest_anomaly(ads_format)
    
    async def ingest_events(self, events: List[AnomalyEvent]) -> None:
        """Ingest batch of AnomalyEvents into ads-anomaly-detection system"""
        ads_events = [self._format_event_for_ads(event) for event in events]
        await self.ingest_anomalies(ads_events)
    
    async def query_recent(self, duration_seconds: int) -> List[Dict[str, Any]]:
        """Query recent anomalies from ads-anomaly-detection system"""
        # This would typically query the ads memory system
        # For now, return empty list as we'd need access to the memory components
        logger.warning("query_recent not fully implemented - would need access to ads memory system")
        return []
    
    async def get_baseline_stats(self, metric: str, window_seconds: int) -> Dict[str, float]:
        """Get baseline statistics for a metric from ads-anomaly-detection"""
        # This would query the ads statistical components
        logger.warning("get_baseline_stats not fully implemented - would need access to ads statistical components")
        return {"mean": 0.0, "std": 1.0, "min": 0.0, "max": 1.0}
    
    def _format_event_for_ads(self, event: AnomalyEvent) -> Dict[str, Any]:
        """Format AnomalyEvent for ads-anomaly-detection DataPoint format"""
        return {
            'timestamp': datetime.fromtimestamp(event.timestamp),
            'source_id': event.detector_id,
            'values': event.raw_values or event.data,
            'metadata': {
                'detector_id': event.detector_id,
                'confidence': event.confidence,
                'severity': event.severity.value,
                'anomaly_type': event.anomaly_type,
                'affected_metrics': event.affected_metrics,
                'z_scores': event.z_scores,
                'correlation_id': event.correlation_id,
                'event_id': event.event_id,
                **(event.metadata or {})
            }
        }
    
    async def _flush_batch(self) -> None:
        """Flush buffered anomalies to ads-anomaly-detection system"""
        if not self._batch_buffer:
            return
        
        try:
            batch_to_send = self._batch_buffer.copy()
            self._batch_buffer.clear()
            self._last_flush = asyncio.get_event_loop().time()
            
            # Send batch to ads-anomaly-detection
            await self._send_batch_to_ads(batch_to_send)
            
            logger.info(f"Flushed {len(batch_to_send)} anomalies to ads-anomaly-detection")
            
        except Exception as e:
            logger.error(f"Failed to flush batch to ads-anomaly-detection: {e}")
            # Re-add failed items to buffer for retry
            self._batch_buffer.extend(batch_to_send)
    
    async def _send_to_ads(self, anomaly: Dict[str, Any]) -> None:
        """Send single anomaly to ads-anomaly-detection system"""
        try:
            # For now, we'll use a direct function call approach
            # The ads ingestion service should have an ingest method that accepts our anomaly data
            
            # Try to detect the correct function name for ads ingestion
            if hasattr(self.ingestion_service, 'ingest'):
                result = await self.ingestion_service.ingest(anomaly)
            elif hasattr(self.ingestion_service, 'store_anomaly'):
                result = await self.ingestion_service.store_anomaly(anomaly)
            elif hasattr(self.ingestion_service, 'ingest_anomaly'):
                result = await self.ingestion_service.ingest_anomaly(anomaly)
            else:
                # Fallback - try to call the object directly if it's callable
                result = await self.ingestion_service(anomaly)
            
            logger.debug(f"Sent anomaly to ads-anomaly-detection: {result}")
            
        except Exception as e:
            logger.error(f"Failed to send anomaly to ads-anomaly-detection: {e}")
            raise
    
    async def _send_batch_to_ads(self, batch: List[Dict[str, Any]]) -> None:
        """Send batch of anomalies to ads-anomaly-detection system"""
        for anomaly in batch:
            await self._send_to_ads(anomaly)
    
    async def _periodic_flush(self) -> None:
        """Periodically flush batched anomalies"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                
                current_time = asyncio.get_event_loop().time()
                if (current_time - self._last_flush) >= self.flush_interval and self._batch_buffer:
                    await self._flush_batch()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")
    
    async def flush(self) -> None:
        """Force flush any buffered anomalies"""
        if self._batch_buffer:
            await self._flush_batch()
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Final flush
        await self.flush()
        
        logger.info("AdsMemoryInterface cleaned up")


class RedisMemoryInterface(MemorySystemInterface):
    """Redis-based memory interface for ads-anomaly-detection compatibility"""
    
    def __init__(self, redis_client: Any, channel: str = "anomaly_events"):
        """
        Initialize with Redis client for pub/sub integration
        
        Args:
            redis_client: Redis client instance
            channel: Redis channel for publishing anomaly events
        """
        self.redis = redis_client
        self.channel = channel
    
    async def ingest_anomaly(self, anomaly: Dict[str, Any]) -> None:
        """Publish anomaly to Redis channel for ads-anomaly-detection consumption"""
        try:
            import json
            message = json.dumps(anomaly, default=str)
            await self.redis.publish(self.channel, message)
            logger.debug(f"Published anomaly to Redis channel {self.channel}")
        except Exception as e:
            logger.error(f"Failed to publish anomaly to Redis: {e}")
            raise
    
    async def ingest_anomalies(self, anomalies: List[Dict[str, Any]]) -> None:
        """Publish batch of anomalies to Redis channel"""
        for anomaly in anomalies:
            await self.ingest_anomaly(anomaly)
    
    async def ingest_event(self, event: AnomalyEvent) -> None:
        """Ingest AnomalyEvent into Redis"""
        ads_format = self._format_event_for_ads(event)
        await self.ingest_anomaly(ads_format)
    
    def _format_event_for_ads(self, event: AnomalyEvent) -> Dict[str, Any]:
        """Format AnomalyEvent for ads-anomaly-detection"""
        return {
            'timestamp': event.timestamp,
            'source_id': event.detector_id,
            'values': event.raw_values or event.data,
            'metadata': {
                'detector_id': event.detector_id,
                'confidence': event.confidence,
                'severity': event.severity.value,
                'anomaly_type': event.anomaly_type,
                'affected_metrics': event.affected_metrics,
                'z_scores': event.z_scores,
                'correlation_id': event.correlation_id,
                'event_id': event.event_id,
                **(event.metadata or {})
            }
        }
    
    async def query_recent(self, duration_seconds: int) -> List[Dict[str, Any]]:
        """Query recent anomalies from Redis (implementation depends on ads setup)"""
        logger.warning("query_recent not implemented for Redis interface")
        return []
    
    async def get_baseline_stats(self, metric: str, window_seconds: int) -> Dict[str, float]:
        """Get baseline statistics from Redis (implementation depends on ads setup)"""
        logger.warning("get_baseline_stats not implemented for Redis interface")
        return {"mean": 0.0, "std": 1.0, "min": 0.0, "max": 1.0}
    
    async def cleanup(self) -> None:
        """Clean up Redis connections"""
        try:
            await self.redis.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")