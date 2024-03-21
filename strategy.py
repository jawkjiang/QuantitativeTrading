import os

import math
import random
import time
import multiprocessing
import uuid

import matplotlib.pyplot as plt

import csv


class Session:
    def __init__(self, side):
        self.balance = 10000
        self.position = 0
        self.position_value = 0
        self.total_value = 10000
        self.symbol = ''
        self.tick = 0
        self.side = side
        self.stoploss_latest = 0

        self.open_price = 0
        self.last_balance = 10000
        self.total_profit = 0
        self.total_loss = 0

    # track stoploss
    def stoploss_track(self, price, stoploss_rate):
        if price == 0:
            return False
        if self.side == 'long':
            if price * (1 - stoploss_rate) > self.stoploss_latest or self.stoploss_latest == 0:
                return price * (1 - stoploss_rate)
            elif price < self.stoploss_latest:
                return True
            else:
                return self.stoploss_latest

        elif self.side == 'short':
            if price * (1 + stoploss_rate) < self.stoploss_latest or self.stoploss_latest == 0:
                return price * (1 + stoploss_rate)
            elif price > self.stoploss_latest:
                return True
            else:
                return self.stoploss_latest

    def common_stoploss(self, price, stoploss_rate):
        if price == 0:
            return False
        if self.side == 'long':
            if price < self.open_price * (1 - stoploss_rate):
                return True
            else:
                return False
        elif self.side == 'short':
            if price > self.open_price * (1 + stoploss_rate):
                return True
            else:
                return False


class SessionContainer:
    def __init__(self, history_time, close_time, leverage, stoploss, trailing_time, trailing_stoploss):
        self.sessions = []
        self.history_time = history_time
        self.close_time = close_time
        self.leverage = leverage
        self.stoploss = stoploss
        self.trailing_time = trailing_time
        self.trailing_stoploss = trailing_stoploss

        self.trade_times = 0
        self.win_rate = 0
        self.win_times = 0
        self.max_streak = 0
        self.streak = 0
        self.max_losing_streak = 0
        self.losing_streak = 0
        self.max_drawdown = 0
        self.total_value = 0
        self.profit_ratio = 0
        self.trade_ticks = []
        self.value_list_when_trade = []
        self.profit_factor = []

        self.base_value = 0
        self.total_value_peak = 0

    def add_session(self, session):
        self.sessions.append(session)


