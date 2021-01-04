import logging
from datetime import datetime
import re

from cryptofeed import FeedHandler
from cryptofeed.defines import L2_BOOK, TRADES, BID, ASK, \
    TICKER, BOOK_TICKER, OKEX, KLINE
from cryptofeed.callback import BookCallback, TradeCallback, TickerCallback, BookTickerCallback, KlineCallback
import cryptofeed.exchanges as cryptofeed_exchanges

from .rest_api_exchange import RestApiExchange

LOGGER = logging.getLogger("feedhandler")

FULL_UTC_PATTERN = '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z'


class WebsocketExchange(RestApiExchange):
    """Websocket exchange.
    """

    def __init__(self, **kwargs):
        """Constructor.
        """
        super().__init__(**kwargs)
        self._feed_handler = None
        self._instrument_mapping = None

    def load(self, **kwargs):
        """Load.
        """
        super().load(is_initialize_instmt=False, **kwargs)
        self._feed_handler = FeedHandler()
        self._instrument_mapping = self._create_instrument_mapping()
        try:
            exchange = getattr(
                cryptofeed_exchanges,
                self._get_exchange_name(self._name))
        except AttributeError as e:
            raise ImportError(
                'Cannot load exchange %s from websocket' % self._name)
        LOGGER.info("exchange load %s", self._name)
        contract_exchanges_use_common_channel = ['HuobiSwap', 'HuibiDM', 'KrakenFutures', 'BinanceFutures', 'Bitmex']
        if self._is_orders:
            if self._type == 'futures':
                channels = [L2_BOOK, BOOK_TICKER, KLINE]
            elif self._type == 'swap':
                channels = [L2_BOOK, BOOK_TICKER]
            LOGGER.info("channel %s ", channels)
            callbacks = {
                L2_BOOK: BookCallback(self._update_order_book_callback),
                BOOK_TICKER: BookTickerCallback(self._update_book_ticker_callback),
                KLINE: KlineCallback(self._update_kline_callback),
            }
        else:
            if self._type == 'spot' or self._name in contract_exchanges_use_common_channel:
                channels = [TRADES]
            elif self._type == 'futures':
                channels = [TRADES, KLINE]
            elif self._type == 'swap':
                channels = [TRADES]
            callbacks = {
                channels[0]: TradeCallback(self._update_trade_callback),
                KLINE: KlineCallback(self._update_kline_callback),
            }
        if self._name.lower() == 'poloniex':
            self._feed_handler.add_feed(
                exchange(
                    channels=list(self._instrument_mapping.keys()),
                    callbacks=callbacks))
        else:
            self._feed_handler.add_feed(
                exchange(
                    pairs=list(self._instrument_mapping.keys()),
                    channels=channels,
                    callbacks=callbacks))

    def run(self):
        """Run.
        """
        self._feed_handler.run()

    @staticmethod
    def _get_exchange_name(name):
        """Get exchange name.
        """
        if name == 'Hitbtc':
            return 'HitBTC'
        elif name == 'Okex':
            return "OKEx"
        elif name == "HuobiPro":
            return "Huobi"

        return name

    def _create_instrument_mapping(self):
        """Create instrument mapping.
        """
        mapping = {}
        instruments_notin_ccxt = {'UST/USD': 'UST-USD'}
        for name in self._instruments.keys():
            if self._name.lower() == 'bitmex' or self._type == 'futures' or self._type == 'swap':
                # BitMEX uses the instrument name directly
                # without normalizing to cryptofeed convention
                normalized_name = name
            elif name in instruments_notin_ccxt.keys():
                normalized_name = instruments_notin_ccxt[name]
            else:

                market = self._exchange_interface.markets[name]
                normalized_name = market['base'] + '-' + market['quote']
            mapping[normalized_name] = name

        return mapping

    def _update_order_book_callback(self, feed, pair, book, timestamp, receipt_timestamp):
        if pair in self._instrument_mapping:
            # The instrument pair can be mapped directly from crypofeed
            # format to the ccxt format
            instmt_info = self._instruments[self._instrument_mapping[pair]]
        else:
            pass
        order_book = {}
        bids = []
        asks = []
        order_book['bids'] = bids
        order_book['asks'] = asks
        for price, volume in book[BID].items():
            bids.append((float(price), float(volume)))
        for price, volume in book[ASK].items():
            asks.append((float(price), float(volume)))
        is_updated = instmt_info.update_bids_asks(
            bids=bids,
            asks=asks)
        if not is_updated:
            return
        self._quotes_store.update_depth(feed=feed, pair=pair, timestamp=timestamp, bids=bids, asks=asks)

    def _update_kline_callback(self, feed, pair, timestamp, receipt_timestamp, kline):
        self._quotes_store.update_kline_queue(feed=feed, pair=pair, timestamp=timestamp, kline=kline)

    def _update_book_ticker_callback(self, feed, pair, best_bid, best_bid_size, best_ask, best_ask_size,
                                     timestamp,
                                     receipt_timestamp=None):
        self._quotes_store.update_best_price_queue(feed=feed, pair=pair, timestamp=timestamp, best_bid=best_bid,
                                              best_bid_size=best_bid_size, best_ask=best_ask,
                                              best_ask_size=best_ask_size)

    def _check_valid_instrument(self):
        """Check valid instrument.
        """
        skip_checking_exchanges = ['bitmex', 'bitfinex', 'okex']
        if self._name.lower() in skip_checking_exchanges:
            # Skip checking on BitMEX
            # Skip checking on Bitfinex
            return

        for instrument_code in self._config['instruments']:
            if instrument_code not in self._exchange_interface.markets:
                raise RuntimeError(
                    'Instrument %s is not found in exchange %s',
                    instrument_code, self._name)

    def _update_trade_callback(
        self, feed, pair, order_id, timestamp, side, amount, price, receipt_timestamp):
        """Update trade callback.
        """
        instmt_info = self._instruments[self._instrument_mapping[pair]]
        trade = {}

        if isinstance(timestamp, str):
            if (len(timestamp) == 27 and
                re.search(FULL_UTC_PATTERN, timestamp) is not None):
                timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
                timestamp = timestamp.timestamp()
                trade['timestamp'] = timestamp
            else:
                trade['timestamp'] = float(timestamp)
        else:
            trade['timestamp'] = timestamp

        trade['id'] = order_id
        trade['price'] = float(price)
        trade['amount'] = float(amount)
        current_timestamp = datetime.utcnow()
        if not instmt_info.update_trade(trade, current_timestamp):
            return

        trades = instmt_info._get_trades()
        price = trade['price']
        amount = trade['amount']
        id = trade['id']
        timestamp = trade['timestamp']
        # LOGGER.info("trade_callback pair=%s, feed=%s, price=%f, amount=%f, id=%s, time=%f", pair, feed, price, amount,
        #             id, timestamp)
        return
        # for handler in self._handlers.values():
        #     instmt_info.update_table(handler=handler)
        # self._rotate_ordre_tables()

    def _update_ticker_callback(self, feed, pair, last_price, first_bid, first_ask, timestamp, receipt_timestamp):
        return
