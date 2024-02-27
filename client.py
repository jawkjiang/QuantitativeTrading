from mexc_api import spot
from mexc_api.common.enums import Interval


key = "mx0vglgPxDIyPkzMRU"
secret = "155879a307f04bfb8113a6d8581074ac"

mexc = spot.Spot(key, secret)
print(mexc.market.klines(symbol='ONDOUSDT', interval=Interval.FIVE_MIN, limit=5))
print(mexc.market.server_time())
