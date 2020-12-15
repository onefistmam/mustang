
import pickle
import multiprocessing as mp
from multiprocessing.reduction import ForkingPickler

from befh.handler import ZmqHandler, SqlHandler
from befh.handler.handler_operator import *

obj = SqlHandler(
                is_debug=False,
                is_cold=False,connection = "sqlite:///./order_book.db")
_queue = mp.Queue(4)
_queue.put(HandlerCreateTableOperator(
            table_name="lll",
            fields="abc"))
_queue.put(HandlerInsertOperator(
            table_name="lll",
            fields="abc"))
_queue.put(HandlerRenameTableOperator(
            from_name="lll",
            to_name="abc"))
_queue.put(HandlerOperator())

one = _queue.get()
one = _queue.get()
one = _queue.get()
one = _queue.get()
print(one)

# obj = 123, "abcdef", ["ac", 123], {"key": "value", "key1": "value1"}
print(obj)

# 序列化到文件
with open(r"/Users/cuijiangkun/local/tmp/a.txt", "wb") as f:
    pickle.dump(obj, f)
    ForkingPickler(f, None).dump(obj)

#
with open(r"/Users/cuijiangkun/local/tmp/a.txt", "rb") as f:

    print(pickle.load(f))# 输出：(123, 'abcdef', ['ac', 123], {'key': 'value', 'key1': 'value1'})
