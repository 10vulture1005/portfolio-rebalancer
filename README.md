# Portfolio Rebalancing Tool

A Python CLI tool for rebalancing investment portfolios (ETFs, stocks, etc.) with support for CSV import, real-time price and currency data, group/adjust logic, and multiple rebalancing strategies.

## Features
- **CSV Import:** Import your portfolio from a CSV file (delimiter auto-detected). Columns: `symbol`, `wkn`, `shares`, `group`, `adjust`, `target`, `currency`.
- **Real-Time Data:** Fetches current prices using Yahoo Finance and currency rates from exchangerate.host.
- **Group/Adjust Logic:** Only assets with `adjust==1` are rebalanced within each group.
- **Rebalancing Strategies:**
  - **Full Rebalance:** Match targets exactly.
  - **Minimal Rebalance:** Only rebalance if drift exceeds a threshold.
  - **Value-Preserving Rebalance:** Minimize drift while keeping total value as close as possible to original.
  - **Distribute Across Adjustables:** Optionally split group adjustment across all adjustable assets.
- **Rounding Control:** Choose floor/ceil rounding for share trades.
- **Detailed Reports:** See before/after allocation, group weights, drift (with color cues), and suggested trades (with cash values).
- **Robust Error Handling:** Warnings for missing prices, currency conversion failures, and malformed CSV rows.

## Usage

1. **Prepare your CSV** (example: `etfs.csv`):
   ```csv
   symbol:wkn:shares:group:adjust:target:currency
   AHYQ.DE:ETF018:605.44:WD:1:50.4:EUR
   XDWD.DE:A1XB5U:122.40:WD:0::EUR
   LYP6.DE:LYX0Q0:18.45:EU:1:12.6:EUR
   ...
   ```
   - `adjust` = 1 means the asset is eligible for rebalancing in its group.
   - `target` is the target percentage allocation for the asset or group.

2. **Run the tool:**
   ```sh
   python main.py
   ```

3. **Follow the prompts:**
   - Enter the CSV path (or press Enter for default `etfs.csv`).
   - Enter your base currency (e.g., EUR, USD).
   - Choose a rebalancing method:
     - 1: Full rebalance
     - 2: Minimal rebalance (set drift threshold)
     - 3: Value-preserving rebalance
   - Choose rounding method for share trades (ceil/floor).

4. **Review the output:**
   - Portfolio and group allocation reports (with color-coded drift)
   - Suggested trades (with cash values and group info)
   - New portfolio allocation after trades, with value delta

## Advanced Options
- **Distribute Across Adjustables:**
  - In `full_rebalance` and `minimal_rebalance`, you can set `distribute_across_adjustables=True` to split group adjustment across all adjustable assets (proportional to their targets or equally).
- **Error Handling:**
  - Malformed CSV rows are skipped with a warning.
  - Missing prices or conversion failures are reported.

## Code Structure
- `main.py` — CLI entry, workflow, and user prompts
- `portfolio.py` — Asset and Portfolio classes, CSV loader
- `data_fetcher.py` — Price and currency fetching
- `rebalance.py` — Rebalancing logic (full, minimal, value-preserving)
- `report.py` — Reporting and trade application utilities

## Requirements
- Python 3.8+
- `yfinance`, `requests`

Install dependencies:
```sh
pip install yfinance requests
```

## License
MIT License

---
*Created by Time Money Code <->, 2025*
