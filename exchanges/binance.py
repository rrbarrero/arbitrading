import os
from mayertrading import config
import logging
import logging.config
from mayertrading.exchanges.exchange_base import BaseMarket


log_conf_file = os.path.join(config.ROOT, 'logging.conf')
logging.config.fileConfig(log_conf_file, disable_existing_loggers=False)

logger = logging.getLogger(__name__)

class Binance(BaseMarket):

    MARKETS = config.BINANCE_MARKETS
    HISTORIC_FILE = os.path.join(config.ROOT, "data", "binance_historic.dat")

    def __init__(self, coin_one, coin_two):
        super().__init__(coin_one, coin_two)
        self.key = config.BINANCE_API_KEY
        self.secret = config.BINANCE_API_SECRET
        self.url = config.BINANCE_BASE_ENDPOINT


    def get_price(self):
        sufix = "api/v3/ticker/price"
        payload = {"symbol": self.symbol}
        try:
            return float(self.s.get(self.url + sufix, params=payload).json()['price'])
        except KeyError as e:
            if config.DEBUG:
                logging.warning(e)
                logging.debug(payload)
                logging.debug(self.s.get(self.url + sufix, params=payload).json())
            self._add_to_historic()
            return None

    def get_book(self):
        sufix = "/api/v1/depth"
        payload = {"symbol": self.symbol, "limit": 5}
        self.book = self.s.get(self.url + sufix, params=payload).json()
        return self.book   

    