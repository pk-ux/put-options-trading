import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from scipy.stats import norm

def load_config():
    import os
    import sys
    
    # Determine the basic path of the application
    if getattr(sys, 'frozen', False):
        # If it's a packaged executable file
        application_path = os.path.dirname(sys.executable)
    else:
        # If it's a development environment
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    # Use application path to load configuration file
    config_path = os.path.join(application_path, 'config.json')
    
    # If configuration file doesn't exist, create a default configuration
    if not os.path.exists(config_path):
        default_config = {
            "data": {
                "symbols": ["AAPL", "MSFT", "GOOGL", "SPY", "QQQ", "TSLA", "APP", "IBIT", "PLTR"
                            ,"AVGO", "MSTR", "COIN", "SVXY", "NVDA", "AMD", "INTC", "META"]
            },
            "options_strategy": {
                "max_dte": 45,
                "min_volume": 10,
                "min_open_interest": 10
            },
            "screening_criteria": {
                "min_annualized_return": 20,
                "min_delta": -0.3,
                "max_delta": -0.1
            },
            "output": {
                "sort_by": ["annualized_return"],
                "sort_order": "descending",
                "max_results": 50
            }
        }
        try:
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            print(f"Created default config file at {config_path}")
        except Exception as e:
            print(f"Error creating default config: {str(e)}")
            return default_config
    
    # Load configuration file
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file: {str(e)}")
        # If unable to load configuration file, return default configuration
        return {
            "data": {"symbols": ["AAPL", "MSFT", "GOOGL", "SPY", "QQQ", "TSLA", "APP", "IBIT", "PLTR"
                            ,"AVGO", "MSTR", "COIN", "SVXY", "NVDA", "AMD", "INTC", "META"]
                            },
            "options_strategy": {"max_dte": 45, "min_volume": 10, "min_open_interest": 10},
            "screening_criteria": {"min_annualized_return": 20, "min_delta": -0.3, "max_delta": -0.1},
            "output": {"sort_by": ["annualized_return"], "sort_order": "descending", "max_results": 10}
        }

def get_options_chain(symbol, config):
    stock = yf.Ticker(symbol)
    max_dte = config['options_strategy']['max_dte']
    expiry_dates = [date for date in stock.options 
                   if (pd.to_datetime(date) - datetime.now()).days <= max_dte]
    
    all_options = pd.DataFrame()
    for date in expiry_dates:
        try:
            chain = stock.option_chain(date)
            puts = chain.puts
            puts['expiry'] = date
            puts['dte'] = int((pd.to_datetime(date) - datetime.now()).days)
            puts['symbol'] = symbol
            
            # Calculate Greeks if not available
            if 'delta' not in puts.columns:
                S = stock.info['regularMarketPrice']
                K = puts['strike']
                T = puts['dte'] / 365
                r = 0.05  # Risk-free rate (approximate)
                sigma = puts['impliedVolatility']
                
                d1 = (np.log(S/K) + (r + sigma**2/2)*T) / (sigma*np.sqrt(T))
                puts['delta'] = -norm.cdf(-d1)
            
            # Ensure all required columns are present
            if 'openInterest' in puts.columns:
                puts['open_interest'] = puts['openInterest']
            elif 'open_interest' not in puts.columns:
                puts['open_interest'] = 0
                
            if 'volume' not in puts.columns:
                puts['volume'] = 0
                
            all_options = pd.concat([all_options, puts])
            
            print(f"Found {len(puts)} put options for {symbol} expiring on {date}")
            
        except Exception as e:
            print(f"Error processing {symbol} for date {date}: {str(e)}")
            continue
    
    if not all_options.empty:
        print(f"Total {len(all_options)} put options found for {symbol}")
        print("Available columns:", all_options.columns.tolist())
    
    return all_options

