'use client'

import { useState, useEffect, useRef } from 'react'
import { Wifi, WifiOff, Activity, AlertTriangle, Settings, TrendingUp, Users, Database, Zap, Clock, MemoryStick } from 'lucide-react'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useDashboardState } from '@/hooks/useDashboardState'

export default function TradingDashboard() {
  const dashboardState = useDashboardState()
  const { isConnected, error } = useWebSocket(dashboardState)
  const { state } = dashboardState
  const [incidentCount, setIncidentCount] = useState(0)
  const alertsScrollRef = useRef<HTMLDivElement>(null)
  const [lastSequenceId, setLastSequenceId] = useState(0)
  const [isUpdating, setIsUpdating] = useState(false)

  useEffect(() => {
    setIncidentCount(state.incidents.length)
    
    // Auto-scroll to the top when new incidents are added
    if (alertsScrollRef.current && state.incidents.length > 0) {
      alertsScrollRef.current.scrollTop = 0
    }
  }, [state.incidents])

  // Track orderbook updates for animations
  useEffect(() => {
    if (state.orderbook_data.sequence_id !== lastSequenceId && state.orderbook_data.sequence_id > 0) {
      setIsUpdating(true)
      setLastSequenceId(state.orderbook_data.sequence_id)
      
      // Reset animation after a short delay
      const timer = setTimeout(() => {
        setIsUpdating(false)
      }, 300)
      
      return () => clearTimeout(timer)
    }
  }, [state.orderbook_data.sequence_id, lastSequenceId])

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price)
  }

  const formatQuantity = (quantity: string) => {
    return parseFloat(quantity).toFixed(4)
  }

  const getDataFreshnessColor = (dataAge: number = 0, isStale: boolean = false) => {
    if (isStale && dataAge > 1000) return 'text-red-600 bg-red-50'
    if (isStale) return 'text-yellow-600 bg-yellow-50'
    return 'text-green-600 bg-green-50'
  }

  const getDataFreshnessText = (dataAge: number = 0, isStale: boolean = false) => {
    if (isStale && dataAge > 1000) return 'STALE'
    if (isStale) return 'SLOW'
    return 'LIVE'
  }

  const handleProfileSwitch = async (profileName: string) => {
    try {
      await fetch(`http://localhost:8000/config/profile/${profileName}`, {
        method: 'POST'
      })
    } catch (error) {
      console.error('Failed to switch profile:', error)
    }
  }

  const getModeDisplayInfo = (mode: string) => {
    switch (mode) {
      case 'stable-mode':
        return { 
          emoji: '🟢', 
          name: 'Stable Mode', 
          color: 'text-green-600 bg-green-50',
          description: 'Normal operation - Low latency'
        }
      case 'burst-mode':
        return { 
          emoji: '🟡', 
          name: 'Burst Mode', 
          color: 'text-yellow-600 bg-yellow-50',
          description: 'High frequency spikes'
        }
      case 'gradual-spike':
        return { 
          emoji: '🟠', 
          name: 'Gradual Spike', 
          color: 'text-orange-600 bg-orange-50',
          description: 'Progressive load increase'
        }
      case 'extreme-spike':
        return { 
          emoji: '🔴', 
          name: 'Extreme Spike', 
          color: 'text-red-600 bg-red-50',
          description: 'Maximum stress - High latency'
        }
      default:
        return { 
          emoji: '⚪', 
          name: 'Unknown', 
          color: 'text-gray-600 bg-gray-50',
          description: 'Unknown mode'
        }
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <TrendingUp className="w-4 h-4 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">BTC/USDT</h1>
                <p className="text-sm text-gray-500">Market Data Monitor</p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-6">
            {/* Connection Status */}
            <div className="flex items-center space-x-2">
              {isConnected ? (
                <div className="flex items-center space-x-1">
                  <div className={`w-2 h-2 bg-green-500 rounded-full transition-all duration-200 ${
                    isUpdating ? 'animate-ping' : 'animate-pulse'
                  }`}></div>
                  <span className={`text-sm text-green-600 font-medium transition-all duration-200 ${
                    isUpdating ? 'text-green-700' : ''
                  }`}>LIVE</span>
                </div>
              ) : (
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                  <span className="text-sm text-red-600 font-medium">OFFLINE</span>
                </div>
              )}
            </div>

            {/* Market Mode Switcher */}
            <div className="flex items-center space-x-3">
              <span className="text-sm font-medium text-gray-700">Mode:</span>
              <div className="flex items-center space-x-2">
                <select
                  onChange={(e) => handleProfileSwitch(e.target.value)}
                  value={state.metrics.current_scenario || "stable-mode"}
                  className="text-sm font-medium text-gray-900 border-2 border-gray-300 rounded-lg px-3 py-2 bg-white shadow-sm hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 cursor-pointer min-w-[140px]"
                >
                  <option value="stable-mode" className="py-2 text-gray-900 bg-white">🟢 Stable Mode</option>
                  <option value="burst-mode" className="py-2 text-gray-900 bg-white">🟡 Burst Mode</option>
                  <option value="gradual-spike" className="py-2 text-gray-900 bg-white">🟠 Gradual Spike</option>
                  <option value="extreme-spike" className="py-2 text-gray-900 bg-white">🔴 Extreme Spike</option>
                </select>
                <div className={`px-2 py-1 rounded-md text-xs font-medium ${getModeDisplayInfo(state.metrics.current_scenario || "stable-mode").color}`}>
                  {getModeDisplayInfo(state.metrics.current_scenario || "stable-mode").description}
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-80px)]">
        {/* Orderbook Section */}
        <div className="flex-1 p-6">
          <div className="bg-white border border-gray-200 rounded-lg h-full">
            {/* Orderbook Header */}
            <div className={`border-b border-gray-100 p-4 transition-all duration-300 ${isUpdating ? 'bg-blue-50 border-blue-200' : 'bg-white'}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <h2 className="text-lg font-semibold text-gray-900">Order Book</h2>
                  <div className={`px-2 py-1 rounded text-xs font-medium transition-all duration-200 ${getDataFreshnessColor(state.orderbook_data.data_age_ms, state.orderbook_data.is_stale)} ${isUpdating ? 'scale-105' : 'scale-100'}`}>
                    {getDataFreshnessText(state.orderbook_data.data_age_ms, state.orderbook_data.is_stale)}
                  </div>
                </div>
                <div className="flex items-center space-x-6 text-sm text-gray-500">
                  <div className={`transition-all duration-200 ${isUpdating ? 'text-blue-600 font-medium' : ''}`}>
                    Mid: {formatPrice(state.orderbook_data.mid_price)}
                  </div>
                  <div className={`transition-all duration-200 ${isUpdating ? 'text-blue-600 font-medium' : ''}`}>
                    Spread: {formatPrice(state.orderbook_data.spread)}
                  </div>
                  <div className={`transition-all duration-200 ${isUpdating ? 'text-blue-600 font-medium' : ''}`}>
                    Seq: {state.orderbook_data.sequence_id}
                  </div>
                  {state.orderbook_data.data_age_ms && (
                    <div className={`font-medium transition-all duration-200 ${
                      state.orderbook_data.data_age_ms > 1000 ? 'text-red-600' : 
                      state.orderbook_data.data_age_ms > 500 ? 'text-yellow-600' : 'text-green-600'
                    } ${isUpdating ? 'scale-105' : 'scale-100'}`}>
                      Age: {state.orderbook_data.data_age_ms.toFixed(0)}ms
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Critical Staleness Alert */}
            {state.orderbook_data.is_stale && state.orderbook_data.data_age_ms > 1000 && (
              <div className="bg-red-50 border-l-4 border-red-400 p-4 m-4">
                <div className="flex items-center">
                  <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
                  <div>
                    <p className="font-medium text-red-800">CRITICAL: Data Staleness Detected</p>
                    <p className="text-sm text-red-600">
                      Data received {state.orderbook_data.data_age_ms.toFixed(0)}ms ago - Processing lag detected
                    </p>
                    <p className="text-xs text-red-500 mt-1">
                      Data Age = Time from exchange receipt to client delivery
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Orderbook Content */}
            <div className={`flex-1 p-4 transition-all duration-200 ${isUpdating ? 'bg-gray-50/50' : ''}`}>
              <div className="grid grid-cols-2 gap-6 h-full">
                {/* Asks (Sell Orders) */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-gray-500 font-medium border-b pb-2">
                    <span>Price (USD)</span>
                    <span>Size (BTC)</span>
                  </div>
                  <div className="space-y-1 max-h-96 overflow-y-auto">
                    {state.orderbook_data.asks.slice(0, 15).reverse().map((ask, index) => (
                      <div 
                        key={index} 
                        className={`flex justify-between text-sm py-1 px-2 hover:bg-red-50 rounded transition-all duration-200 ${
                          isUpdating ? 'bg-red-50 border-l-2 border-red-300 shadow-sm' : ''
                        }`}
                      >
                        <span className={`text-red-600 font-mono font-medium transition-all duration-200 ${
                          isUpdating ? 'text-red-700' : ''
                        }`}>
                          {formatPrice(parseFloat(ask[0]))}
                        </span>
                        <span className={`text-gray-600 font-mono transition-all duration-200 ${
                          isUpdating ? 'text-gray-700' : ''
                        }`}>
                          {formatQuantity(ask[1])}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Bids (Buy Orders) */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-gray-500 font-medium border-b pb-2">
                    <span>Price (USD)</span>
                    <span>Size (BTC)</span>
                  </div>
                  <div className="space-y-1 max-h-96 overflow-y-auto">
                    {state.orderbook_data.bids.slice(0, 15).map((bid, index) => (
                      <div 
                        key={index} 
                        className={`flex justify-between text-sm py-1 px-2 hover:bg-green-50 rounded transition-all duration-200 ${
                          isUpdating ? 'bg-green-50 border-l-2 border-green-300 shadow-sm' : ''
                        }`}
                      >
                        <span className={`text-green-600 font-mono font-medium transition-all duration-200 ${
                          isUpdating ? 'text-green-700' : ''
                        }`}>
                          {formatPrice(parseFloat(bid[0]))}
                        </span>
                        <span className={`text-gray-600 font-mono transition-all duration-200 ${
                          isUpdating ? 'text-gray-700' : ''
                        }`}>
                          {formatQuantity(bid[1])}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* No Data State */}
              {state.orderbook_data.bids.length === 0 && state.orderbook_data.asks.length === 0 && (
                <div className="flex items-center justify-center h-64 text-gray-500">
                  <div className="text-center">
                    <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p className="text-sm">Waiting for market data...</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* System Metrics Sidebar */}
        <div className="w-80 p-6 border-l border-gray-200 flex-shrink-0">
          <div className="space-y-6 h-full">
            {/* System Health */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-3">System Health</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Database className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-600">Memory</span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {state.metrics.memory_usage_mb.toFixed(1)} MB
                    </div>
                    <div className="text-xs text-gray-500">
                      {((state.metrics.memory_usage_mb / 512) * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-600">Queue</span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {state.metrics.queue_size}
                    </div>
                    <div className="text-xs text-gray-500">messages</div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Zap className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-600">Delay</span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {state.metrics.processing_delay_ms}ms
                    </div>
                    <div className="text-xs text-gray-500">processing</div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Users className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-600">Clients</span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {state.metrics.active_clients}
                    </div>
                    <div className="text-xs text-gray-500">connected</div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Activity className={`w-4 h-4 text-gray-500 transition-all duration-200 ${isUpdating ? 'text-blue-500 animate-pulse' : ''}`} />
                    <span className="text-sm text-gray-600">Data Age</span>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-medium transition-all duration-200 ${
                      state.orderbook_data.data_age_ms > 1000 ? 'text-red-600' : 
                      state.orderbook_data.data_age_ms > 500 ? 'text-yellow-600' : 'text-green-600'
                    } ${isUpdating ? 'scale-105' : 'scale-100'}`}>
                      {state.orderbook_data.data_age_ms ? state.orderbook_data.data_age_ms.toFixed(0) + 'ms' : '0ms'}
                    </div>
                    <div className="text-xs text-gray-500">staleness</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Incidents */}
            <div className="bg-white border border-gray-200 rounded-lg p-4 h-80">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-gray-900">System Alerts</h3>
                {incidentCount > 0 && (
                  <span className="bg-red-100 text-red-800 text-xs font-medium px-2 py-1 rounded">
                    {incidentCount}
                  </span>
                )}
              </div>

              <div ref={alertsScrollRef} className="h-64 overflow-y-auto overflow-x-hidden scroll-smooth">
                {state.incidents.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    <div className="text-center">
                      <div className="text-sm">No incidents detected</div>
                      <div className="text-xs text-gray-400">System running normally</div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2 pr-2">
                    {state.incidents.slice(-10).reverse().map((incident, index) => (
                      <div 
                        key={`${incident.timestamp}-${index}`} 
                        className={`border border-red-200 rounded-lg p-3 bg-red-50 flex-shrink-0 transition-all duration-300 ${
                          index === 0 ? 'animate-pulse' : ''
                        }`}
                      >
                        <div className="flex items-start space-x-2">
                          <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium text-red-900 truncate">{incident.type}</div>
                            <div className="text-xs text-red-700 mt-1 break-words">{incident.details}</div>
                            <div className="text-xs text-red-600 mt-1">
                              {new Date(incident.timestamp).toLocaleTimeString()}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Current Status */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Current Status</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Server</span>
                  <span className={`text-sm font-medium ${state.metrics.server_status === 'healthy' ? 'text-green-600' : 'text-yellow-600'}`}>
                    {state.metrics.server_status === 'healthy' ? 'Healthy' : 'Degraded'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Profile</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm">
                      {getModeDisplayInfo(state.metrics.current_scenario || "stable-mode").emoji}
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {getModeDisplayInfo(state.metrics.current_scenario || "stable-mode").name}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Uptime</span>
                  <span className="text-sm font-medium text-gray-900">
                    {Math.floor(state.metrics.uptime_seconds / 60)}m {Math.floor(state.metrics.uptime_seconds % 60)}s
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}