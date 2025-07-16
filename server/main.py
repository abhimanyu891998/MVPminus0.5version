"""
MarketDataPublisher Server - Main Application
"""

import asyncio
import json
import logging
import signal
import time
from datetime import datetime
from typing import List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import ServerConfig
from models import ServerStatus, HeartbeatMessage
from utils.logger import setup_logger
from data_loader import SyntheticDataLoader, OrderbookParser, DataSimulator
from queue_processor import MessageQueueProcessor

# Setup logging
logger = setup_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MarketDataPublisher",
    description="Real-time orderbook data publisher with incident simulation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global server state
server_start_time = time.time()
active_connections: List[WebSocket] = []
total_messages_processed = 0
current_scenario = ServerConfig.INITIAL_SCENARIO

# Initialize components
data_loader = SyntheticDataLoader()
orderbook_parser = OrderbookParser()
data_simulator = DataSimulator(data_loader, orderbook_parser)
queue_processor = MessageQueueProcessor()

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Connect a new client"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total clients: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a client"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

# Initialize connection manager
manager = ConnectionManager()

# Global shutdown event
server_shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    server_shutdown_event.set()

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Callback functions for queue processor
async def handle_orderbook_processed(orderbook_data: dict):
    """Handle processed orderbook data"""
    global total_messages_processed
    total_messages_processed += 1
    
    # Broadcast to all connected clients
    message = {
        "type": "orderbook_update",
        "data": orderbook_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast(json.dumps(message))

async def handle_heartbeat(heartbeat: HeartbeatMessage):
    """Handle heartbeat from queue processor"""
    # Update active clients count
    heartbeat.active_clients = len(manager.active_connections)
    
    # Convert heartbeat to JSON-serializable format
    heartbeat_data = {
        "timestamp": heartbeat.timestamp.isoformat(),
        "server_status": heartbeat.server_status,
        "queue_size": heartbeat.queue_size,
        "memory_usage_mb": heartbeat.memory_usage_mb,
        "active_clients": heartbeat.active_clients,
        "current_scenario": heartbeat.current_scenario
    }
    
    # Broadcast heartbeat to all clients
    message = {
        "type": "heartbeat",
        "data": heartbeat_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast(json.dumps(message))

async def handle_incident_alert(incident_data: dict):
    """Handle incident alert from queue processor"""
    # Broadcast incident alert to all clients
    message = {
        "type": "incident_alert",
        "data": incident_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast(json.dumps(message))
    
    logger.warning(f"Incident alert broadcasted: {incident_data['type']}")

@app.on_event("startup")
async def startup_event():
    """Server startup event"""
    global server_start_time, data_loader, queue_processor
    server_start_time = time.time()
    logger.info("MarketDataPublisher server starting up...")
    logger.info(f"Server will run on {ServerConfig.HOST}:{ServerConfig.PORT}")
    
    # Load all scenarios
    if data_loader.load_all_scenarios():
        logger.info("All scenarios loaded successfully")
    else:
        logger.error("Failed to load some scenarios")
    
    # Set up queue processor callbacks
    queue_processor.set_callbacks(
        on_orderbook_processed=handle_orderbook_processed,
        on_heartbeat=handle_heartbeat,
        on_incident_alert=handle_incident_alert
    )
    
    # Start queue processor
    await queue_processor.start()
    logger.info("Queue processor started")
    
    # Start shutdown monitor
    asyncio.create_task(_monitor_shutdown())

@app.on_event("shutdown")
async def shutdown_event():
    """Server shutdown event"""
    global queue_processor
    logger.info("MarketDataPublisher server shutting down...")
    
    # Stop queue processor
    if queue_processor:
        await queue_processor.stop()
        logger.info("Queue processor stopped")

async def _monitor_shutdown():
    """Monitor for shutdown signal and gracefully stop the server"""
    await server_shutdown_event.wait()
    logger.info("Shutdown signal received, stopping server...")
    
    # Stop the queue processor
    if queue_processor:
        await queue_processor.stop()
    
    # Close all WebSocket connections
    for connection in manager.active_connections[:]:
        try:
            await connection.close()
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
    
    logger.info("Server shutdown complete")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MarketDataPublisher Server",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/test")
async def test_endpoint():
    """Test endpoint for debugging"""
    logger.info("Test endpoint called")
    return {
        "message": "Test endpoint working",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global queue_processor
    uptime = time.time() - server_start_time
    
    # Get queue processor status
    processor_status = queue_processor.get_status() if queue_processor else {}
    
    status = ServerStatus(
        status="healthy" if not processor_status.get("incident_triggered", False) else "degraded",
        uptime_seconds=uptime,
        total_messages_processed=processor_status.get("total_messages_processed", 0),
        current_queue_size=processor_status.get("queue_size", 0),
        memory_usage_mb=processor_status.get("memory_usage_mb", 0.0),
        active_clients=len(manager.active_connections),
        current_scenario=processor_status.get("current_scenario", current_scenario),
        last_heartbeat=datetime.utcnow()
    )
    
    return status.dict()

@app.get("/status")
async def server_status():
    """Detailed server status"""
    uptime = time.time() - server_start_time
    
    status = ServerStatus(
        status="running",
        uptime_seconds=uptime,
        total_messages_processed=total_messages_processed,
        current_queue_size=0,
        memory_usage_mb=0.0,
        active_clients=len(manager.active_connections),
        current_scenario=current_scenario,
        last_heartbeat=datetime.utcnow()
    )
    
    return {
        "server": status.dict(),
        "config": {
            "host": ServerConfig.HOST,
            "port": ServerConfig.PORT,
            "max_queue_size": ServerConfig.MAX_QUEUE_SIZE,
            "processing_delay_ms": ServerConfig.PROCESSING_DELAY_MS,
            "heartbeat_interval": ServerConfig.HEARTBEAT_INTERVAL,
            "memory_threshold_mb": ServerConfig.MEMORY_THRESHOLD_MB
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data"""
    await manager.connect(websocket)
    
    try:
        # Send initial connection message
        welcome_message = {
            "type": "connection",
            "data": {
                "message": "Connected to MarketDataPublisher",
                "timestamp": datetime.utcnow().isoformat(),
                "scenario": current_scenario
            }
        }
        await manager.send_personal_message(json.dumps(welcome_message), websocket)
        
        # Keep connection alive
        while True:
            try:
                # Wait for client messages (ping/pong)
                data = await websocket.receive_text()
                logger.debug(f"Received from client: {data}")
                
                # Echo back for now (will be enhanced with actual data processing)
                response = {
                    "type": "echo",
                    "data": {
                        "message": f"Received: {data}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                await manager.send_personal_message(json.dumps(response), websocket)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(websocket)

@app.get("/scenarios")
async def list_scenarios():
    """List available scenarios"""
    return {
        "available_scenarios": list(ServerConfig.SCENARIOS.keys()),
        "current_scenario": current_scenario,
        "scenario_files": ServerConfig.SCENARIOS
    }

@app.post("/scenarios/{scenario_name}")
async def switch_scenario(scenario_name: str):
    """Switch to a different scenario"""
    global current_scenario, queue_processor
    
    logger.info(f"Received scenario switch request: {scenario_name}")
    
    if scenario_name not in ServerConfig.SCENARIOS:
        logger.error(f"Scenario '{scenario_name}' not found. Available: {list(ServerConfig.SCENARIOS.keys())}")
        raise HTTPException(status_code=400, detail=f"Scenario '{scenario_name}' not found")
    
    current_scenario = scenario_name
    
    # Switch scenario in queue processor
    if queue_processor:
        queue_processor.switch_scenario(scenario_name)
    
    logger.info(f"Successfully switched to scenario: {scenario_name}")
    
    return {
        "message": f"Switched to scenario: {scenario_name}",
        "scenario": scenario_name,
        "timestamp": datetime.utcnow().isoformat()
    }

# Global simulation control
simulation_running = False
simulation_task = None

@app.post("/simulation/start")
async def start_simulation():
    """Start data simulation"""
    global data_simulator, queue_processor, simulation_running, simulation_task
    
    logger.info("Received simulation start request")
    
    if simulation_running:
        return {
            "message": "Simulation already running",
            "scenario": current_scenario,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        simulation_running = True
        # Start simulation in background
        simulation_task = asyncio.create_task(run_simulation())
        
        logger.info("Simulation started successfully")
        return {
            "message": "Data simulation started",
            "scenario": current_scenario,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        simulation_running = False
        logger.error(f"Error starting simulation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start simulation: {e}")

@app.post("/simulation/stop")
async def stop_simulation():
    """Stop data simulation"""
    global simulation_running, simulation_task
    
    logger.info("Received simulation stop request")
    
    if not simulation_running:
        return {
            "message": "Simulation not running",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        simulation_running = False
        if simulation_task and not simulation_task.done():
            simulation_task.cancel()
        
        logger.info("Simulation stopped successfully")
        return {
            "message": "Data simulation stopped",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error stopping simulation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop simulation: {e}")

async def run_simulation():
    """Run the data simulation"""
    global data_simulator, queue_processor, simulation_running
    
    try:
        async for orderbook in data_simulator.start_simulation(current_scenario, speed_multiplier=1.0):
            if not simulation_running:
                logger.info("Simulation stopped by user request")
                break
            # Add orderbook to queue for processing
            await queue_processor.add_orderbook(orderbook)
            
    except asyncio.CancelledError:
        logger.info("Simulation task cancelled")
    except Exception as e:
        logger.error(f"Error in simulation: {e}")
    finally:
        simulation_running = False

@app.get("/simulation/status")
async def get_simulation_status():
    """Get simulation status"""
    global data_simulator
    
    status = data_simulator.get_simulation_status()
    return {
        "simulation": status,
        "scenario_info": data_loader.get_current_scenario_info(),
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=ServerConfig.HOST,
        port=ServerConfig.PORT,
        reload=ServerConfig.DEBUG,
        log_level=ServerConfig.LOG_LEVEL.lower()
    ) 