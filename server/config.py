"""
Configuration settings for MarketDataPublisher server
"""

import os
from typing import Dict, Any

class ServerConfig:
    """Server configuration settings"""
    
    # Server settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # WebSocket settings
    WS_PING_INTERVAL = 20  # seconds
    WS_PING_TIMEOUT = 10   # seconds
    
    # Data processing settings
    MAX_QUEUE_SIZE = 10000
    PROCESSING_DELAY_MS = 50  # Processing delay for message batching
    TOP_LEVELS = 15  # Number of orderbook levels to publish
    
    # Performance settings
    INITIAL_SCENARIO = "stable-mode"
    PROFILE_SWITCH_TIME = 10  # seconds before switching performance profiles
    MEMORY_THRESHOLD_MB = 150  # Memory threshold for performance monitoring (adjusted for demo)
    GRACEFUL_SHUTDOWN_DELAY = 10  # seconds warning before shutdown (reduced for demo)
    
    # Heartbeat settings
    HEARTBEAT_INTERVAL = 1  # seconds
    HEARTBEAT_TIMEOUT = 2   # seconds (client alert threshold)
    
    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Data paths
    DATA_DIR = "../data/generated"
    SCENARIOS = {
        "stable-mode": "stable-mode-data.json",
        "burst-mode": "burst-mode-data.json", 
        "gradual-spike": "gradual-spike-data.json",
        "extreme-spike": "extreme-spike-data.json"
    }
    
    # Trading pair settings
    TRADING_PAIR = "BTCUSDT"
    BASE_PRICE = 120000.0

class PerformanceConfig:
    """Configuration for performance profile scenarios"""
    
    @staticmethod
    def get_scenario_sequence() -> list:
        """Get the sequence of performance profiles"""
        return [
            {
                "name": "stable-mode",
                "duration": 10,  # seconds
                "description": "Normal operation"
            },
            {
                "name": "burst-mode", 
                "duration": 60,  # seconds
                "description": "High-frequency market spike"
            }
        ]
    
    @staticmethod
    def get_processing_delays() -> Dict[str, int]:
        """Get processing delays for different scenarios (in milliseconds)"""
        return {
            "stable-mode": 50,    # Normal processing (increased from 10ms)
            "burst-mode": 300,    # Increased processing delay under load (increased from 100ms)
            "gradual-spike": 150,  # Moderate delay (increased from 50ms)
            "extreme-spike": 500  # Maximum delay (increased from 200ms)
        } 