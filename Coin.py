class Coin:

    def __init__(self, name):
        self.name = name
        self.value = 0
        self.value_before_sell = 0
        self.position = 0
        self.open_price = 0
        self.close_price = 0
        self.current_price = 0

        # states
        self.action = 'CLOSED'
        self.switch = None
        self.Liquidation = False

    def buy(self, value, open_price):
        self.value = float(value)
        self.position = float(value)/float(open_price)
        self.open_price = float(open_price)
        self.action = 'OPENED'
        self.switch = 'BUY'

    def sell(self, close_price):
        self.close_price = float(close_price)
        self.value_before_sell = self.value
        self.action = 'CLOSED'
        self.switch = 'SELL'
        self.position = 0
        self.value = 0

    def realtime_value(self, stop_loss, current_price):
        self.switch = None
        self.current_price = float(current_price)
        if self.action == 'OPENED':
            self.value = self.position * float(current_price)
            if self.value < (1 - stop_loss) * self.position * float(self.open_price):
                self.Liquidation = True
        else:
            self.value = 0

    def get_name(self):
        return self.name
