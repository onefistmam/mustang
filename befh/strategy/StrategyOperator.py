from cryptofeed.defines import BIDS, ASKS


class StrategyOperator:
    def __init__(self):
        super.__init__()

    def execute(self, handler):
        """Execute.
        """
        raise NotImplementedError(
            'Execute is not implemented')


class KlineWaveStrategy(StrategyOperator):
    def __init__(self, pair, feed):
        self._pair = pair
        self._feed = feed

    def execute(self, kline_queue, current_kline_queue, handler):
        kline_queue = self._kline_queue
        current_kline_queue = self._current_kline_queue
        firstBid = 0
        firstAsk = 0
        self._handler.notify_price_signal


class PriceWaveStrategy(StrategyOperator):
    def __init__(self, pair, feed):
        self._pair = pair
        self._feed = feed

    def execute(self, bid_queue, ask_queue, handler):
        firstBid = 0
        firstAsk = 0
        if len(bid_queue) > 1 and len(ask_queue) > 1:
            tmpFirstBid = bid_queue[0][BIDS]
            tmpFirstAsk = ask_queue[0][ASKS]

            if firstBid != tmpFirstBid[0] and firstAsk != tmpFirstAsk[0]:
                firstAsk = tmpFirstAsk[0]
                firstBid = tmpFirstBid[0]

        handler.notify_price_signal