def calculate_metrics(options_chain, current_price):
    # Calculate if option is out of the money (strike price below current price)
    options_chain['out_of_the_money'] = options_chain['strike'] < current_price
    
    # Get current date
    today = datetime.now().date()
    
    # Calculate days to expiration (DTE)
    options_chain['calendar_days'] = options_chain['expiry'].apply(
        lambda x: max((datetime.strptime(x, '%Y-%m-%d').date() - today).days + 1, 1)
    )
    
    # Calculate annualized return based on option premium
    BUSINESS_DAYS_PER_YEAR = 252  # Approximately 252 business days per year
    
    # Use calendar days for annualized return calculation
    options_chain['annualized_return'] = (
        options_chain['lastPrice'] / options_chain['strike'] * (BUSINESS_DAYS_PER_YEAR / options_chain['calendar_days']) * 100
    )
    
    return options_chain

def screen_options(options_df, config):
    criteria = config['screening_criteria']
    strategy = config['options_strategy']
    
    print("\nScreening options...")
    print(f"Initial data shape: {options_df.shape}")
    
    # Rename openInterest to open_interest if needed
    if 'openInterest' in options_df.columns and 'open_interest' not in options_df.columns:
        options_df['open_interest'] = options_df['openInterest']
    
    # Gradually apply filtering conditions and print results
    conditions = {
        'volume': options_df['volume'] >= strategy['min_volume'],
        'open_interest': options_df['open_interest'] >= strategy['min_open_interest'],
        'min_delta': options_df['delta'] >= criteria['min_delta'],
        'max_delta': options_df['delta'] <= criteria['max_delta'],
        'annualized_return': options_df['annualized_return'] >= criteria['min_annualized_return'],
        'out_of_the_money': options_df['out_of_the_money']
    }
    
    print("\nNumber of records meeting each condition:")
    for name, condition in conditions.items():
        print(f"{name}: {condition.sum()} records")
    
    filtered = options_df[
        conditions['volume'] &
        conditions['open_interest'] &
        conditions['min_delta'] &
        conditions['max_delta'] &
        conditions['annualized_return'] &
        conditions['out_of_the_money']
    ]
    
    print(f"\nFinal filtered data shape: {filtered.shape}")
    
    # Sort results
    sort_by = config['output']['sort_by']
    filtered = filtered.sort_values(
        by=sort_by,
        ascending=[config['output']['sort_order'] == 'ascending'] * len(sort_by)
    )
    
    return filtered.head(config['output']['max_results'])

def format_output(filtered_df):
    display_columns = [
        'symbol', 'strike', 'lastPrice', 'volume', 'open_interest',
        'impliedVolatility', 'delta', 'annualized_return', 'expiry', 'calendar_days'
    ]
    
    formatted = filtered_df[display_columns].copy()
    formatted['impliedVolatility'] = formatted['impliedVolatility'] * 100
    formatted['annualized_return'] = formatted['annualized_return'].round(2)
    formatted['impliedVolatility'] = formatted['impliedVolatility'].round(2)
    formatted['delta'] = formatted['delta'].round(3)
    
    print("\nFiltered DataFrame Info:")
    print(filtered_df.info())
    print("\nAvailable Columns:")
    print(filtered_df.columns.tolist())
    
    return formatted

def main():
    config = load_config()
    results = pd.DataFrame()
    
    for symbol in config['data']['symbols']:
        try:
            print(f"Processing {symbol}...")
            stock = yf.Ticker(symbol)
            current_price = stock.info['regularMarketPrice']
            
            options = get_options_chain(symbol, config)
            if not options.empty:
                options = calculate_metrics(options, current_price)
                filtered = screen_options(options, config)
                results = pd.concat([results, filtered])
        except Exception as e:
            print(f"Error processing {symbol}: {str(e)}")
    
    if not results.empty:
        results = format_output(results)
        print("\nTop Options Opportunities:")
        print(results.to_string(index=False))
    else:
        print("No options found matching the criteria.")

if __name__ == '__main__':
    main()
