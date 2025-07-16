#!/usr/bin/env python3
"""
Example script showing how to use the generated synthetic data
"""

import json
import time
from pathlib import Path
from typing import Dict, Any

def load_scenario_data(scenario_name: str) -> Dict[str, Any]:
    """Load generated scenario data"""
    data_path = Path(__file__).parent.parent / "data" / "generated" / f"{scenario_name}-data.json"
    
    with open(data_path, 'r') as f:
        return json.load(f)

def simulate_real_time_feed(scenario_name: str, speed_multiplier: float = 1.0):
    """Simulate real-time data feed from generated data"""
    print(f"Starting {scenario_name} simulation...")
    
    data = load_scenario_data(scenario_name)
    scenario = data['scenario']
    updates = data['updates']
    
    print(f"Scenario: {scenario['description']}")
    print(f"Total updates: {len(updates)}")
    print(f"Duration: {scenario['duration']}ms")
    print(f"Speed multiplier: {speed_multiplier}x")
    print("-" * 50)
    
    # Calculate delay between updates
    avg_interval = scenario['duration'] / len(updates) / 1000.0  # Convert to seconds
    delay = avg_interval / speed_multiplier
    
    for i, update in enumerate(updates):
        # Extract key information
        data_update = update['data']
        best_bid = float(data_update['bids'][0][0])
        best_ask = float(data_update['asks'][0][0])
        spread = best_ask - best_bid
        
        # Print update info
        print(f"Update {i+1:3d}: "
              f"Bid: ${best_bid:8.2f} | "
              f"Ask: ${best_ask:8.2f} | "
              f"Spread: ${spread:5.2f} | "
              f"ID: {data_update['lastUpdateId']}")
        
        # Simulate real-time delay
        time.sleep(delay)
        
        # Stop after first 10 updates for demo
        if i >= 9:
            print("... (showing first 10 updates only)")
            break

def compare_scenarios():
    """Compare key metrics across different scenarios"""
    scenarios = ["stable-mode", "burst-mode", "gradual-spike", "extreme-spike"]
    
    print("SCENARIO COMPARISON")
    print("=" * 80)
    print(f"{'Scenario':<15} {'Updates':<8} {'Duration':<10} {'Avg Interval':<12} {'Volatility':<10}")
    print("-" * 80)
    
    for scenario_name in scenarios:
        try:
            data = load_scenario_data(scenario_name)
            scenario = data['scenario']
            metadata = data['metadata']
            
            # Handle different scenario structures
            if 'priceRange' in scenario:
                volatility = scenario['priceRange']['volatility'] * 100  # Convert to percentage
            elif 'phases' in scenario:
                # For multi-phase scenarios, use the highest volatility phase
                max_volatility = max(phase.get('priceRange', {}).get('volatility', 0) for phase in scenario['phases'])
                volatility = max_volatility * 100
            else:
                volatility = 0
            
            print(f"{scenario_name:<15} "
                  f"{metadata['totalUpdates']:<8} "
                  f"{scenario['duration']:<10} "
                  f"{metadata['avgInterval']:<12} "
                  f"{volatility:<10.1f}%")
                  
        except FileNotFoundError:
            print(f"{scenario_name:<15} Data not found")

def analyze_price_movement(scenario_name: str):
    """Analyze price movement in a scenario"""
    data = load_scenario_data(scenario_name)
    updates = data['updates']
    
    prices = []
    for update in updates:
        best_bid = float(update['data']['bids'][0][0])
        best_ask = float(update['data']['asks'][0][0])
        mid_price = (best_bid + best_ask) / 2
        prices.append(mid_price)
    
    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price
    
    print(f"\nPRICE ANALYSIS for {scenario_name}")
    print("-" * 40)
    print(f"Starting price: ${prices[0]:.2f}")
    print(f"Ending price: ${prices[-1]:.2f}")
    print(f"Min price: ${min_price:.2f}")
    print(f"Max price: ${max_price:.2f}")
    print(f"Price range: ${price_range:.2f}")
    print(f"Total updates: {len(prices)}")

def main():
    """Main function demonstrating different ways to use the data"""
    print("SYNTHETIC DATA USAGE EXAMPLES")
    print("=" * 50)
    
    # Compare all scenarios
    compare_scenarios()
    
    # Analyze price movement
    analyze_price_movement("stable-mode")
    analyze_price_movement("burst-mode")
    
    # Simulate real-time feed (sped up for demo)
    print(f"\n{'='*50}")
    print("REAL-TIME SIMULATION DEMO")
    print("=" * 50)
    simulate_real_time_feed("stable-mode", speed_multiplier=10.0)

if __name__ == "__main__":
    main() 