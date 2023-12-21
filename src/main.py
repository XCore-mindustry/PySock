import argparse
import asyncio
import logging

class SockProtocol(asyncio.Protocol):
   def __init__(self, server):
       self.server = server

   # noinspection PyAttributeOutsideInit
   def connection_made(self, transport: asyncio.Transport):
       self.transport = transport
       peername = transport.get_extra_info('peername')

       if peername[0] != '127.0.0.1':
           logging.info(f"Closing connection to non-loopback client: {peername}")
           self.transport.close()
       else:
           logging.info(f"{peername[0]}:{peername[1]} connected")
           self.server.clients.append(self)

   def connection_lost(self, exc):
       peername = self.transport.get_extra_info('peername')
       logging.info(f"Connection lost: {peername[0]}:{peername[1]}")
       self.server.clients.remove(self)

   def data_received(self, data):
       logging.debug(f"Received data: {data}")
       self.server.broadcast(data, except_for=self)

   def write_data(self, data):
       self.transport.write(data)

   def close(self):
       self.transport.close()

class SockServer:
   def __init__(self):
       self.clients: list[SockProtocol] = []

   def broadcast(self, data, except_for: SockProtocol = None):
       for client in self.clients:
           if client == except_for:
               continue
           client.write_data(data)

async def run(port: int):
   loop = asyncio.get_event_loop()
   server = SockServer()

   server_coroutine = await loop.create_server(lambda: SockProtocol(server), '127.0.0.1', port)
   sockname = server_coroutine.sockets[0].getsockname()
   logging.info(f"Serving on {sockname[0]}:{sockname[1]}")

   await server_coroutine.serve_forever()

if __name__ == "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument("-p", "--port", type=int, default=2000)
   parser.add_argument("-v", "--verbose", default=False)
   args = parser.parse_args()

   logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

   loop = asyncio.new_event_loop()
   asyncio.set_event_loop(loop)

   loop.run_until_complete(run(args.port))