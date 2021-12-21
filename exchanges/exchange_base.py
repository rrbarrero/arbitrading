#!/usr/bin/env python

import os
import datetime
import importlib
from mayertrading import config
import requests
import logging
import logging.config


log_conf_file = os.path.join(config.ROOT, 'logging.conf')
logging.config.fileConfig(log_conf_file, disable_existing_loggers=False)

loggerP = logging.getLogger('urllib3')
loggerP.addHandler(logging.StreamHandler())
loggerP.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class BaseMarket(object):
    def __init__(self, coin_one, coin_two):
        self.symbol = coin_one + coin_two
        self.price = None
        self.coin_one = coin_one
        self.coin_two = coin_two
        self.s = requests.session()
    
    def _check_historic(self):
        #if config.DEBUG:
            #logging.debug('Comprobando histórico para {}'.format(str(self)))
        if not os.path.exists(self.HISTORIC_FILE):
            open(self.HISTORIC_FILE, 'a').close()
        with open(self.HISTORIC_FILE, 'r') as fo:
            for line in fo:
                if str(self) in line:
                    return None
        return True

    def _add_to_historic(self):
        with open(self.HISTORIC_FILE, 'a') as fw:
            fw.write(str(self)+'\n')

    def __repr__(self):
        return "{}/{}".format(self.coin_one, self.coin_two)


    def get_price(self):
        """ Devuelve el precio del par en cuestión """
        raise NotImplementedError

    def get_book(self):
        """ Devuelve un dict con el libro de asks y bids """
        raise NotImplementedError


    def _get_bids(self):
        try:
            return self.book['bids'][0]
        except KeyError:
            return None

    def _get_asks(self):
        try:
            return self.book['asks'][0]
        except KeyError:
            return None


class MetaMarket(object):

    def __init__(self, market, coin_one, coin_two):
        module = importlib.import_module(config.exchanges_path + market.lower())
        self.market = market
        self.coin_one = coin_one
        self.coin_two = coin_two
        self._class_ = getattr(module, market.capitalize())
        self._instance = self._class_(coin_one, coin_two)
        self.price = None
        if self._instance._check_historic():
            self.symbol = coin_one + coin_two
            self.price = self._instance.get_price()
            self.book = self._instance.get_book()
            self.bids = self._instance._get_bids()
            self.asks = self._instance._get_asks()

    @staticmethod
    def get_posible_market_pairs(klass, coin):
        markets = []
        for market in klass.MARKETS:
            if coin.lower() != market.lower():
                markets.append((coin, market))
                markets.append((market, coin))
        return markets

    def symbol_hops(self):
        """ Devuelve los precios de la segunda moneda con cada MARKET DISPONIBLE 
            en un determinado Exchange """
        prices = {}
        for symbol in MetaMarket.get_posible_market_pairs(self._class_, self.coin_two):
            b = MetaMarket(self.market, symbol[0], symbol[1])
            if b.price != None:
                prices['{}/{}'.format(*symbol)] = b.price
        return prices

    def available_symbol_hops(self):
        """ Comprueba si un salto es compatible con la primera moneda """
        availables = []
        for k, v in self.symbol_hops().items():
            pivot_coin = k.split('/')[0]
            c = MetaMarket(self.market, self.coin_one, pivot_coin)
            if c.price != None:
                availables.append(c)
            c = MetaMarket(self.market, pivot_coin, self.coin_one)
            if c.price != None:
                availables.append(c)
        return availables

    @staticmethod
    def find_symbol(market, coin_one, coin_two):
        """ Devuelve un symbol en el primer orden encontrado """
        symbol = MetaMarket(market, coin_one, coin_two)
        if symbol.price != None:
            return symbol
        symbol = MetaMarket(market, coin_two, coin_one)
        if symbol.price != None:
            return symbol
        return None

    def _calculate_goin(self, path_nodes):
        account = 100
        account *= float(path_nodes[0].bids[0])
        account /= float(path_nodes[1].asks[0])
        account /= float(path_nodes[2].asks[0])
        return account

    def _calculate_return(self, path_nodes):
        account = 100
        account *= float(path_nodes[0].bids[0])
        account *= float(path_nodes[1].bids[0])
        account /= float(path_nodes[2].asks[0])
        return account

    def calculate_path(self):
        for symbol in self.available_symbol_hops():
            nodes = [
                MetaMarket.find_symbol(self.market, self.coin_one, self.coin_two),
                MetaMarket.find_symbol(self.market, self.coin_two, symbol.coin_two), 
                MetaMarket.find_symbol(self.market, symbol.coin_two, self.coin_one)]
            if None not in nodes:
                total = self._calculate_goin(nodes)-100
                # if config.DEBUG:
                #     print(nodes, total)
                if total > 0.6:
                    self.register(nodes, total)
                nodes.reverse()           
                total = self._calculate_return(nodes)-100
                # if config.DEBUG:
                #     print(nodes, total)
                if total > 0.6:
                    self.register(nodes, total)

    def register(self, path_hops, result):
        logger.warning(self.market.upper() + '\t' + ", ".join([str(x) for x in path_hops]) + '\t' + str(result))
        with open('resultados.dat', 'a') as fw:
            now = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            fw.write(now + '\t' + self.market.upper() + '\t' + ", ".join([str(x) for x in path_hops]) + '\t' + str(result) + "\n")

    def run(self):
        self.calculate_path()


    def __repr__(self):
        return "{}/{}".format(self.coin_one, self.coin_two)


if __name__ == '__main__':
    
    for coin in config.BINANCE_COINS:
        for symbol_two in config.BINANCE_MARKETS:
            MetaMarket('binance', coin, symbol_two).run()