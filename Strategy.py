import pandas as pd


class Strategy:

    def _init__(self, config):
        self.config = config
        self.action = None
        self.method = config.get('Trade', 'strategy_method')

    @staticmethod
    def ema(src):
        alpha = 2 / (len(src) + 1)
        ema = [src[0]]
        for i in range(1, len(src)):
            current_ema = alpha * float(src[i]) + (1 - alpha) * float(ema[-1])
            ema.append(current_ema)
        return ema

    @staticmethod
    def tr(high_src, low_src):
        tr = [high_src[i] - low_src[i] for i in range(len(high_src))]
        return tr

    @staticmethod
    def atr(src):
        length = len(src)
        atr = [src[0]]
        for i in range(1, len(src)):
            current_atr = (float(src[i]) + float(atr[-1]) * (length-1)) / length
            atr.append(current_atr)
        return atr


class OCC(Strategy):

    def __init__(self, **kwargs):
        super().__init__()
        # parameters
        self.useRes = kwargs.get('useRes', True)
        self.intRes = kwargs.get('intRes', 3)
        self.stratRes = kwargs.get('stratRes', 'intraday')
        self.basisType = kwargs.get('basisType', 'ema')
        self.basisLen = int(self.config.get('OCC', 'basisLen'))
        self.offsetSigma = kwargs.get('offsetSigma', 17)
        self.offsetALMA = kwargs.get('offsetALMA', 0.85)
        self.scolor = kwargs.get('scolor', False)
        self.delayOffset = kwargs.get('delayOffset', 0)
        self.tradeType = kwargs.get('tradeType', 'BOTH')
        self.slPoints = kwargs.get('slPoints', 0)
        self.tpPoints = kwargs.get('tpPoints', 0)
        self.ebar = kwargs.get('ebar', 10000)
        self.dummy = kwargs.get('dummy', False)

    def run(self, data: pd.DataFrame):
        close = list(data['close'])
        _open = list(data['open'])
        close_ema = self.ema(close)
        open_ema = self.ema(_open)
        if close_ema[-2] < open_ema[-2] and close_ema[-1] > open_ema[-1]:
            self.action = 'OPEN'
        elif close_ema[-2] > open_ema[-2] and close_ema[-1] < open_ema[-1]:
            self.action = 'CLOSE'
        else:
            self.action = None


class SAS(Strategy):

    def __init__(self, **kwargs):
        super().__init__()
        # parameters
        self.period = int(self.config.get('SAS', 'period'))
        self.useRes = kwargs.get('useRes', True)
        self.intRes = kwargs.get('intRes', 3)
        self.stratRes = kwargs.get('stratRes', 'intraday')
        self.basisType = kwargs.get('basisType', 'ema')
        self.basisLen = int(self.config.get('SAS', 'basisLen'))
        self.offsetSigma = kwargs.get('offsetSigma', 17)
        self.offsetALMA = kwargs.get('offsetALMA', 0.85)
        self.scolor = kwargs.get('scolor', False)
        self.delayOffset = kwargs.get('delayOffset', 0)
        self.tradeType = kwargs.get('tradeType', 'BOTH')
        self.slPoints = kwargs.get('slPoints', 0)
        self.tpPoints = kwargs.get('tpPoints', 0)
        self.ebar = kwargs.get('ebar', 10000)
        self.dummy = kwargs.get('dummy', False)

        self.last_trade_time = 0

    def run(self, data):
        close = list(data['close'])
        _open = list(data['open'])
        if close[-2] < _open[-2] and close[-1] > _open[-1]:
            self.action = 'OPEN'
        elif close[-2] > _open[-2] and close[-1] < _open[-1]:
            self.action = 'CLOSE'
        else:
            self.action = None


class BAS(Strategy):

    def __init__(self):
        super().__init__()
        self.ATRLen = int(self.config.get('BAS', 'ATRLen'))

    def run(self, data):
        close = list(data['close'])
        high = list(data['high'])
        low = list(data['low'])
        atr = self.atr(self.tr(high, low))

