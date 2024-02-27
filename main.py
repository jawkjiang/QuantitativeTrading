import Backtesting
import RealTrade
import Initialize
import logging

init = Initialize.Initialize()
config = init.config

if input("进行回测？（回测将会使用您在配置文件中设置的初始资金进行回测，回测结束后将会输出最终价值和最终余额）(y/n)").lower() == 'y':
    backtesting = Backtesting.Backtesting(config)
    backtesting.run()

if input("进行实盘交易？（实盘交易将会使用您在配置文件中设置的初始资金进行实盘交易，实盘交易将会持续运行，直到您输入exit命令，或者按下Ctrl+C）(y/n)").lower() == 'y':
    real_trade = RealTrade.RealTrade(config)
    real_trade.run()

logging.info('程序结束')
