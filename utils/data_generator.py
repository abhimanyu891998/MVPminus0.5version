import json
import random
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import math

class SyntheticDataGenerator:
    def __init__(self):
        self.base_price = 120000
        self.current_price = self.base_price
        self.last_update_id = 0
    
    def random_float(self, min_val: float, max_val: float) -> float:
        """Generate a random float between min and max"""
        return random.uniform(min_val, max_val)
    
    def random_int(self, min_val: int, max_val: int) -> int:
        """Generate a random integer between min and max"""
        return random.randint(min_val, max_val)
    
    def generate_price(self, base_price: float, volatility: float, min_price: float, max_price: float) -> float:
        """Generate a new price with volatility"""
        change = (random.random() - 0.5) * 2 * volatility * base_price
        new_price = self.current_price + change
        
        # Keep price within bounds
        new_price = max(min_price, min(max_price, new_price))
        
        # Update current price
        self.current_price = new_price
        
        return round(new_price, 2)
    
    def generate_orderbook_levels(self, price: float, is_bid: bool, levels: int, 
                                 spread_range: Dict, volume_range: Dict) -> List[List[str]]:
        """Generate orderbook levels (bids or asks)"""
        orderbook = []
        spread = self.random_float(spread_range["min"], spread_range["max"])
        
        for i in range(levels):
            if is_bid:
                # Bids are below current price
                level_price = price - (i * spread) - self.random_float(0, spread * 0.5)
            else:
                # Asks are above current price
                level_price = price + (i * spread) + self.random_float(0, spread * 0.5)
            
            volume = self.random_float(volume_range["min"], volume_range["max"])
            
            orderbook.append([
                f"{level_price:.2f}",
                f"{volume:.4f}"
            ])
        
        return orderbook
    
    def generate_orderbook_update(self, scenario: Dict) -> Dict:
        """Generate a single orderbook update"""
        self.last_update_id += 1
        
        price = self.generate_price(
            scenario["priceRange"]["base"],
            scenario["priceRange"]["volatility"],
            scenario["priceRange"]["min"],
            scenario["priceRange"]["max"]
        )
        
        bids = self.generate_orderbook_levels(
            price,
            True,
            scenario["depthLevels"],
            scenario["spreadRange"],
            scenario["volumeRange"]
        )
        
        asks = self.generate_orderbook_levels(
            price,
            False,
            scenario["depthLevels"],
            scenario["spreadRange"],
            scenario["volumeRange"]
        )
        
        return {
            "stream": "btcusdt@depth20@100ms",
            "data": {
                "lastUpdateId": self.last_update_id,
                "bids": bids,
                "asks": asks
            }
        }
    
    def generate_scenario_data(self, scenario_name: str) -> Dict:
        """Generate data for a specific scenario"""
        scenario_path = Path(__file__).parent.parent / "data" / "scenarios" / f"{scenario_name}.json"
        
        with open(scenario_path, 'r') as f:
            scenario = json.load(f)
        
        updates = []
        total_duration = scenario["duration"]
        
        # Handle different scenario types
        if "phases" in scenario:
            # Gradual spike scenario with phases
            current_time = 0
            for phase in scenario["phases"]:
                phase_duration = phase["duration"]
                phase_scenario = {**scenario, **phase}
                
                avg_interval = (phase["updateInterval"]["min"] + phase["updateInterval"]["max"]) / 2
                num_updates = int(phase_duration / avg_interval)
                
                for _ in range(num_updates):
                    update = self.generate_orderbook_update(phase_scenario)
                    updates.append(update)
                
                current_time += phase_duration
        else:
            # Regular scenario
            avg_interval = (scenario["updateInterval"]["min"] + scenario["updateInterval"]["max"]) / 2
            num_updates = int(total_duration / avg_interval)
            
            for _ in range(num_updates):
                update = self.generate_orderbook_update(scenario)
                updates.append(update)
        
        return {
            "scenario": scenario,
            "updates": updates,
            "metadata": {
                "totalUpdates": len(updates),
                "duration": total_duration,
                "avgInterval": avg_interval if "phases" not in scenario else "variable"
            }
        }
    
    def generate_all_scenarios(self) -> Dict:
        """Generate data for all scenarios"""
        scenarios = ["stable-mode", "burst-mode", "gradual-spike", "extreme-spike"]
        all_data = {}
        
        for scenario_name in scenarios:
            print(f"Generating data for {scenario_name}...")
            # Reset price for each scenario to maintain consistency
            self.current_price = self.base_price
            self.last_update_id = 0
            all_data[scenario_name] = self.generate_scenario_data(scenario_name)
        
        return all_data
    
    def save_generated_data(self, data: Dict, output_dir: str = "data/generated"):
        """Save generated data to files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for scenario_name, scenario_data in data.items():
            file_path = output_path / f"{scenario_name}-data.json"
            with open(file_path, 'w') as f:
                json.dump(scenario_data, f, indent=2)
            print(f"Saved {scenario_name} data to {file_path}")
    
    def preview_scenario(self, scenario_name: str, num_samples: int = 5) -> None:
        """Preview first few updates from a scenario"""
        data = self.generate_scenario_data(scenario_name)
        print(f"\n=== {scenario_name.upper()} PREVIEW ===")
        print(f"Total updates: {data['metadata']['totalUpdates']}")
        print(f"Duration: {data['metadata']['duration']}ms")
        print(f"Average interval: {data['metadata']['avgInterval']}")
        print(f"\nFirst {num_samples} updates:")
        
        for i, update in enumerate(data['updates'][:num_samples]):
            print(f"\nUpdate {i+1}:")
            print(f"  Price range: {update['data']['bids'][0][0]} - {update['data']['asks'][0][0]}")
            print(f"  Bid levels: {len(update['data']['bids'])}")
            print(f"  Ask levels: {len(update['data']['asks'])}")

def main():
    """Main function to generate all scenarios when run directly"""
    generator = SyntheticDataGenerator()
    
    # Generate all scenarios
    all_data = generator.generate_all_scenarios()
    
    # Save to files
    generator.save_generated_data(all_data)
    
    print("\n" + "="*50)
    print("All synthetic data generated successfully!")
    print("="*50)
    
    # Show previews
    for scenario in ["stable-mode", "burst-mode"]:
        generator.preview_scenario(scenario, 3)

if __name__ == "__main__":
    main() 