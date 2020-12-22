'''
Copyright (C) 2017-2020  Bryant Moscon - bmoscon@gmail.com

Please see the LICENSE file for the terms and conditions
associated with this software.
'''
from decimal import Decimal
import logging

from yapic import json

from cryptofeed.defines import BINANCE_FUTURES, OPEN_INTEREST, TICKER, BOOK_TICKER
from cryptofeed.exchange.binance import Binance
from cryptofeed.standards import pair_exchange_to_std, timestamp_normalize

LOG = logging.getLogger('feedhandler')


class BinanceFutures(Binance):
    id = BINANCE_FUTURES

    def __init__(self, pairs=None, channels=None, callbacks=None, depth=100, **kwargs):
        super().__init__(pairs=pairs, channels=channels, callbacks=callbacks, depth=depth, **kwargs)
        self.ws_endpoint = 'wss://fstream.binance.com'
        self.rest_endpoint = 'https://fapi.binance.com/fapi/v1'
        self.address = self._address()

    def _address(self):
        address = self.ws_endpoint + '/stream?streams='
        for chan in self.channels if not self.config else self.config:
            if chan == OPEN_INTEREST:
                continue
            for pair in self.pairs if not self.config else self.config[chan]:
                pair = pair.lower()
                if chan == BOOK_TICKER:
                    stream = f"{pair}@bookTicker/"
                elif chan == TICKER:
                    stream = f"{pair}@ticker/"
                else:
                    stream = f"{pair}@{chan}/"
                address += stream
        if address == f"{self.ws_endpoint}/stream?streams=":
            return None
        LOG.warning("address load self.address= %s", address)

        return address[:-1]

    def _check_update_id(self, pair: str, msg: dict) -> (bool, bool):
        skip_update = False
        forced = not self.forced[pair]

        if forced and msg['u'] < self.last_update_id[pair]:
            skip_update = True
        elif forced and msg['U'] <= self.last_update_id[pair] <= msg['u']:
            self.last_update_id[pair] = msg['u']
            self.forced[pair] = True
        elif not forced and self.last_update_id[pair] == msg['pu']:
            self.last_update_id[pair] = msg['u']
        else:
            self._reset()
            LOG.warning("%s: Missing book update detected, resetting book", self.id)
            skip_update = True
        return skip_update, forced

    async def message_handler(self, msg: str, timestamp: float):
        msg = json.loads(msg, parse_float=Decimal)

        # Combined stream events are wrapped as follows: {"stream":"<streamName>","data":<rawPayload>}
        # streamName is of format <symbol>@<channel>
        pair, _ = msg['stream'].split('@', 1)
        msg = msg['data']

        pair = pair.upper()

        msg_type = msg.get('e')
        if msg_type == 'bookTicker':
            # For the BinanceFutures API it appears
            # the ticker stream (<symbol>@bookTicker) is
            # the only payload without an "e" key describing the event type
            await self._book_ticker(msg, timestamp)
        elif msg_type == '24hrTicker':
            await self._24hticker(msg, timestamp)
        elif msg_type == 'depthUpdate':
            await self._book(msg, pair, timestamp)
        elif msg_type == 'aggTrade':
            await self._trade(msg, timestamp)
        elif msg_type == 'forceOrder':
            await self._liquidations(msg, timestamp)
        elif msg_type == 'markPriceUpdate':
            await self._funding(msg, timestamp)
        else:
            LOG.warning("%s: Unexpected message received: %s, msg_type:%s", self.id, msg, msg_type)

    async def _24hticker(self, msg: dict, timestamp: float):
        """
        {
          "e": "24hrTicker",  // 事件类型
          "E": 123456789,     // 事件时间
          "s": "BNBUSDT",      // 交易对
          "p": "0.0015",      // 24小时价格变化
          "P": "250.00",      // 24小时价格变化(百分比)
          "w": "0.0018",      // 平均价格
          "c": "0.0025",      // 最新成交价格
          "Q": "10",          // 最新成交价格上的成交量
          "o": "0.0010",      // 24小时内第一比成交的价格
          "h": "0.0025",      // 24小时内最高成交价
          "l": "0.0010",      // 24小时内最低成交加
          "v": "10000",       // 24小时内成交量
          "q": "18",          // 24小时内成交额
          "O": 0,             // 统计开始时间
          "C": 86400000,      // 统计关闭时间
          "F": 0,             // 24小时内第一笔成交交易ID
          "L": 18150,         // 24小时内最后一笔成交交易ID
          "n": 18151          // 24小时内成交数
        }
        """
        pair = pair_exchange_to_std(msg['s'])
        last_price = Decimal(msg['c'])
        avg_price = Decimal(msg['w'])
        first_bid = Decimal(msg['b'])
        first_ask = Decimal(msg['a'])
        await self.callback(TICKER, feed=self.id,
                            pair=pair,
                            last_price=last_price,
                            avg_price=avg_price,
                            first_bid=first_bid,
                            first_ask=first_ask,
                            timestamp=timestamp_normalize(self.id, msg['E']),
                            receipt_timestamp=timestamp)
