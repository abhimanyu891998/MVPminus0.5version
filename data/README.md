# Synthetic Market Data for Incident Simulation

This directory contains synthetic market data that replicates Binance WebSocket orderbook data for BTC/USDT trading pair around $120,000 USD.

## Directory Structure

```
data/
├── scenarios/           # Scenario configuration files
│   ├── stable-mode.json
│   ├── burst-mode.json
│   ├── gradual-spike.json
│   └── extreme-spike.json
├── templates/           # Base templates
│   └── orderbook-template.json
├── config/             # Configuration files
│   └── scenario-config.json
├── generated/          # Generated synthetic data (created by generator)
│   ├── stable-mode-data.json
│   ├── burst-mode-data.json
│   ├── gradual-spike-data.json
│   └── extreme-spike-data.json
└── README.md
```

## Scenarios

### 1. Stable Mode (`stable-mode.json`)
- **Duration**: 10 seconds
- **Update Interval**: 100-500ms
- **Price Range**: $119,800 - $120,200
- **Volatility**: Low (0.1%)
- **Purpose**: Normal market conditions

### 2. Burst Mode (`burst-mode.json`)
- **Duration**: 15 seconds
- **Update Interval**: 10-50ms
- **Price Range**: $119,000 - $121,000
- **Volatility**: High (0.5%)
- **Purpose**: Market spike simulation with high-frequency updates

### 3. Gradual Spike (`gradual-spike.json`)
- **Duration**: 20 seconds
- **Phases**: 
  - Stable (0-5s): 200-400ms updates
  - Increasing (5-13s): 150-300ms updates
  - High-frequency (13-20s): 20-80ms updates
- **Purpose**: Progressive system degradation demonstration

### 4. Extreme Spike (`extreme-spike.json`)
- **Duration**: 10 seconds
- **Update Interval**: 5-20ms
- **Price Range**: $118,000 - $122,000
- **Volatility**: Very High (1%)
- **Purpose**: Maximum stress test guaranteed to trigger memory issues

## Data Format

The synthetic data follows Binance WebSocket format:

```json
{
  "stream": "btcusdt@depth20@100ms",
  "data": {
    "lastUpdateId": 123456789,
    "bids": [
      ["120000.00", "1.5000"],
      ["119999.50", "2.1000"]
    ],
    "asks": [
      ["120001.00", "0.8000"],
      ["120001.50", "1.2000"]
    ]
  }
}
```

## Usage

### Generate Synthetic Data

```bash
python utils/data_generator.py
```

This will generate all scenario data files in the `data/generated/` directory.

### Programmatic Usage

```python
from utils.data_generator import SyntheticDataGenerator

generator = SyntheticDataGenerator()

# Generate specific scenario
stable_data = generator.generate_scenario_data('stable-mode')

# Generate all scenarios
all_data = generator.generate_all_scenarios()

# Save to files
generator.save_generated_data(all_data)

# Preview a scenario
generator.preview_scenario('stable-mode', num_samples=5)
```

## Configuration

Edit `config/scenario-config.json` to:
- Change default scenario
- Modify scenario sequence
- Adjust switching behavior
- Update data generation parameters

## Scenario Switching

The system supports:
- **Auto-switching**: Automatic progression through scenarios
- **Manual override**: Manual scenario selection
- **Transition delays**: Smooth transitions between scenarios

## Price Movement Patterns

1. **Random**: Random price movements within bounds
2. **Trending**: Directional price movements with volatility
3. **Progressive**: Gradually increasing price volatility
4. **Chaotic**: Extreme price movements for stress testing

## Volume and Spread

- **Volume Range**: 0.1 - 25.0 BTC per level
- **Spread Range**: 0.05 - 2.0 USD between levels
- **Depth Levels**: 20 levels for both bids and asks

## Incident Simulation Strategy

1. **Stable Mode (0-10s)**: Normal operation
2. **Burst Mode (10s+)**: High-frequency updates trigger message queue buildup
3. **Memory Leak**: Delayed processing causes memory accumulation
4. **Server Shutdown**: Memory exhaustion leads to server failure
5. **Client Alert**: Client detects heartbeat failure and shows alert

This synthetic data approach provides consistent, reproducible incident scenarios for demonstration and testing purposes. 