class MediumTerm:
    def __init__(self, id, number, data, coin_list, minQty):
        super().__init__()
        self.id = id
        self.number = number
        self.data = data
        self.coin_list = coin_list
        self.minQty = minQty
        self.sessions = []
        '''
        arguments = [(random.randint(50, 168), random.randint(50, 168), random.randint(10, 40) * 0.1, random.randint(10, 20) * 0.005, random.randint(50, 120), random.choice([0, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]) * 0.005) for _ in range(number)]
        arguments = list(set([argument for argument in arguments if argument[4] <= argument[1]]))
        while len(arguments) < number:
            generator = (random.randint(4, 8), random.randint(50, 168), random.randint(10, 40) * 0.1, random.randint(10, 20) * 0.005, random.randint(50, 120), random.choice([0, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]) * 0.005)
            if generator[4] <= generator[1]:
                arguments.append(generator)
        '''
        # 地狱单吊
        arguments = [(i, 0, j*0.1, 0, 0, k*0.0015) for i in range(4, 9) for j in range(10, 41) for k in range(30, 71)]
        for argument in arguments:
            self.sessions.append(SessionContainer(*argument))
        for session_container in self.sessions:
            session_container.add_session(Session('long'))
            session_container.base_value = sum([session.total_value for session in session_container.sessions])

    @staticmethod
    def calculate_max_drawdown(peak, value, max_drawdown_latest):
        if peak == 0:
            return 0
        drawdown = (peak - value) / peak
        if drawdown > max_drawdown_latest:
            return drawdown
        else:
            return max_drawdown_latest

    def run(self):
        i = max([session_container.history_time * 12 for session_container in self.sessions])
        while i < 100000:
            self.data_handler(i)
            i += 1
            print(i)

        total_profit = 0
        total_loss = 0
        for session_container in self.sessions:
            for session in session_container.sessions:
                total_profit += session.total_profit
                total_loss += session.total_loss
            if total_loss == 0:
                session_container.profit_factor = "inf"
            else:
                session_container.profit_factor = - total_profit / total_loss
            session_container.profit_ratio = session_container.total_value / session_container.base_value - 1
            session_container.win_rate = session_container.win_times / session_container.trade_times
        self.output()

    def data_handler(self, tick):
        for session_container in self.sessions:
            for session in session_container.sessions:
                if session.symbol == '':
                    price = 0
                else:
                    price = self.data[session.symbol][tick]
                if session.tick == 0:
                    self.close_handler(session, session_container, tick, price)
                else:
                    pass_time = tick - session.tick
                    if pass_time >= session_container.trailing_time * 12:
                        session.stoploss_latest = session.stoploss_track(price, session_container.trailing_stoploss)
                    else:
                        session.stoploss_latest = 0
                    common_stoploss = session.common_stoploss(price, session_container.stoploss)
                    # if pass_time >= session_container.close_time * 12 or common_stoploss is True or session.stoploss_latest is True:
                    # 地狱单吊
                    if session.stoploss_latest is True:
                        if self.close_handler(session, session_container, tick, price) == 0:
                            session.total_value = round(session.balance + session.position_value, 2)
                            session_container.total_value = sum(
                                [session.total_value for session in session_container.sessions])
                            session_container.trade_ticks.append(tick)
                            session_container.value_list_when_trade.append(session_container.total_value)
                    else:
                        session.position_value = session.position * price
                        session.total_value = round(session.balance + session.position_value, 2)
                        session_container.total_value = sum(
                            [session.total_value for session in session_container.sessions])
            if session_container.total_value > session_container.total_value_peak:
                session_container.total_value_peak = session_container.total_value
            session_container.max_drawdown = self.calculate_max_drawdown(session_container.total_value_peak, session_container.total_value, session_container.max_drawdown)

    def close_handler(self, session, session_container, tick, price):
        target = self.filter(session, session_container, tick)
        if target == session.symbol:
            session.tick = tick
            return -1
        self.close(session, session_container, price)
        session.symbol = target
        if target == '':
            return -1
        self.trade(session, session_container, target, tick)
        session.tick = tick
        return 0

    def close(self, session, session_container, price):
        if session.symbol == '':
            return
        else:
            if session.side == 'long':
                session.balance += session.position * price * 0.9995
            elif session.side == 'short':
                session.balance += session.position * price * 1.0005
            value_change = session.balance - session.last_balance
            if value_change > 0:
                session.total_profit += value_change
            elif value_change < 0:
                session.total_loss += value_change
            session.position = 0
            session.position_value = 0
            session.stoploss_latest = 0
            session_container.trade_times += 1
            if session.side == 'long':
                if price > session.open_price:
                    session_container.win_times += 1
                    session_container.streak += 1
                    session_container.losing_streak = 0
                    if session_container.streak > session_container.max_streak:
                        session_container.max_streak = session_container.streak
                else:
                    session_container.streak = 0
                    session_container.losing_streak += 1
                    if session_container.losing_streak > session_container.max_losing_streak:
                        session_container.max_losing_streak = session_container.losing_streak
            elif session.side == 'short':
                if price < session.open_price:
                    session_container.win_times += 1
                    session_container.streak += 1
                    session_container.losing_streak = 0
                    if session_container.streak > session_container.max_streak:
                        session_container.max_streak = session_container.streak
                else:
                    session_container.streak = 0
                    session_container.losing_streak += 1
                    if session_container.losing_streak > session_container.max_losing_streak:
                        session_container.max_losing_streak = session_container.losing_streak

    def filter(self, session, session_container, tick):
        symbol_list = []
        profit_ratio_list = []
        for symbol in self.coin_list:
            if self.data[symbol][tick] >= 2 and symbol not in [token.symbol for token in session_container.sessions]:
                # price_before = self.data[symbol][tick - session_container.history_time * 12]
                # 地狱单吊
                price_before = self.data[symbol][tick - session_container.history_time]
                if price_before == 0:
                    continue
                profit_ratio = (self.data[symbol][tick] - price_before) / price_before
                if profit_ratio >= 0.02:
                    symbol_list.append(symbol)
                    profit_ratio_list.append(profit_ratio)

        if profit_ratio_list:
            if session.side == 'long':
                return symbol_list[profit_ratio_list.index(max(profit_ratio_list))]
            elif session.side == 'short':
                return symbol_list[profit_ratio_list.index(min(profit_ratio_list))]
        else:
            return ''

    def trade(self, session, session_container, symbol, tick):
        min_qty = self.minQty[symbol]
        price = self.data[symbol][tick]
        if session.side == 'long':
            session.position = math.floor(session.balance / price / min_qty) * min_qty * session_container.leverage
        elif session.side == 'short':
            session.position = -math.floor(session.balance / price / min_qty) * min_qty * session_container.leverage
        session.position_value = session.position * price
        session.last_balance = session.balance
        if session.side == 'long':
            session.balance -= session.position_value * 1.0005
        elif session.side == 'short':
            session.balance -= session.position_value * 0.9995
        session.open_price = price

    def output(self):
        unique_id = uuid.uuid4().hex
        title = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
        with open(f'output/longrace/{title}-overview-{unique_id}.csv', 'w') as file:
            file.write('index,history_time,close_time,leverage,stoploss,trailing_time,trailing_stoploss,profit_ratio,trade_times,win_rate,win_times,max_streak,max_losing_streak,max_drawdown,profit_factor\n')
            for session_container in self.sessions:
                file.write(f'{self.sessions.index(session_container)},{session_container.history_time},{session_container.close_time},{session_container.leverage},{session_container.stoploss},{session_container.trailing_time},{session_container.trailing_stoploss},{session_container.profit_ratio},{session_container.trade_times},{session_container.win_rate},{session_container.win_times},{session_container.max_streak},{session_container.max_losing_streak},{session_container.max_drawdown},{session_container.profit_factor}\n')


def data_loader():
    with open("data/combined.csv", "r") as file:
        csv_reader = csv.reader(file)
        coin_list = next(csv_reader)
        print("coin_list loaded")
        data = {coin: [] for coin in coin_list}

        for row in csv_reader:
            for i in range(len(coin_list)):
                data[coin_list[i]].append(float(row[i]))
    print("data loaded")

    with open("data/minQty.csv", "r") as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)
        for row in csv_reader:
            minQty = {headers[i]: float(row[i]) for i in range(len(headers))}
        for symbol in headers:
            if symbol not in coin_list:
                del minQty[symbol]
    print("minQty loaded")

    return data, coin_list, minQty


if __name__ == '__main__':
    DATA, COIN_LIST, MIN_QTY = data_loader()
    num_processes = 100
    strategy_list = []
    processes = []
    for i in range(num_processes):
        strategy_list.append(MediumTerm(i+1, 10000, DATA, COIN_LIST, MIN_QTY))
        p = multiprocessing.Process(target=strategy_list[i].run())
        processes.append(p)

    for p in processes:
        p.start()
        print(f"Process {processes.index(p)} started")

    print("done.")







