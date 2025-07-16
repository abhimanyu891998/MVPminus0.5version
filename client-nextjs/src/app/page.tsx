'use client'

import { useState, useEffect } from 'react'
import { Wifi, WifiOff, Activity, AlertTriangle, Clock, Users, Database, Zap } from 'lucide-react'
import OrderbookView from '@/components/OrderbookView'
import MetricsPanel from '@/components/MetricsPanel'
import LogsPanel from '@/components/LogsPanel'
import ScenarioControls from '@/components/ScenarioControls'
import PerformanceChart from '@/components/PerformanceChart'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useDashboardState } from '@/hooks/useDashboardState'

export default function Dashboard() {
  const { isConnected, error } = useWebSocket()
  const { state, updateOrderbook, updateMetrics } = useDashboardState()

  // Test state updates
  const testUpdate = () => {
    console.log('Testing state update...')
    const testMidPrice = 50000 + Math.floor(Date.now() % 1000)
    const testSpread = 1 + (Date.now() % 10)

    // Generate test orderbook data
    const testBids: [string, string][] = []
    const testAsks: [string, string][] = []

    for (let i = 0; i < 10; i++) {
      const bidPrice = testMidPrice - (i * 0.5) - (i * 0.01)
      const askPrice = testMidPrice + (i * 0.5) + (i * 0.01)
      const quantity = (5 + i * 0.3).toFixed(4)

      testBids.push([bidPrice.toFixed(2), quantity])
      testAsks.push([askPrice.toFixed(2), quantity])
    }

    updateOrderbook({
      bids: testBids,
      asks: testAsks,
      mid_price: testMidPrice,
      spread: testSpread
    })
    updateMetrics({
      memory_usage_mb: 20 + (Date.now() % 30),
      queue_size: 100 + (Date.now() % 500)
    })
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-950">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <Activity className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-xl font-bold">SRE Dashboard</h1>
                <p className="text-sm text-gray-400">MarketDataPublisher - AI SRE Training</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                {isConnected ? (
                  <Wifi className="w-4 h-4 text-green-400" />
                ) : (
                  <WifiOff className="w-4 h-4 text-red-400" />
                )}
                <span className="text-sm">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              {error && (
                <div className="flex items-center space-x-2 text-red-400">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-sm">{error}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {/* Debug Info */}
        <div className="mb-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-semibold text-gray-300">Debug Info</h4>
            <button
              onClick={testUpdate}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded"
            >
              Test Update
            </button>
          </div>
          <div className="text-xs text-gray-400 space-y-1">
            <div>Connection: {isConnected ? 'Connected' : 'Disconnected'}</div>
            <div>Orderbook Bids: {state.orderbook_data.bids.length}</div>
            <div>Orderbook Asks: {state.orderbook_data.asks.length}</div>
            <div>Mid Price: ${state.orderbook_data.mid_price.toFixed(2)}</div>
            <div>Memory: {state.metrics.memory_usage_mb.toFixed(1)} MB</div>
            <div>Queue: {state.metrics.queue_size}</div>
            <div>Logs: {state.logs.length}</div>
          </div>
        </div>

        {/* Top Row - Controls and Quick Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
          <ScenarioControls />

          {/* Quick Stats */}
          <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-green-600/20 rounded-lg flex items-center justify-center">
                  <Activity className="w-5 h-5 text-green-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Server Status</p>
                  <p className="text-lg font-semibold">
                    {state.metrics.server_status === 'healthy' ? 'Healthy' :
                      state.metrics.server_status === 'degraded' ? 'Degraded' : 'Unknown'}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-600/20 rounded-lg flex items-center justify-center">
                  <Database className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Memory Usage</p>
                  <p className="text-lg font-semibold">{state.metrics.memory_usage_mb.toFixed(1)} MB</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-yellow-600/20 rounded-lg flex items-center justify-center">
                  <Users className="w-5 h-5 text-yellow-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Active Clients</p>
                  <p className="text-lg font-semibold">{state.metrics.active_clients}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Orderbook and Metrics Row */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
          {/* Orderbook */}
          <div className="xl:col-span-2">
            <OrderbookView
              key={`orderbook-${state.orderbook_data.sequence_id}-${state.orderbook_data.timestamp}`}
              bids={state.orderbook_data.bids}
              asks={state.orderbook_data.asks}
              midPrice={state.orderbook_data.mid_price}
              spread={state.orderbook_data.spread}
              lastUpdate={state.orderbook_data.timestamp ? new Date(state.orderbook_data.timestamp) : undefined}
            />
          </div>

          {/* Metrics Panel */}
          <div>
            <MetricsPanel metrics={state.metrics} />
          </div>
        </div>

        {/* Performance Chart */}
        <div className="mb-6">
          <PerformanceChart data={state.performance_history} />
        </div>

        {/* Bottom Row - Logs and Incidents */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <LogsPanel logs={state.logs} />

          <div className="bg-gray-800 rounded-lg border border-gray-700">
            <div className="p-4 border-b border-gray-700">
              <h3 className="text-lg font-semibold flex items-center space-x-2">
                <AlertTriangle className="w-5 h-5 text-red-400" />
                <span>Recent Incidents</span>
              </h3>
            </div>
            <div className="p-4 max-h-80 overflow-y-auto">
              {state.incidents.length === 0 ? (
                <div className="text-center text-gray-400 py-8">
                  <AlertTriangle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No incidents recorded</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {state.incidents.slice(-5).reverse().map((incident, index) => (
                    <div key={index} className="bg-red-900/20 border border-red-800 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-red-400">{incident.type}</span>
                        <span className="text-sm text-gray-400">
                          {new Date(incident.timestamp || '').toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-300">{incident.details}</p>
                      <p className="text-xs text-gray-500 mt-1">Scenario: {incident.scenario}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
