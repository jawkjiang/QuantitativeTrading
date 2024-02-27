import plotly.graph_objects as go


class Plot:
    def __init__(self, data):
        self.data = data
        self.fig = go.Figure()

    def plot(self):
        self.fig = go.Figure(data=[go.Candlestick(x=list(self.data['open_time']),
                                                  open=list(self.data['open']),
                                                  high=list(self.data['high']),
                                                  low=list(self.data['low']),
                                                  close=list(self.data['close']))])

    def arrows(self, point, action):
        if action == 'OPEN':
            self.fig.add_trace(go.Scatter(x=[point[0]], y=[point[1]], mode='markers', marker=dict(symbol='arrow-up',
                                                                                                  size=10,
                                                                                                  color='green')))

        elif action == 'CLOSE':
            self.fig.add_trace(go.Scatter(x=[point[0]], y=[point[1]], mode='markers', marker=dict(symbol='arrow-down',
                                                                                                  size=10,
                                                                                                  color='red')))

        elif action == 'LIQUIDATION':
            self.fig.add_trace(go.Scatter(x=[point[0]], y=[point[1]], mode='markers', marker=dict(symbol='arrow-down',
                                                                                                  size=10,
                                                                                                  color='black')))

    def show(self):
        self.fig.show()

