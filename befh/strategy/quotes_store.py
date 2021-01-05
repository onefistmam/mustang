import json
import logging
import time

# 时间戳误差
from threading import Lock

from cryptofeed.defines import BINANCE_FUTURES, TIMESTAMP, ASKS, BIDS
import multiprocessing as mp

LOG = logging.getLogger("feedhandler")

TIME_DEVIATION = 1
QUEUE_STORE_SEC = 60

signal = "sell"
mutex = Lock()


class QuotesStore:

    def __init__(self, pair, feed):
        self._pair = pair
        self._feed = feed

        self._price_queue = mp.Manager().list()
        self._kline_queue = mp.Manager().list()

        self._current_kline_queue = mp.Manager().list()
        self._bid_queue = mp.Manager().list()
        self._ask_queue = mp.Manager().list()

        self._best_bid = mp.Manager().list()
        self._best_ask = mp.Manager().list()

    def update_best_price_queue(self, feed, pair, timestamp, best_bid, best_bid_size, best_ask, best_ask_size):
        bb = self._best_bid
        ba = self._best_ask
        if time.time() - timestamp > TIME_DEVIATION:
            return
        bb.append([timestamp, [best_bid, best_bid_size]])
        ba.append([timestamp, [best_ask, best_ask_size]])

        if len(bb) > 1 and bb[len(bb) - 1][0] - bb[0][0] > QUEUE_STORE_SEC:
            bb.pop(0)[0]

        if len(ba) > 1 and ba[len(ba) - 1][0] - ba[0][0] > QUEUE_STORE_SEC:
            ba.pop(0)[0]

    def update_depth(self, feed, pair, timestamp, asks, bids):
        ask_queue = self._ask_queue
        bid_queue = self._bid_queue

        if time.time() - timestamp > TIME_DEVIATION:
            return

        ask_queue.append({TIMESTAMP: timestamp, ASKS: asks})
        bid_queue.append({TIMESTAMP: timestamp, BIDS: bids})

        if len(ask_queue) > 1 and ask_queue[len(ask_queue) - 1][TIMESTAMP] - ask_queue[0][TIMESTAMP] > QUEUE_STORE_SEC:
            ask_queue.pop(0)

        if len(bid_queue) > 1 and bid_queue[len(bid_queue) - 1][TIMESTAMP] - bid_queue[0][TIMESTAMP] > QUEUE_STORE_SEC:
            bid_queue.pop(0)

    def update_kline_queue(self, feed, pair, timestamp, kline):
        kline_queue = self._kline_queue
        if time.time() - timestamp > TIME_DEVIATION:
            return
        if feed == BINANCE_FUTURES:
            from befh.strategy import BinanceKline
            bk = BinanceKline(open_p=kline['o'], close_p=kline['c'], start_t=kline['t'], end_t=kline['T'],
                              high_P=kline['h'], low_p=kline['l'], finish=kline['x'])
            if bk.finish:
                kline_queue.append([timestamp, bk])
                if len(kline_queue) > 0 and kline_queue[len(kline_queue) - 1][0] - kline_queue[0][0] > QUEUE_STORE_SEC:
                    kline_queue.pop(0)[0]
                self._current_kline_queue = []
            else:
                self._current_kline_queue.append([timestamp, bk])

    @property
    def pair(self):
        return self._pair

    @property
    def feed(self):
        return self._feed

    @property
    def price_queue(self):
        return self._price_queue

    @property
    def bid_queue(self):
        return self._bid_queue

    @property
    def ask_queue(self):
        return self._ask_queue

    @property
    def kline_queue(self):
        return self._kline_queue

    @property
    def best_bid(self):
        return self._best_bid
