import logging
import multiprocessing as mp
import sys

import ccxt
from cryptofeed import FeedHandler
from cryptofeed.callback import TickerCallback, BookCallback
from cryptofeed.defines import TICKER, L2_BOOK

import cryptofeed.exchanges as cryptofeed_exchanges

LOGGER = logging.getLogger(__name__)


# (self, *, feed: str, pair: str, last_price: Decimal, avg_price: Decimal, timestamp: float, receipt_timestamp: float)
def _update_ticker_callback(self, feed, pair, last_price, avg_price, timestamp, receipt_timestamp=None):
    print("_update_ticker_callback", int(round(timestamp * 1000)))
    LOGGER.info("_update_ticker_callback feed :%s, pair:%s, last_price:%9.4f, avg_price: %9.4f,timestamp:%d",
                feed, pair, last_price, avg_price, timestamp, receipt_timestamp)
    return


# feed: str, pair: str, book: dict, timestamp: float, receipt_timestamp: float
def _update_orderbook_callback(self, feed, pair, book, timestamp, receipt_timestamp=None):
    print("_update_ticker_callback", int(round(timestamp * 1000)))
    LOGGER.warning("_update_orderbook_callback feed :%s, pair:%s, book: %s,timestamp:%d, receipt_timestamp:%s",
                feed, pair, str(book), timestamp, receipt_timestamp)
    return


if __name__ == '__main__':
    sys.setrecursionlimit(10000)
    print("ccxt_exchange")
    ccxt_exchange = getattr(ccxt, "binance", None)

    exchange = getattr(
        cryptofeed_exchanges, "BinanceFutures")
    channels = [
        TICKER,
        L2_BOOK
    ]
    callbacks = {
        TICKER: TickerCallback(_update_ticker_callback),
        L2_BOOK: BookCallback(_update_orderbook_callback)
    }
    print("exchage")
    exchange = exchange(pairs=list({"ETH-USDT"}), channels=channels, callbacks=callbacks)
    _feed_handler = FeedHandler()
    _feed_handler.add_feed(exchange)
    _feed_handler.run()
