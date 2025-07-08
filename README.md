# Sell Put Screener

## Overview
This application is a powerful put option selling screener that helps traders identify potential cash-secured sell put trades based on customizable criteria. The tool provides a user-friendly interface for screening put options across multiple stock symbols, with detailed metrics and color code of results.

## Features

### Stock Symbol Management
- Select from existing stock symbols
- Add new stock symbols to the screening list
- Screen individual stocks or all stocks in your list

### Customizable Screening Criteria
- **Options Strategy Settings**
  - Maximum calendar days to expiration (DTE)
  - Minimum volume requirements
  - Minimum open interest thresholds

- **Performance Criteria**
  - Minimum annualized return percentage
  - Delta range selection (for risk management)

### Results Display
- Comprehensive table view of filtered put options
- Key metrics displayed for each option:
  - Strike price
  - Option price
  - Volume and open interest
  - Implied volatility
  - Delta
  - Annualized return percentage
  - Expiration date
  - Calendar days and remaining business days

- Color-coded results highlighting high-potential trades:
  - Green highlighting for options with ≥50% annualized returns
  - Yellow highlighting for options with ≥30% annualized returns

### Background Processing
- Multi-threaded design for processing multiple stocks simultaneously
- Real-time progress updates in the status bar
- Non-blocking UI during data retrieval and processing

## Technical Details
- Built with PyQt5 for the user interface
- Utilizes yfinance for retrieving options data
- Implements QThread for background processing
- Configuration saved in JSON format for persistence

## Getting Started
1. Launch the application
2. Add your desired stock symbols
3. Adjust screening criteria to match your put-selling strategy
4. Click "Screen Selected Stock" or "Screen All Stocks"
5. Review the filtered put options in the results table

### Launch Using Batch File
You can also use the included batch file to launch the application. Simply double-click on `run_sell_put_screener.bat` to start the program. Note that you may need to modify the path in the batch file to match your installation location.

## Requirements
- Python 3.6+
- PyQt5
- pandas
- yfinance

## Configuration
The application saves your settings in a config.json file, including:
- List of stock symbols
- Options strategy parameters
- Screening criteria thresholds

This allows your preferences to persist between sessions.