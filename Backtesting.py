import pandas as pd

from Scraping import Interface
from Trade import Trade
from Plot import Plot

import logging
import time


class Backtesting:

    def __init__(self, config):
        self.config = config
        self.balance = float(config.get('Backtesting', 'balance'))

    def run(self):
        if self.config.getint('Backtesting', 'data_length') <= 1000:
            scraper = Interface(self.config, data_length=self.config.getint('Backtesting', 'data_length'))
            scraper.run()
            data = scraper.data
        else:
            scraper = Interface(self.config, data_length=1000)
            request_times = self.config.getint('Backtesting', 'data_length') // 1000
            data = {}
            start_time = scraper.get_server_time() - request_times * 1000 * 60 * 1000
            for _ in range(request_times):
                scraper.run(start_time)
                for key in scraper.data.keys():
                    if key in data:
                        data[key] = data[key] + scraper.data[key]
                    else:
                        data[key] = scraper.data[key]
                start_time += 1000 * 60 * 1000
                time.sleep(5)
        trade = Trade(self.config, self.balance, self.balance)
        count = 2
        while True:
            try:
                trade.run(count, data)
                print(f'当前价值：{trade.value}，当前余额：{trade.balance}')
                count += 1
            except IndexError:
                break
        logging.info(f'回测结束，最终价值为{trade.value}，最终余额为{trade.balance}')
        if input('是否查看交易历史k线？(y/n)').lower() == 'y':
            while True:
                coin = input('请输入币种：')
                if coin in [target_coin.get_name() for target_coin in trade.coins_list]:
                    df = pd.DataFrame(data[coin], columns=['open_time', 'open', 'high', 'low', 'close', 'volume',
                                                           'close_time', 'quote_asset_volume'])
                    k_df = df[['open_time', 'open', 'high', 'low', 'close', 'volume']]
                    k_df = k_df.astype(float)
                    k_df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
                    plot = Plot(k_df)
                    plot.plot()
                    for count in range(2, len(k_df) + 1):
                        try:
                            trade_history = trade.trade_history[count][coin]
                            print(f'{k_df["open_time"][count]}，{coin}，{trade_history["action"]}，价格：{trade_history["price"]}，')
                            plot.arrows((k_df['open_time'][count], 0.95 * float(min(k_df['open']))), trade_history['action'])

                        except KeyError:
                            continue
                    plot.show()
                else:
                    print('币种不存在，请重新输入')
                    continue
                if input('是否继续查看交易历史k线？(y/n)').lower() == 'n':
                    break
        else:
            pass


if __name__ == '__main__':
    from Initialize import Initialize
    init = Initialize()
    config = init.config
    backtesting = Backtesting(config)
    backtesting.run()
