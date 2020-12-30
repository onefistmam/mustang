import json
import logging
import time

# 时间戳误差
from threading import Lock

from cryptofeed.defines import BINANCE_FUTURES

LOG = logging.getLogger("feedhandler")

TIME_DEVIATION = 2000

signal = "sell"
mutex = Lock()


class QuotesStore:

    def __init__(self, pair, feed):
        self._feed = feed
        self._pair = pair

        self._price_queue = []
        self._kline_queue = []

        self._current_kline_queue = []
        self._bid_queue = []
        self._ask_queue = []

        self._best_bid = []
        self._best_ask = []

    def update_price_queue(self, feed, pair, timestamp, best_bid, best_bid_size, best_ask, best_ask_size):
        bb = self._best_bid
        ba = self._best_ask
        if time.time() - timestamp > 500:
            return
        bb.append([timestamp, [best_bid, best_bid_size]])
        ba.append([timestamp, [best_ask, best_ask_size]])

        if len(bb) > 1 and bb[len(bb) - 1][0] - bb[0][0] > 10:
            bb.pop(0)[0]
            print(bb[0][1])

        if len(ba) > 1 and ba[len(ba) - 1][0] - ba[0][0] > 10:
            ba.pop(0)[0]
            print(ba[0][1])

    def update_depth(self, feed, pair, timestamp, asks, bids):
        ask_queue = self._ask_queue
        bid_queue = self._bid_queue

        if time.time() - timestamp > 500:
            return

        ask_queue.append([timestamp, asks])
        bid_queue.append([timestamp, bids])

        if len(ask_queue) > 1 and ask_queue[len(ask_queue) - 1][0] - ask_queue[0][0] > 120:
            ask_queue.pop(0)[0]

        if len(bid_queue) > 1 and bid_queue[len(bid_queue) - 1][0] - bid_queue[0][0] > 120:
            bid_queue.pop(0)[0]

    def update_kline_queue(self, feed, pair, timestamp, kline):
        kline_queue = self._kline_queue
        if feed == BINANCE_FUTURES:
            from befh.strategy import BinanceKline
            bk = BinanceKline(open_p=kline['o'], close_p=kline['c'], start_t=kline['t'], end_t=kline['T'],
                              high_P=kline['h'], low_p=kline['l'], finish=kline['x'])
            if kline['x']:
                kline_queue.append([timestamp, bk])
                if len(kline_queue) > 0 and kline_queue[len(kline_queue) - 1][0] - kline_queue[0][0] > 60:
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
