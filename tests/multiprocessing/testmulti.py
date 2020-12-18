import logging
import multiprocessing as mp
import sys

import ccxt
from cryptofeed import FeedHandler
from cryptofeed.callback import TickerCallback
from cryptofeed.defines import TICKER

import cryptofeed.exchanges as cryptofeed_exchanges

LOGGER = logging.getLogger(__name__)


def loopa():
    for i in [1, 2, 3, 4, 5, 6]:
        print(i)


def process():
    process = mp.Process(loopa())
    return process

#(self, *, feed: str, pair: str, last_price: Decimal, avg_price: Decimal, timestamp: float, receipt_timestamp: float)
def _update_ticker_callback(self, feed, pair, last_price, avg_price, timestamp):
    print("_update_ticker_callback")
    LOGGER.info("_update_ticker_callback feed :%s, pair:%s, last_price:%9.4f, avg_price: %9.4f,timestamp:%d",
                feed, pair, last_price, avg_price, timestamp)
    return


if __name__ == '__main__':
    sys.setrecursionlimit(10000)
    print("ccxt_exchange")
    ccxt_exchange = getattr(ccxt, "binance", None)

    exchange = getattr(
        cryptofeed_exchanges, "Binance")
    channels = [
        TICKER
    ]
    callbacks = {
        TICKER: TickerCallback(_update_ticker_callback)
    }
    print("exchage")
    exchange = exchange(pairs=list({"ETH/USDT"}), channels=channels, callbacks=callbacks)
    _feed_handler = FeedHandler()
    _feed_handler.add_feed(exchange)
    _feed_handler.run()
