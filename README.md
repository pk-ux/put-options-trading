# Sell Put Screener / 卖出看跌期权筛选器

## Overview / 概述
This application is a powerful put option selling screener that helps traders identify potential cash-secured sell put trades based on customizable criteria. The tool provides a user-friendly interface for screening put options across multiple stock symbols, with detailed metrics and color code of results.

这个应用程序是一个强大的卖出看跌期权筛选工具，帮助交易者根据自定义标准识别潜在的现金担保卖出看跌期权交易。该工具提供了用户友好的界面，可以跨多个股票代码筛选看跌期权，并提供详细的指标和结果颜色编码。

## Features / 功能

### Stock Symbol Management / 股票代码管理
- Select from existing stock symbols / 从现有股票代码中选择
- Add new stock symbols to the screening list / 向筛选列表添加新的股票代码
- Screen individual stocks or all stocks in your list / 筛选单个股票或列表中的所有股票

### Customizable Screening Criteria / 自定义筛选条件
- **Options Strategy Settings / 期权策略设置**
  - Maximum calendar days to expiration (DTE) / 最大到期天数
  - Minimum volume requirements / 最小成交量要求
  - Minimum open interest thresholds / 最小未平仓量阈值

- **Performance Criteria / 性能标准**
  - Minimum annualized return percentage / 最小年化回报率百分比
  - Delta range selection (for risk management) / Delta范围选择（用于风险管理）

### Results Display / 结果显示
- Comprehensive table view of filtered put options / 筛选后的看跌期权综合表格视图
- Key metrics displayed for each option / 每个期权显示的关键指标:
  - Strike price / 行权价
  - Option price / 期权价格
  - Volume and open interest / 成交量和未平仓量
  - Implied volatility / 隐含波动率
  - Delta / Delta值
  - Annualized return percentage / 年化回报率百分比
  - Expiration date / 到期日
  - Calendar days and remaining business days / 日历天数和剩余交易日

- Color-coded results highlighting high-potential trades / 颜色编码结果突出显示高潜力交易:
  - Green highlighting for options with ≥50% annualized returns / 年化回报率≥50%的期权以绿色突出显示
  - Yellow highlighting for options with ≥30% annualized returns / 年化回报率≥30%的期权以黄色突出显示

### Background Processing / 后台处理
- Multi-threaded design for processing multiple stocks simultaneously / 多线程设计，同时处理多个股票
- Real-time progress updates in the status bar / 状态栏中的实时进度更新
- Non-blocking UI during data retrieval and processing / 数据检索和处理期间的非阻塞UI

## Technical Details / 技术细节
- Built with PyQt5 for the user interface / 使用PyQt5构建用户界面
- Utilizes yfinance for retrieving options data / 利用yfinance检索期权数据
- Implements QThread for background processing / 实现QThread进行后台处理
- Configuration saved in JSON format for persistence / 配置以JSON格式保存以实现持久性

## Getting Started / 入门指南
1. Launch the application / 启动应用程序
2. Add your desired stock symbols / 添加您想要的股票代码
3. Adjust screening criteria to match your put-selling strategy / 调整筛选条件以匹配您的看跌期权卖出策略
4. Click "Screen Selected Stock" or "Screen All Stocks" / 点击"筛选所选股票"或"筛选所有股票"
5. Review the filtered put options in the results table / 在结果表中查看筛选后的看跌期权

### Launch Using Batch File / 使用批处理文件启动
You can also use the included batch file to launch the application. Simply double-click on `run_sell_put_screener.bat` to start the program. Note that you may need to modify the path in the batch file to match your installation location.

您也可以使用包含的批处理文件来启动应用程序。只需双击`run_sell_put_screener.bat`即可启动程序。请注意，您可能需要修改批处理文件中的路径以匹配您的安装位置。


## Requirements / 系统要求
- Python 3.6+
- PyQt5
- pandas
- yfinance

## Configuration / 配置
The application saves your settings in a config.json file, including: / 应用程序将您的设置保存在config.json文件中，包括:
- List of stock symbols / 股票代码列表
- Options strategy parameters / 期权策略参数
- Screening criteria thresholds / 筛选条件阈值

This allows your preferences to persist between sessions. / 这使您的偏好设置在会话之间保持不变。