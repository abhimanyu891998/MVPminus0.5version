#!/usr/bin/env python3
"""
Simple WebSocket client to test the MarketDataPublisher server
"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_websocket():
    """Test WebSocket connection to the server"""
    uri = "ws://localhost:8000/ws"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server!")
            print("Waiting for messages...\n")
            
            # Send a test message
            test_message = {
                "type": "subscribe",
                "data": {
                    "client_id": "test_client",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            await websocket.send(json.dumps(test_message))
            print(f"📤 Sent: {test_message}")
            
            # Listen for messages
            message_count = 0
            start_time = datetime.now()
            
            while True:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    message_count += 1
                    
                    # Parse and display message
                    data = json.loads(message)
                    message_type = data.get("type", "unknown")
                    timestamp = data.get("timestamp", "unknown")
                    
                    print(f"📥 Message #{message_count} ({message_type}) at {timestamp}")
                    
                    if message_type == "heartbeat":
                        heartbeat_data = data.get("data", {})
                        print(f"   💓 Server Status: {heartbeat_data.get('server_status')}")
                        print(f"   📊 Queue Size: {heartbeat_data.get('queue_size')}")
                        print(f"   💾 Memory: {heartbeat_data.get('memory_usage_mb', 0):.2f} MB")
                        print(f"   👥 Active Clients: {heartbeat_data.get('active_clients')}")
                        print(f"   🎭 Scenario: {heartbeat_data.get('current_scenario')}")
                    
                    elif message_type == "orderbook_update":
                        orderbook_data = data.get("data", {})
                        print(f"   📈 Pair: {orderbook_data.get('pair')}")
                        print(f"   🔢 Sequence: {orderbook_data.get('sequence_id')}")
                        print(f"   💰 Mid Price: {orderbook_data.get('mid_price', 0):.2f}")
                        print(f"   📏 Spread: {orderbook_data.get('spread', 0):.2f}")
                        print(f"   ⏱️  Processing Time: {orderbook_data.get('processing_time_ms', 0):.2f}ms")
                    
                    elif message_type == "incident_alert":
                        incident_data = data.get("data", {})
                        print(f"   🚨 INCIDENT: {incident_data.get('type')}")
                        print(f"   📋 Details: {incident_data.get('details')}")
                        print(f"   🎭 Scenario: {incident_data.get('scenario')}")
                    
                    print()
                    
                    # Stop after 20 messages or 2 minutes
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if message_count >= 20 or elapsed >= 120:
                        print(f"✅ Test completed! Received {message_count} messages in {elapsed:.1f} seconds")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for message...")
                    break
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
                    break
                    
    except websockets.exceptions.ConnectionRefused:
        print("❌ Connection refused. Is the server running on port 8000?")
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🧪 WebSocket Connection Test")
    print("=" * 40)
    asyncio.run(test_websocket()) 