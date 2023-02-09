import asyncio
import logging
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from main import as_get_curr_ratelist, check_args

logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message[:8] == 'exchange':
                message = await as_get_curr_ratelist(parse_message(message[9:]))
                await self.send_to_clients(f"currency rate: {format_rate(message)}")
            else:
                await self.send_to_clients(f"{ws.name}: {message}")

def format_rate(raw_rate: list) -> str:
    rez = ""
    if len(raw_rate):
        for itr_d in raw_rate:
            for f_data in itr_d.keys():
                rez += f'on {f_data} rate'
                for f_cur in itr_d[f_data].keys():
                    rez += f': {f_cur} '
                    for f_rate in itr_d[f_data][f_cur].keys():
                        rez += f': {f_rate} {itr_d[f_data][f_cur][f_rate]} '


    return rez


def parse_message(message):
    list_mes = message.split(' ')
    if len(list_mes):
        try:
            day = int(list_mes[0])
        except IndexError:
            logging.info(f'{list_mes} has no 0 index')
            day = 2
        except ValueError:
            logging.info(f'{list_mes[0]} wait for int')
            day = 2
        try:
            cur_name = list_mes[1]
        except IndexError:
            logging.info(f'{list_mes} has no 1 index')
            cur_name = 'USD'
        return check_args(day, [cur_name])
    else:
        return [2, ['EUR', 'USD']]

async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    asyncio.run(main())
