# minQTY reader
import json
import pandas as pd

df = pd.DataFrame()
with open('tradingInfo.json', 'r') as f:
    data = json.load(f)
    for symbol in data['symbols']:
        for each in symbol['filters']:
            if each['filterType'] == 'MARKET_LOT_SIZE':
                df[symbol['symbol']] = [each['minQty']]

df.to_csv('data/minQty.csv', index=False)
