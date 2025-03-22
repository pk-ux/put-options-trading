import sys
import json
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QComboBox, QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox,
                             QHeaderView, QMessageBox, QTabWidget, QSplitter, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

# 导入现有的options_screener模块中的函数
from options_screener import (
    load_config, get_options_chain, calculate_metrics,
    screen_options, format_output
)


class OptionsWorker(QThread):
    """后台线程处理期权数据获取和筛选"""
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
            self.progress.emit(f"正在处理 {self.symbol}...")
            
            if not self._is_running:
                return
                
            # 获取股票价格
            stock = yf.Ticker(self.symbol)
            current_price = stock.info['regularMarketPrice']
            
            if not self._is_running:
                return
                
            # 获取期权链
            options = get_options_chain(self.symbol, self.config)
            
            if not self._is_running:
                return
                
            if options.empty:
                self.finished.emit(pd.DataFrame(), f"未找到 {self.symbol} 的期权数据", False)
                return
                
            # 计算指标
            options = calculate_metrics(options, current_price)
            
            if not self._is_running:
                return
                
            # 筛选期权
            filtered = screen_options(options, self.config)
            
            # 格式化输出
            formatted = format_output(filtered)
            if not formatted.empty:
                self.finished.emit(formatted, f"{self.symbol} 处理完成，找到{len(formatted)}个符合条件的期权", True)
            else:
                self.finished.emit(pd.DataFrame(), f"没有找到符合条件的 {self.symbol} 期权", False)
                
        except Exception as e:
            if self._is_running:
                self.finished.emit(pd.DataFrame(), f"处理 {self.symbol} 时出错: {str(e)}", False)
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
        # 停止所有运行中的线程
        for worker in self.workers:
            worker.stop()
            worker.wait()
        event.accept()
        
    def screen_symbols(self, symbols):
        # 清空结果下拉框
        self.results_combo.clear()
        
        # 停止所有运行中的线程
        for worker in self.workers:
            worker.stop()
            worker.wait()
        self.workers.clear()
        
        # 逐个处理股票
        for symbol in symbols:
            worker = OptionsWorker(symbol, self.config)
            worker.finished.connect(self.process_results)
            worker.progress.connect(lambda msg: self.status_bar.showMessage(msg))
            self.workers.append(worker)
            worker.start()
    
    def init_ui(self):
        self.setWindowTitle("期权筛选器")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建上下分割区域
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # 上部分 - 控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        splitter.addWidget(control_panel)
        
        # 创建标签页
        tab_widget = QTabWidget()
        control_layout.addWidget(tab_widget)
        
        # 标的选择标签页
        symbols_tab = QWidget()
        symbols_layout = QVBoxLayout(symbols_tab)
        tab_widget.addTab(symbols_tab, "股票标的")
        
        # 股票标的选择区域
        symbols_group = QGroupBox("股票标的选择")
        symbols_form = QFormLayout(symbols_group)
        symbols_layout.addWidget(symbols_group)
        
        # 现有股票下拉框
        self.symbols_combo = QComboBox()
        self.symbols_combo.addItems(self.config['data']['symbols'])
        self.symbols_combo.currentTextChanged.connect(self.on_symbol_selected)
        symbols_form.addRow("选择股票:", self.symbols_combo)
        
        # 添加新股票
        add_symbol_layout = QHBoxLayout()
        self.new_symbol_input = QLineEdit()
        self.new_symbol_input.setPlaceholderText("输入股票代码 (例如: AAPL)")
        add_symbol_button = QPushButton("添加")
        add_symbol_button.clicked.connect(self.add_symbol)
        add_symbol_layout.addWidget(self.new_symbol_input)
        add_symbol_layout.addWidget(add_symbol_button)
        symbols_form.addRow("添加新股票:", add_symbol_layout)
        
        # 筛选按钮
        screen_button = QPushButton("筛选所选股票")
        screen_button.clicked.connect(self.screen_selected_symbol)
        screen_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        symbols_layout.addWidget(screen_button)
        
        # 筛选所有按钮
        screen_all_button = QPushButton("筛选所有股票")
        screen_all_button.clicked.connect(self.screen_all_symbols)
        screen_all_button.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        symbols_layout.addWidget(screen_all_button)
        
        # 筛选条件标签页
        criteria_tab = QWidget()
        criteria_layout = QVBoxLayout(criteria_tab)
        tab_widget.addTab(criteria_tab, "筛选条件")
        
        # 期权策略设置
        strategy_group = QGroupBox("期权策略设置")
        strategy_form = QFormLayout(strategy_group)
        criteria_layout.addWidget(strategy_group)
        
        # 最大到期天数
        self.max_dte_spin = QSpinBox()
        self.max_dte_spin.setRange(1, 365)
        self.max_dte_spin.setValue(self.config['options_strategy']['max_dte'])
        strategy_form.addRow("最大到期天数:", self.max_dte_spin)
        
        # 最小成交量
        self.min_volume_spin = QSpinBox()
        self.min_volume_spin.setRange(0, 10000)
        self.min_volume_spin.setValue(self.config['options_strategy']['min_volume'])
        strategy_form.addRow("最小成交量:", self.min_volume_spin)
        
        # 最小未平仓量
        self.min_oi_spin = QSpinBox()
        self.min_oi_spin.setRange(0, 10000)
        self.min_oi_spin.setValue(self.config['options_strategy']['min_open_interest'])
        strategy_form.addRow("最小未平仓量:", self.min_oi_spin)
        
        # 筛选条件设置
        criteria_group = QGroupBox("筛选条件设置")
        criteria_form = QFormLayout(criteria_group)
        criteria_layout.addWidget(criteria_group)
        
        # 最小年化回报率
        self.min_return_spin = QDoubleSpinBox()
        self.min_return_spin.setRange(0, 100)
        self.min_return_spin.setValue(self.config['screening_criteria']['min_annualized_return'])
        criteria_form.addRow("最小年化回报率(%):", self.min_return_spin)
        
        # Delta范围
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
        delta_layout.addWidget(QLabel("至"))
        delta_layout.addWidget(self.max_delta_spin)
        criteria_form.addRow("Delta范围:", delta_layout)
        
        # 保存设置按钮
        save_settings_button = QPushButton("保存设置")
        save_settings_button.clicked.connect(self.save_settings)
        criteria_layout.addWidget(save_settings_button)
        
        # 下部分 - 结果显示
        results_panel = QWidget()
        results_layout = QVBoxLayout(results_panel)
        splitter.addWidget(results_panel)
        
        # 结果选择区域
        results_header = QHBoxLayout()
        results_layout.addLayout(results_header)
        
        self.results_label = QLabel("筛选结果:")
        self.results_label.setFont(QFont("Arial", 12, QFont.Bold))
        results_header.addWidget(self.results_label)
        
        self.results_combo = QComboBox()
        self.results_combo.currentTextChanged.connect(self.display_results)
        results_header.addWidget(self.results_combo)
        
        # 结果表格
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        results_layout.addWidget(self.results_table)
        
        # 状态栏
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")
        
        # 设置分割器比例
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
            QMessageBox.information(self, "提示", f"{new_symbol} 已在列表中")
            return
            
        # 添加到配置和下拉框
        self.config['data']['symbols'].append(new_symbol)
        self.symbols_combo.addItem(new_symbol)
        self.symbols_combo.setCurrentText(new_symbol)
        self.new_symbol_input.clear()
        
        # 保存到配置文件
        self.save_config()
        self.status_bar.showMessage(f"已添加 {new_symbol} 到股票列表")
    
    def save_settings(self):
        # 更新配置
        self.config['options_strategy']['max_dte'] = self.max_dte_spin.value()
        self.config['options_strategy']['min_volume'] = self.min_volume_spin.value()
        self.config['options_strategy']['min_open_interest'] = self.min_oi_spin.value()
        
        self.config['screening_criteria']['min_annualized_return'] = self.min_return_spin.value()
        self.config['screening_criteria']['min_delta'] = self.min_delta_spin.value()
        self.config['screening_criteria']['max_delta'] = self.max_delta_spin.value()
        
        # 保存到配置文件
        self.save_config()
        self.status_bar.showMessage("设置已保存")
    
    def save_config(self):
        try:
            import os
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存配置失败: {str(e)}")
            self.status_bar.showMessage(f"保存配置失败: {str(e)}")
    
    def screen_selected_symbol(self):
        symbol = self.symbols_combo.currentText()
        if not symbol:
            return
            
        self.status_bar.showMessage(f"正在处理 {symbol}...")
        self.screen_symbols([symbol])
    
    def screen_all_symbols(self):
        symbols = self.config['data']['symbols']
        if not symbols:
            QMessageBox.information(self, "提示", "没有可用的股票标的")
            return
            
        self.status_bar.showMessage("正在处理所有股票...")
        self.screen_symbols(symbols)
    
    def process_results(self, df, message, success):
        self.status_bar.showMessage(message)
        
        if success:
            # 从消息中提取股票代码
            symbol = self.current_symbol
            if not df.empty:
                symbol = df['symbol'].iloc[0]
                self.results[symbol] = df
                
                # 更新结果下拉框
                if symbol not in [self.results_combo.itemText(i) for i in range(self.results_combo.count())]:
                    self.results_combo.addItem(symbol)
                    
                # 如果是当前选中的股票，立即显示结果
                if symbol == self.current_symbol or self.results_combo.count() == 1:
                    self.results_combo.setCurrentText(symbol)
                    self.display_results(symbol)
            else:
                # 仅在状态栏显示消息，不弹出对话框
                self.status_bar.showMessage(f"没有找到符合条件的{symbol}期权")
        else:
            self.status_bar.showMessage(message)
    
    def display_results(self, symbol):
        if not symbol or symbol not in self.results:
            return
            
        df = self.results[symbol]
        if df.empty:
            return
            
        try:
            # 更新标签
            self.results_label.setText(f"{symbol} 筛选结果:")
            
            # 设置表格
            self.results_table.clear()
            self.results_table.setRowCount(len(df))
            self.results_table.setColumnCount(len(df.columns))
            
            # 设置表头
            column_headers = {
                'symbol': '股票代码',
                'strike': '行权价',
                'lastPrice': '期权价格', 
                'volume': '成交量',
                'open_interest': '未平仓量',
                'impliedVolatility': '隐含波动率(%)',
                'delta': 'Delta',
                'annualized_return': '年化收益率(%)',
                'expiry': '到期日',
                'calendar_days': '日历天数',
                'remaining_business_days': '剩余交易日'
            }
            
            headers = [column_headers.get(col, col) for col in df.columns]
            self.results_table.setHorizontalHeaderLabels(headers)
            
            # 填充数据
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
                        
                    # 为年化收益率添加颜色
                    if df.columns[j] == 'annualized_return':
                        if value >= 50:
                            item.setBackground(QColor(144, 238, 144))  # 浅绿色
                        elif value >= 30:
                            item.setBackground(QColor(255, 255, 224))  # 浅黄色
                            
                    self.results_table.setItem(i, j, item)
                    
            # 调整列宽
            self.results_table.resizeColumnsToContents()
            
            # 更新状态栏
            self.status_bar.showMessage(f"显示 {symbol} 的 {len(df)} 个期权结果")
        except Exception as e:
            self.status_bar.showMessage(f"显示结果时出错: {str(e)}")
            print(f"显示结果时出错: {str(e)}")


def main():
    app = QApplication(sys.argv)
    window = OptionsScreenerUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()