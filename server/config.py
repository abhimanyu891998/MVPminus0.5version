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
    PROCESSING_DELAY_MS = 50  # Intentional delay for incident simulation
    TOP_LEVELS = 15  # Number of orderbook levels to publish
    
    # Incident simulation settings
    INITIAL_SCENARIO = "stable-mode"
    SCENARIO_SWITCH_TIME = 10  # seconds before switching to burst mode
    MEMORY_THRESHOLD_MB = 150  # Memory threshold for crash simulation (lowered for testing)
    GRACEFUL_SHUTDOWN_DELAY = 30  # seconds warning before shutdown
    
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

class IncidentSimulationConfig:
    """Configuration for incident simulation scenarios"""
    
    @staticmethod
    def get_scenario_sequence() -> list:
        """Get the sequence of scenarios for incident simulation"""
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
            "stable-mode": 10,    # Normal processing
            "burst-mode": 100,    # Intentional delay for incident simulation
            "gradual-spike": 50,  # Moderate delay
            "extreme-spike": 200  # Maximum delay
        } 