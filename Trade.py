import time

import Strategy
from Coin import Coin

import json
import pandas as pd


class Trade:
    def __init__(self, config, value, balance):
        self.config = config
        self.strategy_coin_dict = json.loads(config.get('Trade', 'strategy_coin'))
        self.strategy_names = self.strategy_coin_dict.keys()
        self.strategies = [getattr(Strategy, strategy_name)(config) for strategy_name in self.strategy_names]
        self.running_coins_num_dict = json.loads(config.get('Trade', 'running_coins_num'))
        self.value_distribution_dict = json.loads(config.get('Trade', 'value_distribution'))

        self.value = value
        self.balance = balance

        self.stop_loss = float(config.get('Trade', 'stop_loss'))
        self.stop_loss_for_each = float(config.get('Trade', 'stop_loss_for_each'))
        self.take_profit = float(config.get('Trade', 'take_profit'))
        self.commission = float(config.get('Trade', 'commission'))

        self.coins_iter_dict = {}
        self.running_coins_dict = {}
        for strategy in self.strategies:
            coins = [Coin(coin) for coin in list(self.strategy_coin_dict[strategy.__class__.__name__])]
            coins_iter = iter(coins)
            self.coins_iter_dict[strategy.__class__.__name__] = coins_iter
            self.running_coins_dict[strategy.__class__.__name__] = [next(coins_iter) for _ in range(
                self.running_coins_num_dict[strategy.__class__.__name__])]
        self.coins_list = [coin for strategy in self.strategies for coin in
                           self.running_coins_dict[strategy.__class__.__name__]]
        self.trade_history = {}

        self.running_counter = 0

    def run(self, count, data):

        for strategy in self.strategies:

            running_coins_num = int(self.running_coins_num_dict[strategy.__class__.__name__])
            value_distribution = float(self.value_distribution_dict[strategy.__class__.__name__])
            share_ratio = value_distribution / running_coins_num
            self.trade_history[count] = {}

            for coin in self.running_coins_dict[strategy.__class__.__name__]:
                if count < strategy.basisLen:
                    df = data[coin.name][:count]
                else:
                    df = data[coin.name][count - strategy.basisLen:count]
                    if len(df) < strategy.basisLen:
                        raise IndexError
                df = pd.DataFrame(df, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                                               'quote_asset_volume'])
                strategy.run(df)
                coin.realtime_value(self.stop_loss_for_each, float(df.iloc[-1]["open"]))

                if strategy.__class__.__name__ == 'SAS':
                    if self.running_counter == 0:
                        strategy.last_trade_time = df.iloc[-1]["open_time"]
                    elif int(df.iloc[-1]["open_time"]) - int(strategy.last_trade_time) < strategy.period * 60000:
                        continue
                    else:
                        strategy.last_trade_time = df.iloc[-1]["open_time"]

                if coin.Liquidation:
                    self.balance += float(coin.value) * (1 - self.commission)
                    coin.sell(coin.current_price)
                    print(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}, 第{count}根k线，强制平仓，{coin.name}，'
                          f'当前价格：{coin.current_price}，当前流动资金：{self.balance}')
                    self.running_coins_dict[strategy].remove(coin)
                    self.running_coins_dict[strategy].append(next(self.coins_iter_dict[strategy]))
                    self.coins_list = [coin for strategy in self.strategies for coin in
                                       self.running_coins_dict[strategy.__class__.__name__]]
                    self.trade_history[count][coin.name] = {'action': 'LIQUIDATION', 'price': coin.current_price,
                                                            'value': coin.value_before_sell}
                    continue

                if strategy.action == 'OPEN':
                    if coin.action == 'CLOSED':
                        if self.balance >= self.value * share_ratio:
                            coin.buy(self.value * share_ratio * (1 - self.commission), coin.current_price)
                            self.balance -= self.value * share_ratio
                            print(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}, 第{count}根k线，'
                                  f'{strategy.__class__.__name__}，开盘，{coin.name}，'
                                  f'当前价格：{coin.current_price}，当前货币市值：{coin.value}，当前流动资金：{self.balance}')
                            self.trade_history[count][coin.name] = {'action': 'OPEN', 'price': coin.current_price,
                                                                    'value': coin.value}
                        else:
                            print(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}, 第{count}根k线，'
                                  f'{strategy.__class__.__name__}，尝试开盘失败，'
                                  f'{coin.name}，当前价格：{coin.current_price}，余额不足')
                    else:
                        print(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}, 第{count}根k线，'
                              f'{strategy.__class__.__name__}，尝试开盘失败，'
                              f'{coin.name}，当前价格：{coin.current_price}，已经开盘')

                elif strategy.action == 'CLOSE':
                    if coin.action == 'OPENED':
                        self.balance += float(coin.value) * (1 - self.commission)
                        coin.sell(df.iloc[-1]["open"])
                        print(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}, 第{count}根k线，'
                              f'{strategy.__class__.__name__}，收盘，{coin.name}，'
                              f'当前价格：{coin.current_price}，当前流动资金：{self.balance}')
                        self.trade_history[count][coin.name] = {'action': 'CLOSE', 'price': coin.current_price,
                                                                'value': coin.value_before_sell}
                    else:
                        print(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}, 第{count}根k线，'
                              f'{strategy.__class__.__name__}，尝试收盘失败，{coin.name}，'
                              f'当前价格：{coin.current_price}，已经收盘')

                else:
                    pass

        self.value = self.balance + sum([coin.value for coin in self.coins_list])
        if self.stop_loss != 0 and self.value < (1 - self.stop_loss) * self.balance:
            self.liquidate(count)
        self.running_counter += 1

        return self.value, self.balance

    def liquidate(self, count):
        for coin in self.coins_list:
            if coin.action == 'OPEN':
                self.balance += float(coin.value) * (1 - self.commission)
                coin.sell(coin.current_price)
        print(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}, 第{count}根k线，强制平仓，当前价值低于止损线，程序退出')
        exit(0)
