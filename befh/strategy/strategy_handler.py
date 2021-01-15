import logging
import multiprocessing as mp

from befh.strategy.config import configs, STRATEGY_PRICE_WAVE
from cryptofeed.defines import BIDS, ASKS

LOG = logging.getLogger("feedhandler")


class StrategyHandler:

    def __init__(self, pair):
        self._config = configs[pair.upper().replace('-', '')]
        self._price_signal = 0

    def handle(self):
        if self._config[STRATEGY_PRICE_WAVE]:
            self._task_list.append("p")
            # quote = self._quotes_store
            # process = mp.Process(target=process_price_wave, args=(quote.bid_queue, quote.ask_queue))
            # print("p start")
            #
            # process.start()
            # self._task_list.append("p1")
            #
            # process1 = mp.Process(target=process_kline_wave, args=(self._task_list, share_lock))
            # process1.start()
            # print("p1 start")

    def notify_price_signal(self):
        self._price_signal = 1
        pass

