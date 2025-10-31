# pairs-trading-gui
A Python-based pairs trading analysis tool with a modern GUI built using `ttkbootstrap`. This application allows users to explore mean-reversion strategies by analyzing the spread between two assets and simulating trades based on customizable thresholds.

## Overview
This tool enables users to load historical stock price data for two assets and analyze potential trade signals based on spread dynamics. A trade is triggered when the **raw spread** between the two assets crosses a user-defined threshold, calculated as a number of standard deviations from the historical mean.

The tool displays key performance metrics, including:
- Correlation between the asset prices
- Sharpe ratio of the simulated strategy
- Total return over the backtest period
- Number of trades executed

### Visualizations
Two interactive plots are produced:
- **Price & Spread Chart**: Displays historical prices of both assets, the calculated spread, and optional overlays (e.g., mean, thresholds, trade signals).
- **Portfolio Value Chart**: Simulates portfolio performance over time based on the generated trade signals.


## Settings
- **Starting Capital**: Initial capital used for simulating portfolio performance.
- **Order Size**: Number of shares to buy/sell per trade.
- **Standard Deviation (SD) Threshold**: Number of standard deviations from the mean used to trigger entry/exit signals.
- **Show Thresholds**: Toggle to display SD threshold lines on the spread chart.
- **Show Price Mean**: Toggle to display average price lines.
- **Show Trade Signals**: Toggle to display entry/exit points on the chart.


## Setup
1. Install dependencies from `requirements.txt`
2. Run the application `Main Application.py`

## Sample Data
Two sample data files (`KO historical quotes.csv`, `PEP historical quotes.csv`) are included for demonstration. These files were downloaded from NASDAQ, and the application is designed to work with this format, specifically:
- A `Date` column
- A `Close/Last` price column
If using your own data, ensure it follows this structure for compatibility.
