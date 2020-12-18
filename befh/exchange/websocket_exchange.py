import logging
from datetime import datetime
import re

from cryptofeed import FeedHandler
from cryptofeed.defines import L2_BOOK, TRADES, BID, ASK, TICKER
from cryptofeed.callback import BookCallback, TradeCallback, TickerCallback
import cryptofeed.exchanges as cryptofeed_exchanges

from .rest_api_exchange import RestApiExchange

LOGGER = logging.getLogger(__name__)

FULL_UTC_PATTERN = '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z'


class WebsocketExchange(RestApiExchange):
    """Websocket exchange.
    """

    def __init__(self,
                 exchange_name,
                 subscription,
                 is_debug,
                 is_cold):
        """Constructor.
        """
        super().__init__(exchange_name,
                         subscription,
                         is_debug,
                         is_cold)
        self._feed_handler = None
        self._instrument_mapping = None

    def load(self, handlers=None):
        """Load.
        """
        super().load(is_initialize_instmt=False, handlers=handlers)
        self._feed_handler = FeedHandler()
        self._instrument_mapping = self._create_instrument_mapping()

        try:
            exchange = getattr(
                cryptofeed_exchanges,
                self._get_exchange_name(self._name))
        except AttributeError as e:
            raise ImportError(
                'Cannot load exchange %s from websocket' % self._name)

        contract_exchanges_use_common_channel = ['HuobiSwap', 'HuibiDM', 'KrakenFutures', 'BinanceFutures', 'Bitmex']
        if self._is_orders:
            LOGGER.info("exchange :%s, type:%s, _is_orders:%s", self._name, self._type, self._is_orders)
            if self._type == 'spot' or self._name in contract_exchanges_use_common_channel:
                channels = [
                    # TRADES,
                    # L2_BOOK,
                    TICKER
                ]
            # elif self._type == 'futures':
            #     channels = [TRADES_FUTURES, L2_BOOK_FUTURES]
            elif self._type == 'swap':
                channels = [L2_BOOK, TRADES, TICKER]
            LOGGER.info("WebsocketExchange init _instrument_mapping=%s, name=%s, channels=%s", self._instrument_mapping,
                        self._name, channels)

            callbacks = {
                # channels[0]: TradeCallback(self._update_trade_callback),
                # L2_BOOK: BookCallback(self._update_order_book_callback),
                TICKER: TickerCallback(self._update_ticker_callback)
            }
        else:
            if self._type == 'spot' or self._name in contract_exchanges_use_common_channel:
                channels = [TRADES]
            # elif self._type == 'futures':
            #     channels = [TRADES_FUTURES]
            # elif self._type == 'swap':
            #     channels = [TRADES_SWAP]

            callbacks = {
                channels[0]: TradeCallback(self._update_trade_callback),
            }

        if self._name.lower() == 'poloniex':
            self._feed_handler.add_feed(
                exchange(
                    channels=list(self._instrument_mapping.keys()),
                    callbacks=callbacks))
        else:
            insts = list(self._instrument_mapping.keys())
            LOGGER.info("add_feed feed=%s, callbacks=%s, _feed_handle=%s, insts=%s", channels, callbacks, self._feed_handler, insts)
            exchange = exchange(pairs=insts,
                     channels=channels,
                     callbacks=callbacks)
            self._feed_handler.add_feed(exchange)

    def run(self):
        """Run.
        """
        LOGGER.info("feed run")
        self._feed_handler.run()

    @staticmethod
    def _get_exchange_name(name):
        """Get exchange name.
        """
        LOGGER.info("get exchange name ,%s", name)
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
        """Update order book callback.
        """
        LOGGER.info("_update_order_book_callback, pair=%s, feed=%s, timestamp=%d", pair, feed, timestamp)

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
        LOGGER.info("_update_order_book_callback, pair=%s, exchange=%s, is_upd=%s", pair, feed, is_updated)
        if not is_updated:
            return

    def _update_ticker_callback(self, feed, pair, bid, ask, timestamp, receipt_timestamp):
        print("21311111")
        LOGGER.info("_update_ticker_callback feed :%s, pair:%s, bid:%9.4f, ask: %9.4f,timestamp:%d receipt_time:%d",
                    feed, pair, bid, ask, timestamp, receipt_timestamp)
        return

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

        for handler in self._handlers.values():
            instmt_info.update_table(handler=handler)

        self._rotate_order_tables()

    def _check_valid_instrument(self):
        """Check valid instrument.
        """
        skip_checking_exchanges = ['bitmex', 'bitfinex', 'okex']
        if self._name.lower() in skip_checking_exchanges:
            # Skip checking on BitMEX
            # Skip checking on Bitfinex
            return

        for instrument_code in self._config['instruments']:
            from befh.core.PairConverter import PairConverter
            # instrument_code = PairConverter.convertPair(instrument_code, exchange=self.name)
            # LOGGER.info("_check_valid_instrument pair=%s", instrument_code)
            if instrument_code not in self._exchange_interface.markets:
                raise RuntimeError(
                    'Instrument %s is not found in exchange %s',
                    instrument_code, self._name)
