import math
import time

from befh.strategy.config import configs, PRICE_GAPS
from befh.strategy.ding_notify import DingTalkNotify
from cryptofeed.defines import BIDS, ASKS, TIMESTAMP


class StrategyOperator:
    def __init__(self):
        self._dd_notify = DingTalkNotify()

    def execute(self, handler):
        """Execute.
        """
        raise NotImplementedError(
            'Execute is not implemented')

    def notify_wave(self, msg):
        self._dd_notify.send_msg(msg)


class KlineWaveStrategy(StrategyOperator):
    def __init__(self, pair, feed, config):
        self._pair = pair
        self._feed = feed
        self._config = config

    def execute(self, kline_queue, current_kline_queue, handler):
        # kline_queue = self._kline_queue
        # current_kline_queue = self._current_kline_queue
        # firstBid = 0
        # firstAsk = 0
        # self._handler.notify_price_signal
        pass


class PriceWaveStrategy(StrategyOperator):
    def __init__(self, pair, feed, config):
        super(PriceWaveStrategy, self).__init__()
        self._pair = pair
        self._feed = feed
        self._config = config
        self._notify_signal = 0
        self._notify_time = 0
        self._notify_max_gaps = 0
        self._notify_max_change = 0

    def execute(self, bid_queue, ask_queue, handler):
        firstBid = 0
        firstAsk = 0
        if len(bid_queue) > 1 and len(ask_queue) > 1:
            lastBid = bid_queue[len(bid_queue) - 1][BIDS][0][0]
            lastTime = bid_queue[len(bid_queue) - 1][TIMESTAMP]
            # lastAsk = ask_queue[len(bid_queue) - 1][ASKS][0][0]
            if lastTime - bid_queue[0][TIMESTAMP] < 1 * 60:
                return

            maxChange = 0
            waveGaps = 0
            timeDiff = 0
            for i in range(len(bid_queue) - 1, -1, -1):
                tmpBid = bid_queue[i][BIDS][0][0]
                diff = lastBid - tmpBid
                if abs(diff) > abs(maxChange):
                    maxChange = diff
                    waveGaps = diff / tmpBid

            timeDiff = lastTime - bid_queue[0][TIMESTAMP]
            timeGaps = lastTime - self._notify_time
            # print(timeDiff, waveTime)
            # 波动大于配置，波动大于上次通知，通知间隔大于5S
            if abs(waveGaps) > self._config[PRICE_GAPS]:
                # print(timeDiff, self._notify_max_gaps)

                if abs(waveGaps) > abs(self._notify_max_gaps):
                    if timeGaps > 5:
                        self._notify_time = lastTime
                        self._notify_max_gaps = waveGaps
                        self._notify_max_change = maxChange
                        timeStr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(lastTime))
                        msg = str.format(
                            "short time buy1 wave over size:{0:.5f},price diff:{1:.2f}, now time:{2}, current_buy1:{3}, time_diff:{4:.2f}, timeDiff:{5:.2f}",
                            waveGaps, maxChange, timeStr, lastBid, timeGaps, timeDiff)
                        super().notify_wave(msg)
                        # print(msg)
                else:
                    self._notify_max_gaps = 0
                    self._notify_max_change = 0
