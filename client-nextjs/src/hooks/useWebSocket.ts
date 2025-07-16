'use client'

import { useState, useEffect, useRef } from 'react'
import { useDashboardState } from './useDashboardState'

interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const isConnectingRef = useRef(false)
  const { updateOrderbook, updateMetrics, addLog, addIncident, updatePerformanceHistory } = useDashboardState()

  const connect = () => {
    if (isConnectingRef.current || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    isConnectingRef.current = true

    try {
      console.log('Attempting WebSocket connection...')
      const ws = new WebSocket('ws://localhost:8000/ws')
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        setError(null)
        isConnectingRef.current = false
        addLog('INFO', 'WebSocket connected successfully')
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          console.log('📨 Received WebSocket message:', message.type, message.data)

          // Handle different message types
          switch (message.type) {
            case 'connection':
              console.log('Connected to server:', message.data.message)
              addLog('INFO', `Connected to server: ${message.data.message}`)

              // Send subscription after connection is established
              if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                  type: 'subscribe',
                  data: {
                    client_id: 'nextjs_dashboard',
                    timestamp: new Date().toISOString()
                  }
                }))
              }
              break

            case 'orderbook_update':
              console.log('🔄 Updating orderbook - Full message:', message)
              console.log('📊 Orderbook data structure:', {
                bids: message.data.bids,
                asks: message.data.asks,
                mid_price: message.data.mid_price,
                spread: message.data.spread,
                sequence_id: message.data.sequence_id,
                timestamp: message.data.timestamp
              })
              updateOrderbook({
                bids: message.data.bids || [],
                asks: message.data.asks || [],
                mid_price: message.data.mid_price || 0,
                spread: message.data.spread || 0,
                sequence_id: message.data.sequence_id || 0,
                timestamp: message.data.timestamp || new Date().toISOString()
              })
              break

            case 'heartbeat':
              console.log('Updating metrics:', message.data)
              updateMetrics({
                memory_usage_mb: message.data.memory_usage_mb || 0,
                queue_size: message.data.queue_size || 0,
                processing_delay_ms: message.data.processing_delay_ms || 0,
                server_status: message.data.server_status || 'unknown',
                active_clients: message.data.active_clients || 0,
                current_scenario: message.data.current_scenario || 'unknown',
                uptime_seconds: message.data.uptime_seconds || 0
              })

              // Update performance history
              updatePerformanceHistory(
                message.data.memory_usage_mb || 0,
                message.data.queue_size || 0,
                message.data.processing_delay_ms || 0
              )
              break

            case 'incident_alert':
              console.log('Incident alert:', message.data)
              addIncident({
                timestamp: message.data.timestamp || new Date().toISOString(),
                type: message.data.type || 'Unknown',
                details: message.data.details || 'No details provided',
                scenario: message.data.scenario || 'unknown',
                uptime: message.data.uptime || 0
              })
              addLog('INCIDENT', `Incident: ${message.data.type} - ${message.data.details}`)
              break

            default:
              console.log('Unknown message type:', message.type)
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err)
          addLog('ERROR', `Failed to parse WebSocket message: ${err}`)
        }
      }

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        setIsConnected(false)
        isConnectingRef.current = false
        addLog('WARNING', `WebSocket connection lost (${event.code})`)

        // Only attempt to reconnect if it wasn't a clean close
        if (event.code !== 1000) {
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current)
          }
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...')
            addLog('INFO', 'Attempting to reconnect...')
            connect()
          }, 3000)
        }
      }

      ws.onerror = (event) => {
        console.error('WebSocket error:', event)
        setError('Connection error')
        setIsConnected(false)
        isConnectingRef.current = false
        addLog('ERROR', 'WebSocket connection error')
      }

    } catch (err) {
      console.error('Error creating WebSocket connection:', err)
      setError('Failed to connect')
      setIsConnected(false)
      isConnectingRef.current = false
      addLog('ERROR', `Failed to create WebSocket connection: ${err}`)
    }
  }

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounting')
      }
    }
  }, [])

  return { isConnected, error }
} 