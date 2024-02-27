from mexc_api import spot
from mexc_api.common.enums import Interval

import time
import json
import logging


class Interface:

    def __init__(self, config, data_length=1000):
        self.config = config
        self.platform = config.get('Platform', 'platform')
        self.coins = list(set([coin for strategy in json.loads(config.get('Trade', 'strategy_coin')).values() for coin
                               in strategy]))
        self.use_interface = config.get('Scraping', 'use_interface')
        self.data_length = data_length
        self.data = None

    def run(self, start_ms=None):
        try:
            import apikeys
            self.data = {}
            if self.platform == 'mexc':
                mexc = spot.Spot(apikeys.mexc_api_key, apikeys.mexc_secret_key)
                for coin in self.coins:
                    if start_ms:
                        self.data[coin] = mexc.market.klines(symbol=coin, interval=Interval.FIVE_MIN,
                                                             limit=self.data_length, start_ms=start_ms)
                    else:
                        self.data[coin] = mexc.market.klines(symbol=coin, interval=Interval.FIVE_MIN,
                                                             limit=self.data_length)
            elif self.platform == 'bybit':
                pass

        except Exception as e:
            logging.error(e)
            time.sleep(5)
            self.run()

    def get_server_time(self):
        try:
            import apikeys
            mexc = spot.Spot(apikeys.mexc_api_key, apikeys.mexc_secret_key)
            return mexc.market.server_time()
        except Exception as e:
            logging.error(e)
            time.sleep(5)
            self.get_server_time()


if __name__ == '__main__':
    from Initialize import Initialize
    init = Initialize()
    config = init.config
    interface = Interface(config)
    interface.run()
