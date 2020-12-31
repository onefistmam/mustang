import asyncio
import string
import time
from multiprocessing.managers import BaseManager
from multiprocessing.queues import Queue
from threading import Lock

from befh.strategy import QuotesStore
from befh.strategy.config import configs, STRATEGY_PRICE_WAVE
import multiprocessing as mp


class StrategyHandler:

    def __init__(self, quotes: QuotesStore):
        self._quotes_store = quotes
        print("init obj", quotes._feed)

        self._queue = Queue
        self._config = configs[str(quotes.pair).upper().replace('-', '')]
        self._task_list = mp.Manager().list()

    def handle(self):
        if self._config[STRATEGY_PRICE_WAVE]:
            self._task_list.append("p")
            quote = self._quotes_store
            process = mp.Process(target=process_price_wave, args=(quote.bid_queue, quote.ask_queue))
            print("p start")

            process.start()
            self._task_list.append("p1")
            #
            # process1 = mp.Process(target=process_kline_wave, args=(self._task_list, share_lock))
            # process1.start()
            # print("p1 start")


def process_price_wave(bid_queue, ask_queue):
    print(id(bid_queue))
    if len(bid_queue) > 0:
        print(bid_queue)
    while True:  # print("time diff", time.time() - bid_queue[0][0])
        if len(bid_queue) > 1 and len(ask_queue) > 1:
            firstBid = bid_queue[len(bid_queue) - 1][1][0]
            firstAsk = ask_queue[len(ask_queue) - 1][1][0]
            print(firstAsk, firstBid)


def process_kline_wave(quotes):
    print(id(quotes.bid_queue))
    while len(quotes.bid_queue) > 0:
        print("time diff", time.time() - quotes.bid_queue[0][0])
        if len(quotes.bid_queue) > 0 and time.time() - quotes.bid_queue[0][0] > 50:
            firstBid = quotes.bid_queue[len(quotes.bid_queue) - 1][0]
            firstAsk = quotes.bid_queue[len(quotes.ask_queue) - 1][0]
            print(firstAsk, firstBid)


if __name__ == '__main__':
    tt = []
    tt.append((1, 2, 3, 4))
    tt.append((1, 2, 3, 4))
    tt.append((1, 2, 3, 4))
    tt.append((1, 2, 3, 4))
    tt.append((1, 2, 3, 4))
    while len(tt) > 0:
        print(tt.pop())
    # tl = mp.Manager().list()
    # share_lock = mp.Manager().Lock()
    # tl.append("start flag")
    #
    # len(tl)
    # process = mp.Process(target=process_price_wave, args=(tl,share_lock))
    # print("p start")
    #
    # process.start()
    # len(tl)
    # process1 = mp.Process(target=process_kline_wave, args=(tl,share_lock))
    # process1.start()
    # print("p1 start", tl)
