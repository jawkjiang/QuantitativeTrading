import configparser
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

filehandler = logging.FileHandler('log.log', encoding='utf-8')
filehandler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
filehandler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(filehandler)


class Initialize:
    def __init__(self):
        self.config = configparser.ConfigParser()
        try:
            self.config.read('config.ini')
            if not self.config.sections():
                raise FileNotFoundError
        except FileNotFoundError:
            if input('没有找到配置文件，是否创建默认配置文件？(y/n)').lower() == 'y':
                self.config['Trade'] = {
                                        'strategy_coin': '{"OCC": ["GASUSDT", "GALUSDT", "ARKUSDT", "NEOUSDT", '
                                                         '"ZENUSDT", "GMXUSDT", "MXUSDT", "FXSUSDT", "RLCUSDT", '
                                                         '"YFIUSDT", "PAXGUSDT", "TOMIUSDT"], '
                                                         '"SAS": ["GASUSDT", "ARKUSDT", "NEOUSDT", "ZENUSDT", '
                                                         '"GMXUSDT", "FXSUSDT", "RLCUSDT", "WEMIXUSDT", "YFIUSDT", '
                                                         '"GTCUSDT", "TOMIUSDT"]}',
                                        'running_coins_num': '{"OCC": 5, "SAS": 5}',
                                        'value_distribution': '{"OCC": 0.5, "SAS": 0.5}',
                                        'stop_loss': '0.3',
                                        'stop_loss_for_each': '0.275',
                                        'take_profit': '0.2',
                                        'commission': '0.001'
                                       }
                self.config['Backtesting'] = {
                                                'balance': '10000',
                                                'data_length': '1000'
                                                }
                self.config['RealTrade'] = {
                                            'data_length': '20'
                                            }
                self.config['Scraping'] = {
                                            'use_interface': 'True',
                                            'data_length': '1000'
                                            }
                self.config['OCC'] = {
                                        'basisLen': '20'
                                         }
                self.config['SAS'] = {
                                        'period': '500',
                                        'basisLen': '20'
                                         }

                with open('config.ini', 'w') as configfile:
                    self.config.write(configfile)
                logging.info('创建默认配置文件成功')

    def get(self, section, key):
        return self.config[section][key]

    def set(self, section, key, value):
        self.config[section][key] = value
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)


if __name__ == '__main__':
    init = Initialize()
    config = init.config
    print(config['Trade']['strategy_coin'])
    print(config['Trade']['running_coins_num'])
    print(config['Trade']['value_distribution'])
    print(config['Trade']['stop_loss'])
    print(config['Trade']['stop_loss_for_each'])
    print(config['Trade']['take_profit'])
    print(config['Trade']['commission'])
    print(config['Backtesting']['balance'])
    print(config['Scraping']['use_backtesting'])
    print(config['Scraping']['use_interface'])
    print(config['Scraping']['data_length'])
    print(config['Scraping']['data_length'])
