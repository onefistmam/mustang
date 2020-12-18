import logging
import multiprocessing as mp

import ccxt

from cryptofeed import FeedHandler
from cryptofeed.callback import TickerCallback

from cryptofeed.defines import TICKER

import cryptofeed.exchanges as cryptofeed_exchanges
LOGGER = logging.getLogger(__name__)

def loopa():
    for i in [1,2,3,4,5,6]:
        print(i)

def process():
    process = mp.Process(loopa())
    return process

def _update_ticker_callback(self, feed, pair, bid, ask, timestamp, receipt_timestamp):
    LOGGER.info("_update_ticker_callback feed :%s, pair:%s, bid:%9.4f, ask: %9.4f,timestamp:%d receipt_time:%d",
                feed, pair, bid, ask, timestamp, receipt_timestamp)
    return

if __name__ == '__main__':

    ccxt_exchange = getattr(ccxt, "binance", None)

    exchange = getattr(
        cryptofeed_exchanges, "Binance")
    channels = [
        # TRADES,
        # L2_BOOK,
        TICKER
    ]

    callbacks = {
        TICKER: TickerCallback(_update_ticker_callback)
    }

    exchange = exchange(pairs=list({"ETH/USDT"}), channels=channels, callbacks=callbacks)
    _feed_handler = FeedHandler()
    _feed_handler.add_feed(exchange)
    #
    # if ccxt_exchange:
    #     exchanges = ccxt_exchange()
    #     maks = exchanges.load_markets()
    #     print(exchanges)
    #     print("\n")
    #     print(maks)
    # if "ETH/USDT" not in maks:
    #     print("ffff")
