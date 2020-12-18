
# 向服务器端认证，用户名密码通过才能退出循环
import asyncio
import sys

import websockets

sys.setrecursionlimit(10000)


async def auth_system(websocket):
    while True:
        await websocket.send("{\"method\": \"SUBSCRIBE\",\"params\":[\"btcusdt@aggTrade\",\"btcusdt@depth\"],\"id\": 1}")
        response_str = await websocket.recv()
        print(response_str)

# 向服务器端发送认证后的消息
# async def send_msg(websocket):
#     while True:
#         _text = input("please enter your context: ")
#         if _text == "exit":
#             print(f'you have enter "exit", goodbye')
#             await websocket.close(reason="user exit")
#             return False
#         await websocket.send(_text)
#         recv_text = await websocket.recv()
#         print(f"{recv_text}")

# 客户端主逻辑
async def main_logic():
    async with websockets.connect('wss://fstream.binance.com/ws/<BTCUSDT>@markPrice@1s') as websocket:
        await auth_system(websocket)
        # await send_msg(websocket)

asyncio.get_event_loop().run_until_complete(main_logic())
