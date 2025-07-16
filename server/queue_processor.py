"""
Message queue processor with intentional delays for incident simulation
"""

import asyncio
import time
import psutil
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import json

from config import ServerConfig, IncidentSimulationConfig
from models import InternalOrderbook, HeartbeatMessage
from utils.logger import setup_logger

logger = setup_logger(__name__)

class MessageQueueProcessor:
    """Process orderbook messages with configurable delays for incident simulation"""
    
    def __init__(self):
        self.queue = asyncio.Queue(maxsize=ServerConfig.MAX_QUEUE_SIZE)
        self.is_running = False
        self.total_messages_processed = 0
        self.total_messages_received = 0
        self.current_scenario = ServerConfig.INITIAL_SCENARIO
        self.processing_delay_ms = ServerConfig.PROCESSING_DELAY_MS
        self.memory_threshold_mb = ServerConfig.MEMORY_THRESHOLD_MB
        self.incident_triggered = False
        self.start_time = time.time()
        
        # Background tasks
        self.background_tasks = []
        
        # Callbacks
        self.on_orderbook_processed: Optional[Callable] = None
        self.on_heartbeat: Optional[Callable] = None
        self.on_incident_alert: Optional[Callable] = None
        
    async def start(self):
        """Start the queue processor"""
        self.is_running = True
        self.start_time = time.time()
        logger.info("Message queue processor started")
        
        # Start background tasks
        self.background_tasks = [
            asyncio.create_task(self._process_queue()),
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._memory_monitor())
        ]
    
    async def stop(self):
        """Stop the queue processor"""
        self.is_running = False
        logger.info("Message queue processor stopping...")
        
        # Cancel all background tasks
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.background_tasks.clear()
        logger.info("Message queue processor stopped")
    
    async def add_orderbook(self, orderbook: InternalOrderbook):
        """Add an orderbook update to the queue"""
        try:
            if self.queue.full():
                logger.warning("Queue is full, dropping oldest message")
                try:
                    self.queue.get_nowait()  # Remove oldest message
                except asyncio.QueueEmpty:
                    pass
            
            await self.queue.put(orderbook)
            self.total_messages_received += 1
            
            # Log queue status periodically
            if self.total_messages_received % 100 == 0:
                logger.info(f"Queue status: {self.queue.qsize()}/{ServerConfig.MAX_QUEUE_SIZE} messages")
                
        except Exception as e:
            logger.error(f"Error adding orderbook to queue: {e}")
    
    async def _process_queue(self):
        """Process messages from the queue with intentional delays"""
        while self.is_running:
            try:
                # Get message from queue
                orderbook = await self.queue.get()
                
                # Simulate processing delay (this is the "bad code" for incident simulation)
                processing_start = time.time()
                
                # Get delay for current scenario
                delay_ms = self._get_processing_delay()
                await asyncio.sleep(delay_ms / 1000.0)  # Convert to seconds
                
                processing_time = (time.time() - processing_start) * 1000  # Convert to ms
                
                # Process the orderbook (simulate some work)
                await self._process_orderbook(orderbook, processing_time)
                
                # Mark task as done
                self.queue.task_done()
                self.total_messages_processed += 1
                
                # Log processing metrics periodically
                if self.total_messages_processed % 50 == 0:
                    await self._log_processing_metrics()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing queue message: {e}")
    
    async def _process_orderbook(self, orderbook: InternalOrderbook, processing_time_ms: float):
        """Process a single orderbook update"""
        try:
            # Simulate some processing work
            processed_data = orderbook.to_dict()
            
            # Add processing metadata
            processed_data['processing_time_ms'] = processing_time_ms
            processed_data['queue_position'] = self.queue.qsize()
            
            # Log the processed orderbook
            logger.info(f"Processed orderbook {orderbook.sequence_id} in {processing_time_ms:.2f}ms")
            
            # Call callback if registered
            if self.on_orderbook_processed:
                await self.on_orderbook_processed(processed_data)
                
        except Exception as e:
            logger.error(f"Error processing orderbook {orderbook.sequence_id}: {e}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self.is_running:
            try:
                heartbeat = await self._create_heartbeat()
                
                # Call heartbeat callback if registered
                if self.on_heartbeat:
                    await self.on_heartbeat(heartbeat)
                
                # Wait for next heartbeat
                await asyncio.sleep(ServerConfig.HEARTBEAT_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(1)  # Brief pause on error
    
    async def _memory_monitor(self):
        """Monitor memory usage for incident simulation"""
        while self.is_running:
            try:
                memory_usage = self._get_memory_usage()
                
                # Check if memory threshold exceeded
                if memory_usage > self.memory_threshold_mb and not self.incident_triggered:
                    await self._trigger_incident("memory_threshold_exceeded", {
                        "memory_usage_mb": memory_usage,
                        "threshold_mb": self.memory_threshold_mb,
                        "queue_size": self.queue.qsize()
                    })
                
                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in memory monitor: {e}")
    
    async def _trigger_incident(self, incident_type: str, details: Dict[str, Any]):
        """Trigger an incident simulation"""
        self.incident_triggered = True
        
        incident_data = {
            "type": incident_type,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "scenario": self.current_scenario,
            "uptime_seconds": time.time() - self.start_time
        }
        
        logger.warning(f"INCIDENT TRIGGERED: {incident_type}", extra=incident_data)
        
        # Call incident callback if registered
        if self.on_incident_alert:
            await self.on_incident_alert(incident_data)
        
        # Simulate graceful shutdown delay
        logger.info(f"Graceful shutdown in {ServerConfig.GRACEFUL_SHUTDOWN_DELAY} seconds...")
        await asyncio.sleep(ServerConfig.GRACEFUL_SHUTDOWN_DELAY)
        
        # Stop the processor
        await self.stop()
    
    async def _create_heartbeat(self) -> HeartbeatMessage:
        """Create a heartbeat message with current server status"""
        memory_usage = self._get_memory_usage()
        
        return HeartbeatMessage(
            timestamp=datetime.utcnow(),
            server_status="healthy" if not self.incident_triggered else "degraded",
            queue_size=self.queue.qsize(),
            memory_usage_mb=memory_usage,
            active_clients=0,  # Will be updated by connection manager
            current_scenario=self.current_scenario
        )
    
    def _heartbeat_to_dict(self, heartbeat: HeartbeatMessage) -> dict:
        """Convert heartbeat to JSON-serializable dictionary"""
        return {
            "timestamp": heartbeat.timestamp.isoformat(),
            "server_status": heartbeat.server_status,
            "queue_size": heartbeat.queue_size,
            "memory_usage_mb": heartbeat.memory_usage_mb,
            "active_clients": heartbeat.active_clients,
            "current_scenario": heartbeat.current_scenario
        }
    
    def _get_processing_delay(self) -> int:
        """Get processing delay for current scenario"""
        delays = IncidentSimulationConfig.get_processing_delays()
        return delays.get(self.current_scenario, ServerConfig.PROCESSING_DELAY_MS)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # Convert to MB
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return 0.0
    
    async def _log_processing_metrics(self):
        """Log processing performance metrics"""
        uptime = time.time() - self.start_time
        processing_rate = self.total_messages_processed / uptime if uptime > 0 else 0
        
        metrics = {
            "uptime_seconds": uptime,
            "total_messages_processed": self.total_messages_processed,
            "total_messages_received": self.total_messages_received,
            "queue_size": self.queue.qsize(),
            "processing_rate_per_sec": processing_rate,
            "memory_usage_mb": self._get_memory_usage(),
            "current_scenario": self.current_scenario,
            "processing_delay_ms": self._get_processing_delay()
        }
        
        logger.info("Processing metrics", extra=metrics)
    
    def switch_scenario(self, scenario_name: str):
        """Switch to a different scenario"""
        old_scenario = self.current_scenario
        self.current_scenario = scenario_name
        
        # Update processing delay for new scenario
        delays = IncidentSimulationConfig.get_processing_delays()
        self.processing_delay_ms = delays.get(scenario_name, ServerConfig.PROCESSING_DELAY_MS)
        
        logger.info(f"Switched scenario from '{old_scenario}' to '{scenario_name}' (delay: {self.processing_delay_ms}ms)")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current processor status"""
        uptime = time.time() - self.start_time
        processing_rate = self.total_messages_processed / uptime if uptime > 0 else 0
        
        return {
            "is_running": self.is_running,
            "uptime_seconds": uptime,
            "total_messages_processed": self.total_messages_processed,
            "total_messages_received": self.total_messages_received,
            "queue_size": self.queue.qsize(),
            "queue_max_size": ServerConfig.MAX_QUEUE_SIZE,
            "processing_rate_per_sec": processing_rate,
            "memory_usage_mb": self._get_memory_usage(),
            "memory_threshold_mb": self.memory_threshold_mb,
            "current_scenario": self.current_scenario,
            "processing_delay_ms": self._get_processing_delay(),
            "incident_triggered": self.incident_triggered
        }
    
    def set_callbacks(self, 
                     on_orderbook_processed: Optional[Callable] = None,
                     on_heartbeat: Optional[Callable] = None,
                     on_incident_alert: Optional[Callable] = None):
        """Set callback functions for events"""
        self.on_orderbook_processed = on_orderbook_processed
        self.on_heartbeat = on_heartbeat
        self.on_incident_alert = on_incident_alert 