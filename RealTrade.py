import mexc_api.spot
from mexc_api.common.enums import OrderType, Side
from Scraping import Interface
from Trade import Trade

import time
import schedule
import logging


class RealTrade:
    def __init__(self, config):
        self.config = config
        self.api_keys = input("请输入API Key，放心，不会被记录的：")
        self.api_secrets = input("请输入API Secret，放心，同样不会被记录的：")
        self.balance = float(input("请输入划转初始资金，请保证您的账户余额大于输入值，否则可能导致交易失败："))
        self.test = input("是否进行测试？(y/n)")
        while self.test.lower() != 'y' and self.test.lower() != 'n':
            print("输入错误，请重新输入")
            self.test = input("是否进行测试？(y/n)")
        self.manual = input("是否手动确认交易？(y/n)")
        while self.manual.lower() != 'y' and self.manual.lower() != 'n':
            print("输入错误，请重新输入")
            self.manual = input("是否手动确认交易？(y/n)")

    def run(self):
        if self.config.get('trade', 'platform') == 'mexc':
            spot = mexc_api.spot.Spot(self.api_keys, self.api_secrets)
        elif self.config.get('trade', 'platform') == 'bybit':
            pass
        scraper = Interface(self.config, data_length=self.config.getint('RealTrade', 'data_length'))
        trade = Trade(self.config, self.balance, self.balance)
        scraper.coins = [coin.name for coin in trade.coins_list]

        # Create two threads, one for trading, another for monitoring user input
        def trading():
            while True:
                scraper.run()
                data = scraper.data
                trade.run(self.config.getint('RealTrade', 'data_length'), data)
                for coin in trade.coins_list:
                    for _ in range(5):
                        try:
                            if coin.switch == 'BUY':
                                if self.test.lower() == 'y':
                                    spot.account.test_new_order(symbol=coin.name, side=Side.BUY, order_type=OrderType.MARKET,
                                                                quote_order_quantity=str(coin.value))
                                    logging.info(f'测试交易成功，交易币种为{coin.name}，交易金额为{coin.value}，交易类型为买入')
                                elif self.test == 'n':
                                    if self.manual.lower() == 'y':
                                        if input(f'是否确认买入{coin.name}，交易金额为{coin.value}？(y/n)').lower() == 'y':
                                            spot.account.new_order(symbol=coin.name, side=Side.BUY, order_type=OrderType.MARKET,
                                                                   quote_order_quantity=str(coin.value))
                                            logging.info(f'交易成功，交易币种为{coin.name}，交易金额为{coin.value}，交易类型为买入')
                                        else:
                                            break
                                    elif self.manual.lower() == 'n':
                                        spot.account.new_order(symbol=coin.name, side=Side.BUY, order_type=OrderType.MARKET,
                                                               quote_order_quantity=str(coin.value))
                                        logging.info(f'交易成功，交易币种为{coin.name}，交易金额为{coin.value}，交易类型为买入')

                            elif coin.switch == 'SELL':
                                if self.test.lower() == 'y':
                                    spot.account.test_new_order(symbol=coin.name, side=Side.SELL, order_type=OrderType.MARKET,
                                                                quantity=str(coin.value_before_sell / coin.current_price))
                                    logging.info(f'测试交易成功，交易币种为{coin.name}，交易金额为{coin.value_before_sell}，交易类型为卖出')
                                elif self.test.lower() == 'n':
                                    if self.manual.lower() == 'y':
                                        if input(f'是否确认卖出{coin.name}，交易金额为{coin.value}，交易数量为{float(coin.value_before_sell) / float(coin.current_price)}？(y/n)').lower() == 'y':
                                            spot.account.new_order(symbol=coin.name, side=Side.SELL, order_type=OrderType.MARKET,
                                                                   quantity=str(coin.value_before_sell / coin.current_price))
                                            logging.info(f'交易成功，交易币种为{coin.name}，交易金额为{coin.value_before_sell}，交易类型为卖出')
                                        else:
                                            break
                                    elif self.manual.lower() == 'n':
                                        spot.account.new_order(symbol=coin.name, side=Side.SELL, order_type=OrderType.MARKET,
                                                               quantity=str(coin.value_before_sell / coin.current_price))
                                        logging.info(f'交易成功，交易币种为{coin.name}，交易金额为{coin.value_before_sell}，交易类型为卖出')

                            break
                        except Exception as e:
                            logging.error(e)
                            logging.error(f'交易失败，重试中，重试次数为{_}')
                            if _ == 4:
                                logging.error(f'交易失败，重试次数超过上限，跳过此次交易')
                                break
                            else:
                                continue

                for strategy in trade.strategies:
                    print(f'{strategy.__class__.__name__}持仓情况：')
                    for coin in trade.running_coins_dict[strategy.__class__.__name__]:
                        print(f'{coin.name}：{coin.value}')
                print(f'\n当前价值：{trade.value}，当前余额：{trade.balance}')

                while True:
                    print(f'\r{time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}', end='')
                    if time.gmtime().tm_min in [4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59] and time.gmtime().tm_sec >= 58:
                        break
                    time.sleep(1)

        while True:
            print(f'\r等待第一个交易时间点：{time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}', end='')
            if time.gmtime().tm_min in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55] and time.gmtime().tm_sec == 0:
                schedule.every(5).minutes.at(":00").do(trading)
                trading()
                break
            time.sleep(1)
        while True:
            schedule.run_pending()
            time.sleep(1)
