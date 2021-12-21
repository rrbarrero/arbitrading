#!/usr/bin/env python

import os
import logging
import logging.config
import config
from exchanges.exchange_base import MetaMarket

log_conf_file = os.path.join(config.ROOT, 'logging.conf')
logging.config.fileConfig(log_conf_file, disable_existing_loggers=False)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Iniciando...")
    for coin in config.BINANCE_COINS:
        for symbol_two in config.BINANCE_MARKETS:
            MetaMarket('binance', coin, symbol_two).run()
    logger.info("Terminado.")