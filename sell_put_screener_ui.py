import sys
import json
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QComboBox, QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox,
                             QHeaderView, QMessageBox, QTabWidget, QSplitter, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

# Import functions from existing options_screener module
from sell_put_screener import (
    load_config, get_options_chain, calculate_metrics,
    screen_options, format_output
)


class OptionsWorker(QThread):
    """Background thread for processing options data retrieval and screening"""
    finished = pyqtSignal(pd.DataFrame, str, bool)
    progress = pyqtSignal(str)
    
    def __init__(self, symbol, config):
        super().__init__()
        self.symbol = symbol
        self.config = config
        self._is_running = True
        
    def stop(self):
        self._is_running = False
        
    def run(self):
        try:
            import yfinance as yf
            self.progress.emit(f"Processing {self.symbol}...")
            
            if not self._is_running:
                return
                
            # Get stock price
            stock = yf.Ticker(self.symbol)
            current_price = stock.info['regularMarketPrice']
            
            if not self._is_running:
                return
                
            # Get options chain
            options = get_options_chain(self.symbol, self.config)
            
            if not self._is_running:
                return
                
            if options.empty:
                self.finished.emit(pd.DataFrame(), f"No options data found for {self.symbol}", False)
                return
                
            # Calculate metrics
            options = calculate_metrics(options, current_price)
            
            if not self._is_running:
                return
                
            # Screen options
            filtered = screen_options(options, self.config)
            
            # Format output
            formatted = format_output(filtered, current_price)
            if not formatted.empty:
                self.finished.emit(formatted, f"{self.symbol} processing complete, found {len(formatted)} qualifying options", True)
            else:
                self.finished.emit(pd.DataFrame(), f"No qualifying options found for {self.symbol}", False)
                
        except Exception as e:
            if self._is_running:
                self.finished.emit(pd.DataFrame(), f"Error processing {self.symbol}: {str(e)}", False)
        finally:
            self._is_running = False


class OptionsScreenerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.results = {}
        self.current_symbol = ""
        self.workers = []
        self.init_ui()
        
    def closeEvent(self, event):
        # Stop all running threads
        for worker in self.workers:
            worker.stop()
            worker.wait()
        event.accept()
        
    def screen_symbols(self, symbols):
        # Clear results dropdown
        self.results_combo.clear()
        # Clear previous results
        self.results = {}
        # Track the current batch of symbols
        self._current_symbols = list(symbols)
        # Stop all running threads
        for worker in self.workers:
            worker.stop()
            worker.wait()
        self.workers.clear()
        # Track how many workers are expected
        self._pending_workers = len(symbols)
        self._screening_all = len(symbols) > 1
        # Process stocks one by one
        for symbol in symbols:
            worker = OptionsWorker(symbol, self.config)
            worker.finished.connect(self.process_results)
            worker.progress.connect(lambda msg: self.status_bar.showMessage(msg))
            self.workers.append(worker)
            worker.start()
    
    def init_ui(self):
        self.setWindowTitle("Options Screener")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create top-bottom splitter
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # Top section - Control panel
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        splitter.addWidget(control_panel)
        
        # Create tabs
        tab_widget = QTabWidget()
        control_layout.addWidget(tab_widget)
        
        # Stock selection tab
        symbols_tab = QWidget()
        symbols_layout = QVBoxLayout(symbols_tab)
        tab_widget.addTab(symbols_tab, "Stock Symbols")
        
        # Stock symbol selection area
        symbols_group = QGroupBox("Stock Symbol Selection")
        symbols_form = QFormLayout(symbols_group)
        symbols_layout.addWidget(symbols_group)
        
        # Existing stock dropdown
        self.symbols_combo = QComboBox()
        self.symbols_combo.addItems(self.config['data']['symbols'])
        self.symbols_combo.currentTextChanged.connect(self.on_symbol_selected)
        symbols_form.addRow("Select Stock:", self.symbols_combo)
        
        # Add new stock
        add_symbol_layout = QHBoxLayout()
        self.new_symbol_input = QLineEdit()
        self.new_symbol_input.setPlaceholderText("Enter stock symbol (e.g., AAPL)")
        add_symbol_button = QPushButton("Add")
        add_symbol_button.clicked.connect(self.add_symbol)
        add_symbol_layout.addWidget(self.new_symbol_input)
        add_symbol_layout.addWidget(add_symbol_button)
        symbols_form.addRow("Add New Stock:", add_symbol_layout)
        
        # Screen button
        screen_button = QPushButton("Screen Selected Stock")
        screen_button.clicked.connect(self.screen_selected_symbol)
        screen_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        symbols_layout.addWidget(screen_button)
        
        # Screen all button
        screen_all_button = QPushButton("Screen All Stocks")
        screen_all_button.clicked.connect(self.screen_all_symbols)
        screen_all_button.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        symbols_layout.addWidget(screen_all_button)
        
        # Screening criteria tab
        criteria_tab = QWidget()
        criteria_layout = QVBoxLayout(criteria_tab)
        tab_widget.addTab(criteria_tab, "Screening Criteria")
        
        # Options strategy settings
        strategy_group = QGroupBox("Options Strategy Settings")
        strategy_form = QFormLayout(strategy_group)
        criteria_layout.addWidget(strategy_group)
        
        # Maximum days to expiration
        self.max_dte_spin = QSpinBox()
        self.max_dte_spin.setRange(1, 365)
        self.max_dte_spin.setValue(self.config['options_strategy']['max_dte'])
        strategy_form.addRow("Max Days to Expiration:", self.max_dte_spin)
        
        # Minimum days to expiration
        self.min_dte_spin = QSpinBox()
        self.min_dte_spin.setRange(0, 364)
        self.min_dte_spin.setValue(self.config['options_strategy'].get('min_dte', 0))
        strategy_form.addRow("Min Days to Expiration:", self.min_dte_spin)
        
        # Minimum volume
        self.min_volume_spin = QSpinBox()
        self.min_volume_spin.setRange(0, 10000)
        self.min_volume_spin.setValue(self.config['options_strategy']['min_volume'])
        strategy_form.addRow("Minimum Volume:", self.min_volume_spin)
        
        # Minimum open interest
        self.min_oi_spin = QSpinBox()
        self.min_oi_spin.setRange(0, 10000)
        self.min_oi_spin.setValue(self.config['options_strategy']['min_open_interest'])
        strategy_form.addRow("Minimum Open Interest:", self.min_oi_spin)
        
        # Screening criteria settings
        criteria_group = QGroupBox("Screening Criteria Settings")
        criteria_form = QFormLayout(criteria_group)
        criteria_layout.addWidget(criteria_group)
        
        # Minimum annualized return
        self.min_return_spin = QDoubleSpinBox()
        self.min_return_spin.setRange(0, 100)
        self.min_return_spin.setValue(self.config['screening_criteria']['min_annualized_return'])
        criteria_form.addRow("Min Annualized Return (%):", self.min_return_spin)
        
        # Delta range
        delta_layout = QHBoxLayout()
        self.min_delta_spin = QDoubleSpinBox()
        self.min_delta_spin.setRange(-1, 0)
        self.min_delta_spin.setSingleStep(0.05)
        self.min_delta_spin.setValue(self.config['screening_criteria']['min_delta'])
        
        self.max_delta_spin = QDoubleSpinBox()
        self.max_delta_spin.setRange(-1, 0)
        self.max_delta_spin.setSingleStep(0.05)
        self.max_delta_spin.setValue(self.config['screening_criteria']['max_delta'])
        
        delta_layout.addWidget(self.min_delta_spin)
        delta_layout.addWidget(QLabel("to"))
        delta_layout.addWidget(self.max_delta_spin)
        criteria_form.addRow("Delta Range:", delta_layout)
        
        # Save settings button
        save_settings_button = QPushButton("Save Settings")
        save_settings_button.clicked.connect(self.save_settings)
        criteria_layout.addWidget(save_settings_button)
        
        # Bottom section - Results display
        results_panel = QWidget()
        results_layout = QVBoxLayout(results_panel)
        splitter.addWidget(results_panel)
        
        # Results selection area
        results_header = QHBoxLayout()
        results_layout.addLayout(results_header)
        
        self.results_label = QLabel("Screening Results:")
        self.results_label.setFont(QFont("Arial", 12, QFont.Bold))
        results_header.addWidget(self.results_label)
        
        self.results_combo = QComboBox()
        self.results_combo.currentTextChanged.connect(self.display_results)
        results_header.addWidget(self.results_combo)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(False)  # Disable to avoid conflicts with cell colors
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        results_layout.addWidget(self.results_table)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Set splitter proportions
        splitter.setSizes([300, 500])
        
    def on_symbol_selected(self, symbol):
        self.current_symbol = symbol
        if symbol in self.results:
            self.display_results(symbol)
    
    def add_symbol(self):
        new_symbol = self.new_symbol_input.text().strip().upper()
        if not new_symbol:
            return
            
        if new_symbol in self.config['data']['symbols']:
            QMessageBox.information(self, "Info", f"{new_symbol} is already in the list")
            return
            
        # Add to config and dropdown
        self.config['data']['symbols'].append(new_symbol)
        self.symbols_combo.addItem(new_symbol)
        self.symbols_combo.setCurrentText(new_symbol)
        self.new_symbol_input.clear()
        
        # Save to config file
        self.save_config()
        self.status_bar.showMessage(f"Added {new_symbol} to stock list")
    
    def save_settings(self):
        # Update config
        self.config['options_strategy']['max_dte'] = self.max_dte_spin.value()
        self.config['options_strategy']['min_dte'] = self.min_dte_spin.value()
        self.config['options_strategy']['min_volume'] = self.min_volume_spin.value()
        self.config['options_strategy']['min_open_interest'] = self.min_oi_spin.value()
        self.config['screening_criteria']['min_annualized_return'] = self.min_return_spin.value()
        self.config['screening_criteria']['min_delta'] = self.min_delta_spin.value()
        self.config['screening_criteria']['max_delta'] = self.max_delta_spin.value()
        # Save to config file
        self.save_config()
        self.status_bar.showMessage("Settings saved")
    
    def save_config(self):
        try:
            import os
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save config: {str(e)}")
            self.status_bar.showMessage(f"Failed to save config: {str(e)}")
    
    def screen_selected_symbol(self):
        symbol = self.symbols_combo.currentText()
        if not symbol:
            return
            
        self.status_bar.showMessage(f"Processing {symbol}...")
        self.screen_symbols([symbol])
    
    def screen_all_symbols(self):
        symbols = self.config['data']['symbols']
        if not symbols:
            QMessageBox.information(self, "Info", "No stock symbols available")
            return
            
        self.status_bar.showMessage("Processing all stocks...")
        self.screen_symbols(symbols)
    
    def process_results(self, df, message, success):
        self.status_bar.showMessage(message)
        
        if success:
            symbol = self.current_symbol
            if not df.empty:
                symbol = df['symbol'].iloc[0]
                self.results[symbol] = df
                if symbol not in [self.results_combo.itemText(i) for i in range(self.results_combo.count())]:
                    self.results_combo.addItem(symbol)
        # Decrement pending workers
        if hasattr(self, '_pending_workers'):
            self._pending_workers -= 1
        # Only build summary after all workers finish and if screening all
        if hasattr(self, '_pending_workers') and self._pending_workers == 0 and getattr(self, '_screening_all', False):
            summary_rows = []
            for sym in self._current_symbols:
                df = self.results.get(sym)
                if df is not None and not df.empty:
                    summary_rows.append(df.iloc[0])
            if summary_rows:
                summary_df = pd.DataFrame(summary_rows)
                self.results['Summary'] = summary_df
                if 'Summary' not in [self.results_combo.itemText(i) for i in range(self.results_combo.count())]:
                    self.results_combo.insertItem(0, 'Summary')
                self.results_combo.setCurrentText('Summary')
                self.display_results('Summary')
        elif not getattr(self, '_screening_all', False) and success and not df.empty:
            # For single symbol, show results immediately
            self.results_combo.setCurrentText(symbol)
            self.display_results(symbol)

    def display_results(self, symbol):
        if not symbol or symbol not in self.results:
            return
        df = self.results[symbol]
        if df.empty:
            return
        try:
            label = 'Screening Results:' if symbol == 'Summary' else f"{symbol} Screening Results:"
            self.results_label.setText(label)
            self.results_table.clear()
            self.results_table.setRowCount(len(df))
            self.results_table.setColumnCount(len(df.columns))
            column_headers = {
                'symbol': 'Symbol',
                'current_price': 'Current Price',
                'strike': 'Strike Price',
                'lastPrice': 'Option Price', 
                'volume': 'Volume',
                'open_interest': 'Open Interest',
                'impliedVolatility': 'Implied Volatility (%)',
                'delta': 'Delta',
                'annualized_return': 'Annualized Return (%)',
                'expiry': 'Expiration Date',
                'calendar_days': 'DTE'
            }
            headers = [column_headers.get(col, col) for col in df.columns]
            self.results_table.setHorizontalHeaderLabels(headers)
            for i in range(len(df)):
                for j in range(len(df.columns)):
                    value = df.iloc[i, j]
                    if isinstance(value, (float, int)):
                        text = f"{value:.3f}" if df.columns[j] == 'delta' else f"{value:.2f}"
                        item = QTableWidgetItem(text)
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item = QTableWidgetItem(str(value))
                        item.setTextAlignment(Qt.AlignCenter)
                    if df.columns[j] == 'annualized_return':
                        if value >= 50:
                            item.setBackground(QColor(76, 175, 80))
                            item.setForeground(QColor(255, 255, 255))
                        elif value >= 30:
                            item.setBackground(QColor(255, 193, 7))
                            item.setForeground(QColor(0, 0, 0))
                        else:
                            item.setBackground(QColor(255, 255, 255))
                            item.setForeground(QColor(0, 0, 0))
                    self.results_table.setItem(i, j, item)
            self.results_table.resizeColumnsToContents()
            self.status_bar.showMessage(f"Displaying {len(df)} options results for {label}")
        except Exception as e:
            self.status_bar.showMessage(f"Error displaying results: {str(e)}")
            print(f"Error displaying results: {str(e)}")


def main():
    app = QApplication(sys.argv)
    window = OptionsScreenerUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()