"""
Logging configuration for MarketDataPublisher server
"""

import logging
import sys
from datetime import datetime
from pythonjsonlogger import jsonlogger
from config import ServerConfig

def setup_logger(name: str) -> logging.Logger:
    """Setup a logger with JSON formatting"""
    
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, ServerConfig.LOG_LEVEL.upper()))
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Create JSON formatter
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger

def log_orderbook_update(logger: logging.Logger, orderbook_data: dict, processing_time_ms: float = None):
    """Log orderbook update with structured data"""
    log_data = {
        "event": "orderbook_update",
        "pair": orderbook_data.get("pair"),
        "sequence_id": orderbook_data.get("sequence_id"),
        "timestamp_received": orderbook_data.get("timestamp_received"),
        "timestamp_parsed": orderbook_data.get("timestamp_parsed"),
        "best_bid": orderbook_data.get("bids", [[]])[0][0] if orderbook_data.get("bids") else None,
        "best_ask": orderbook_data.get("asks", [[]])[0][0] if orderbook_data.get("asks") else None,
        "spread": orderbook_data.get("spread"),
        "processing_time_ms": processing_time_ms
    }
    
    logger.info("Orderbook update processed", extra=log_data)

def log_heartbeat(logger: logging.Logger, heartbeat_data: dict):
    """Log heartbeat with server metrics"""
    log_data = {
        "event": "heartbeat",
        "server_status": heartbeat_data.get("server_status"),
        "queue_size": heartbeat_data.get("queue_size"),
        "memory_usage_mb": heartbeat_data.get("memory_usage_mb"),
        "active_clients": heartbeat_data.get("active_clients"),
        "current_scenario": heartbeat_data.get("current_scenario")
    }
    
    logger.info("Heartbeat sent", extra=log_data)

def log_scenario_switch(logger: logging.Logger, old_scenario: str, new_scenario: str):
    """Log scenario switching"""
    log_data = {
        "event": "scenario_switch",
        "old_scenario": old_scenario,
        "new_scenario": new_scenario,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info("Scenario switched", extra=log_data)

def log_incident_alert(logger: logging.Logger, alert_type: str, details: dict):
    """Log incident alerts"""
    log_data = {
        "event": "incident_alert",
        "alert_type": alert_type,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.warning("Incident alert triggered", extra=log_data)

def log_server_metrics(logger: logging.Logger, metrics: dict):
    """Log server performance metrics"""
    log_data = {
        "event": "server_metrics",
        "uptime_seconds": metrics.get("uptime_seconds"),
        "total_messages_processed": metrics.get("total_messages_processed"),
        "queue_size": metrics.get("queue_size"),
        "memory_usage_mb": metrics.get("memory_usage_mb"),
        "active_clients": metrics.get("active_clients"),
        "processing_rate_per_sec": metrics.get("processing_rate_per_sec")
    }
    
    logger.info("Server metrics", extra=log_data) 