import collections
import logging
import sys
from collections import deque
import time

# 时间戳误差
from threading import Lock

LOG = logging.getLogger("feedhandler")

TIME_DEVIATION = 2000

signal = "sell"
mutex = Lock()


class PriceStrategy:

    def __init__(self, name):
        self._name = name
        self._price_queue = []
        self._kline_queue = []
        self._bid_queue = []
        self._ask_queue = []

    def update_price_queue(self, feed, pair, timestamp, price):
        price_queue = self._price_queue
        price_queue.append([timestamp, price])
        if time.time() - timestamp > 500:
            return
        if len(price_queue) > 1 and price_queue[len(price_queue) - 1][0] - price_queue[0][0] > 60:
            price_queue.pop(0)[0]

    def update_kline_queue(self, feed, pair, timestamp, kline):
        self._kline_queue.append({"time": timestamp, "kline": kline})
        # if len(self.kline_queue) > 100:
        # LOG.info("pop kline=%s", self.kline_queue.popleft())
