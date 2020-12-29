'''
Copyright (C) 2017-2020  Bryant Moscon - bmoscon@gmail.com

Please see the LICENSE file for the terms and conditions
associated with this software.
'''
import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from time import time

import aiohttp
from sortedcontainers import SortedDict as sd
from yapic import json

from cryptofeed.defines import BID, ASK, BINANCE, BUY, FUNDING, L2_BOOK, LIQUIDATIONS, OPEN_INTEREST, SELL, TICKER, \
    TRADES, BOOK_TICKER, KLINE
from cryptofeed.feed import Feed
from cryptofeed.standards import pair_exchange_to_std, timestamp_normalize

LOG = logging.getLogger('feedhandler')


class Binance(Feed):
    id = BINANCE

    def __init__(self, pairs=None, channels=None, callbacks=None, depth=1000, **kwargs):
        super().__init__(None, pairs=pairs, channels=channels, callbacks=callbacks, **kwargs)
        self.book_depth = depth
        self.ws_endpoint = 'wss://stream.binance.com:9443'
        self.rest_endpoint = 'https://www.binance.com/api/v1'
        self.address = self._address()
        self._reset()

    def _address(self):
        address = self.ws_endpoint + '/stream?streams='
        for chan in self.channels if not self.config else self.config:
            for pair in self.pairs if not self.config else self.config[chan]:
                pair = pair.lower()
                stream = f"{pair}@{chan}/"
                address += stream
        return address[:-1]

    def _reset(self):
        self.forced = defaultdict(bool)
        self.l2_book = {}
        self.last_update_id = {}
        self.open_interest = {}

    async def _trade(self, msg: dict, timestamp: float):
        """
        {
            "e": "aggTrade",  // Event type
            "E": 123456789,   // Event time
            "s": "BNBBTC",    // Symbol
            "a": 12345,       // Aggregate trade ID
            "p": "0.001",     // Price
            "q": "100",       // Quantity
            "f": 100,         // First trade ID
            "l": 105,         // Last trade ID
            "T": 123456785,   // Trade time
            "m": true,        // Is the buyer the market maker?
            "M": true         // Ignore
        }
        """
        price = Decimal(msg['p'])
        amount = Decimal(msg['q'])
        await self.callback(TRADES, feed=self.id,
                            order_id=msg['a'],
                            pair=pair_exchange_to_std(msg['s']),
                            side=SELL if msg['m'] else BUY,
                            amount=amount,
                            price=price,
                            timestamp=timestamp_normalize(self.id, msg['E']),
                            receipt_timestamp=timestamp)

    async def _ticker(self, msg: dict, timestamp: float):
        """
        {
          "e":"bookTicker",     // 事件类型
          "u":400900217,        // 更新ID
          "E": 1568014460893,   // 事件推送时间
          "T": 1568014460891,   // 撮合时间
          "s":"BNBUSDT",        // 交易对
          "b":"25.35190000",    // 买单最优挂单价格
          "B":"31.21000000",    // 买单最优挂单数量
          "a":"25.36520000",    // 卖单最优挂单价格
          "A":"40.66000000"     // 卖单最优挂单数量
        }
        """
        pair = pair_exchange_to_std(msg['s'])
        bid = Decimal(msg['b'])
        ask = Decimal(msg['a'])
        last_price = (bid + ask) / 2
        await self.callback(TICKER, feed=self.id,
                            pair=pair,
                            last_price=last_price,
                            first_bid=bid,
                            first_ask=ask,
                            timestamp=timestamp_normalize(self.id, msg['E']),
                            receipt_timestamp=timestamp)

    async def _book_ticker(self, msg: dict, timestamp: float):
        """
        {
          "e":"bookTicker",     // 事件类型
          "u":400900217,        // 更新ID
          "E": 1568014460893,   // 事件推送时间
          "T": 1568014460891,   // 撮合时间
          "s":"BNBUSDT",        // 交易对
          "b":"25.35190000",    // 买单最优挂单价格
          "B":"31.21000000",    // 买单最优挂单数量
          "a":"25.36520000",    // 卖单最优挂单价格
          "A":"40.66000000"     // 卖单最优挂单数量
        }
        """
        pair = pair_exchange_to_std(msg['s'])
        bid = Decimal(msg['b'])
        ask = Decimal(msg['a'])
        last_price = (bid + ask) / 2
        #self, feed, pair, last_price, first_bid, first_ask, timestamp, receipt_timestamp
        await self.callback(BOOK_TICKER, feed=self.id,
                            pair=pair,
                            last_price=last_price,
                            first_bid=bid,
                            first_ask=ask,
                            timestamp=timestamp_normalize(self.id, msg['E']),
                            receipt_timestamp=timestamp)

    async def _liquidations(self, msg: dict, timestamp: float):
        """
        {
        "e":"forceOrder",       // Event Type
        "E":1568014460893,      // Event Time
        "o":{
            "s":"BTCUSDT",      // Symbol
            "S":"SELL",         // Side
            "o":"LIMIT",        // Order Type
            "f":"IOC",          // Time in Force
            "q":"0.014",        // Original Quantity
            "p":"9910",         // Price
            "ap":"9910",        // Average Price
            "X":"FILLED",       // Order Status
            "l":"0.014",        // Order Last Filled Quantity
            "z":"0.014",        // Order Filled Accumulated Quantity
            "T":1568014460893,  // Order Trade Time
            }
        }
        """
        pair = pair_exchange_to_std(msg['o']['s'])
        await self.callback(LIQUIDATIONS,
                            feed=self.id,
                            pair=pair,
                            side=msg['o']['S'],
                            leaves_qty=Decimal(msg['o']['q']),
                            price=Decimal(msg['o']['p']),
                            order_id=None,
                            timestamp=timestamp_normalize(self.id, msg['E']),
                            receipt_timestamp=timestamp)

    async def _snapshot(self, pair: str) -> None:
        url = f'{self.rest_endpoint}/depth?symbol={pair}&limit={self.book_depth}'

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                resp = await response.json()

                std_pair = pair_exchange_to_std(pair)
                self.last_update_id[std_pair] = resp['lastUpdateId']
                self.l2_book[std_pair] = {BID: sd(), ASK: sd()}
                for s, side in (('bids', BID), ('asks', ASK)):
                    for update in resp[s]:
                        price = Decimal(update[0])
                        amount = Decimal(update[1])
                        self.l2_book[std_pair][side][price] = amount

    def _check_update_id(self, pair: str, msg: dict) -> (bool, bool):
        skip_update = False
        forced = not self.forced[pair]

        if forced and msg['u'] <= self.last_update_id[pair]:
            skip_update = True
        elif forced and msg['U'] <= self.last_update_id[pair] + 1 <= msg['u']:
            self.last_update_id[pair] = msg['u']
            self.forced[pair] = True
        elif not forced and self.last_update_id[pair] + 1 == msg['U']:
            self.last_update_id[pair] = msg['u']
        else:
            self._reset()
            LOG.warning("%s: Missing book update detected, resetting book", self.id)
            skip_update = True

        return skip_update, forced

    async def _book(self, msg: dict, pair: str, timestamp: float):
        """
        {
            "e": "depthUpdate", // Event type
            "E": 123456789,     // Event time
            "s": "BNBBTC",      // Symbol
            "U": 157,           // First update ID in event
            "u": 160,           // Final update ID in event
            "b": [              // Bids to be updated
                    [
                        "0.0024",       // Price level to be updated
                        "10"            // Quantity
                    ]
            ],
            "a": [              // Asks to be updated
                    [
                        "0.0026",       // Price level to be updated
                        "100"           // Quantity
                    ]
            ]
        }
        """
        exchange_pair = pair
        pair = pair_exchange_to_std(pair)

        if pair not in self.l2_book:
            await self._snapshot(exchange_pair)

        skip_update, forced = self._check_update_id(pair, msg)
        if skip_update:
            return

        delta = {BID: [], ASK: []}
        ts = msg['E']

        for s, side in (('b', BID), ('a', ASK)):
            for update in msg[s]:
                price = Decimal(update[0])
                amount = Decimal(update[1])

                if amount == 0:
                    if price in self.l2_book[pair][side]:
                        del self.l2_book[pair][side][price]
                        delta[side].append((price, amount))
                else:
                    self.l2_book[pair][side][price] = amount
                    delta[side].append((price, amount))

        await self.book_callback(self.l2_book[pair], L2_BOOK, pair, forced, delta, timestamp_normalize(self.id, ts),
                                 timestamp)

    async def _open_interest(self, pairs: list):
        """
        {
            "openInterest": "10659.509",
            "symbol": "BTCUSDT",
            "time": 1589437530011   // Transaction time
        }
        """

        rate_limiter = 2  # don't fetch too many pairs too fast
        async with aiohttp.ClientSession() as session:
            while True:
                for pair in pairs:
                    end_point = f"{self.rest_endpoint}/openInterest?symbol={pair}"
                    async with session.get(end_point) as response:
                        data = await response.text()
                        data = json.loads(data, parse_float=Decimal)

                        oi = data['openInterest']
                        if oi != self.open_interest.get(pair, None):
                            await self.callback(OPEN_INTEREST,
                                                feed=self.id,
                                                pair=pair_exchange_to_std(pair),
                                                open_interest=oi,
                                                timestamp=timestamp_normalize(self.id, data['time']),
                                                receipt_timestamp=time()
                                                )
                            self.open_interest[pair] = oi
                            await asyncio.sleep(rate_limiter)
                # Binance updates OI every 15 minutes, however not all pairs are ready exactly at :15 :30 :45 :00
                wait_time = (17 - (datetime.now().minute % 15)) * 60
                await asyncio.sleep(wait_time)

    async def _funding(self, msg: dict, timestamp: float):
        """
        {
            "e": "markPriceUpdate",  // Event type
            "E": 1562305380000,      // Event time
            "s": "BTCUSDT",          // Symbol
            "p": "11185.87786614",   // Mark price
            "r": "0.00030000",       // Funding rate
            "T": 1562306400000       // Next funding time
        }
        """
        await self.callback(FUNDING,
                            feed=self.id,
                            pair=pair_exchange_to_std(msg['s']),
                            timestamp=timestamp_normalize(self.id, msg['E']),
                            receipt_timestamp=timestamp,
                            mark_price=msg['p'],
                            rate=msg['r'],
                            next_funding_time=timestamp_normalize(self.id, msg['T']),
                            )

    async def continuousKline(self, msg: dict, timestamp: float):
        """{
          "e":"continuous_kline",   // 事件类型
          "E":1607443058651,        // 事件时间
          "ps":"BTCUSDT",           // 标的交易对
          "ct":"PERPETUAL",         // 合约类型
          "k":{
            "t":1607443020000,      // 这根K线的起始时间
            "T":1607443079999,      // 这根K线的结束时间
            "i":"1m",               // K线间隔
            "f":116467658886,       // 这根K线期间第一笔成交ID
            "L":116468012423,       // 这根K线期间末一笔成交ID
            "o":"18787.00",         // 这根K线期间第一笔成交价
            "c":"18804.04",         // 这根K线期间末一笔成交价
            "h":"18804.04",         // 这根K线期间最高成交价
            "l":"18786.54",         // 这根K线期间最低成交价
            "v":"197.664",          // 这根K线期间成交量
            "n":543,                // 这根K线期间成交笔数
            "x":false,              // 这根K线是否完结(是否已经开始下一根K线)
            "q":"3715253.19494",    // 这根K线期间成交额
            "V":"184.769",          // 主动买入的成交量
            "Q":"3472925.84746",    // 主动买入的成交额
            "B":"0"                 // 忽略此参数
          }
        }
        """
        await self.callback(KLINE,
                            feed=self.id,
                            pair=pair_exchange_to_std(msg['s']),
                            timestamp=timestamp_normalize(self.id, msg['E']),
                            receipt_timestamp=timestamp,
                            kline=msg['k']
                            )

    async def message_handler(self, msg: str, timestamp: float):
        msg = json.loads(msg, parse_float=Decimal)

        # Combined stream events are wrapped as follows: {"stream":"<streamName>","data":<rawPayload>}
        # streamName is of format <symbol>@<channel>
        pair, _ = msg['stream'].split('@', 1)
        msg = msg['data']

        pair = pair.upper()

        if msg['e'] == 'bookTicker':
            await self._book_ticker(msg, pair, timestamp)
        if msg['e'] == 'depthUpdate':
            await self._book(msg, pair, timestamp)
        elif msg['e'] == 'aggTrade':
            await self._trade(msg, timestamp)
        elif msg['e'] == '24hrTicker':
            await self._ticker(msg, timestamp)
        elif msg['e'] == 'forceOrder':
            await self._liquidations(msg, timestamp)
        elif msg['e'] == 'markPriceUpdate':
            await self._funding(msg, timestamp)
        else:
            LOG.warning("%s: Unexpected message received: %s", self.id, msg)

    async def subscribe(self, websocket):
        # Binance does not have a separate subscribe message, the
        # subsription information is included in the
        # connection endpoint
        for chan in self.channels if self.channels else self.config:
            if chan == 'open_interest':
                asyncio.create_task(self._open_interest(self.pairs if self.pairs else self.config[chan]))
                break
        self._reset()
