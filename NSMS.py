import numpy as np
import pandas as pd


class OCC:

    def __init__(self, data: pd.DataFrame, **kwargs):
        # data is a pandas dataframe, with columns: date, open, high, low, close, volume
        self.data = data
        self.date = data['date']
        self.open = data['open']
        self.high = data['high']
        self.low = data['low']
        self.close = data['close']
        self.volume = data['volume']

        # parameters
        self.needlong = kwargs.get('needlong', True)
        self.needshort = kwargs.get('needshort', True)
        self.length = kwargs.get('length', 20)
        self.mult = kwargs.get('mult', 2)
        self.lengthKC = kwargs.get('lengthKC', 20)
        self.multKC = kwargs.get('multKC', 1.5)
        self.useTrueRange = kwargs.get('useTrueRange', False)
        self.usecolor = kwargs.get('usecolor', True)
        self.usebody = kwargs.get('usebody', True)
        self.needbg = kwargs.get('needbg', False)
        self.fromyear = kwargs.get('fromyear', 1900)
        self.toyear = kwargs.get('toyear', 2100)
        self.frommonth = kwargs.get('frommonth', 1)
        self.tomonth = kwargs.get('tomonth', 12)
        self.fromday = kwargs.get('fromday', 1)
        self.today = kwargs.get('today', 31)

        # states
        self.squeeze = "None"
        self.val = np.zeros(self.length)
        self.trend = np.zeros(self.length)
        self.bar = np.zeros(self.length)
        self.up = np.zeros(self.length)
        self.down = np.zeros(self.length)

    def run(self):
        # Calculate BB
        basis = sum(self.close) / self.length
        dev = self.mult * np.std(self.close)
        upperBB = basis + dev
        lowerBB = basis - dev

        # Calculate KC
        if self.useTrueRange:
            pass
        range = self.high - self.low
        rangema = sum(range) / self.lengthKC
        upperKC = sum(self.close) / self.lengthKC + rangema * self.multKC
        lowerKC = sum(self.close) / self.lengthKC - rangema * self.multKC

        # confirm squeeze
        if upperBB < upperKC and lowerBB > lowerKC:
            self.squeeze = "On"
        elif upperBB > upperKC and lowerBB < lowerKC:
            self.squeeze = "Off"
        else:
            self.squeeze = "None"

        # Calculate val, it's an indicator of linreg
        # linreg: y = mx + c
        for i in range(1, self.length + 1):
            if i < self.lengthKC:
                x = np.arange(0, i)
                y = np.array(self.close[:i] - ((np.maximum(self.high[:i]) + np.minimum(self.low[:i])) / 2 + sum(self.close[:i]) / self.lengthKC) / 2)
                A = np.vstack([x, np.ones(len(x))]).T
                m, c = np.linalg.lstsq(A, y, rcond=None)[0]
                self.val[i-1] = m * (len(self.close) - 1) + c
            else:
                x = np.arange(0, self.lengthKC)
                y = np.array(self.close[i - self.lengthKC:i] - ((np.maximum(self.high[i - self.lengthKC:i]) + np.minimum(self.low[i - self.lengthKC:i])) / 2 + sum(self.close[i - self.lengthKC:i]) / self.lengthKC) / 2)
                A = np.vstack([x, np.ones(len(x))]).T
                m, c = np.linalg.lstsq(A, y, rcond=None)[0]
                self.val[i-1] = m * (len(self.close) - 1) + c
            if self.val[i-1] > 0:
                self.trend[i-1] = 1
            elif self.val[i-1] < 0:
                self.trend[i-1] = -1
            else:
                self.trend[i-1] = 0

        # Calculate EMA body
        body = abs(self.close - self.open)

        def ema(src, n):
            emaverage = np.zeros(len(src))
            for i in range(len(src)):
                if i == 0:
                    emaverage[i] = src[i]
                else:
                    a = 2 / (n + 1)
                    emaverage[i] = a * src[i] + (1 - a) * emaverage[i - 1]
            return emaverage
        emabody = ema(body, 30) / 3

        # Calculate signals
        for i in range(self.length):
            if self.close[i] > self.open[i]:
                self.bar[i] = 1
            elif self.close[i] < self.open[i]:
                self.bar[i] = -1
            else:
                self.bar[i] = 0
            if self.trend[i] == 1 and (self.bar[i] == -1 or self.usecolor == False) and (body[i] > emabody[i] or self.usebody == False):
                self.up[i] = 1
            elif self.trend[i] == -1 and (self.bar[i] == 1 or self.usecolor == False) and (body[i] > emabody[i] or self.usebody == False):
                self.down[i] = 1

        # def trade():










