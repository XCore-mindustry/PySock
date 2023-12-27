import argparse
import logging
import asyncio

from eventbus import EventBus
from asyncio import StreamReader, StreamWriter

import orjson
import aioconsole

from util import ByteBuffer

logger = logging.getLogger(__name__)


class SockClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader: StreamReader = None
        self.writer: StreamWriter = None

        self.bus = EventBus()

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            logger.info(f"Connected to server at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            await self.close()

    async def post_event(self, key: str, data: object):
        if self.writer:
            try:
                json = orjson.dumps(data)
                buffer = ByteBuffer.allocate(4 + len(key) + len(json))

                buffer.put_UBInt8(len(key))
                buffer.put(bytearray(key, "utf-8"))

                buffer.put_UBInt16(len(json))
                buffer.put(bytearray(json))
                re = buffer.read()
                print(re)
                self.writer.write(re)
                await self.writer.drain()
            except Exception as e:
                logger.error(f"Failed to send event", exc_info=e)

    async def on_receive(self):
        while True:
            data = await self.reader.read(1024)
            if not data:
                break
            try:
                buffer = ByteBuffer.wrap(bytearray(data))

                keylen = buffer.get_UBInt8()
                key = buffer.get_bytes(keylen).decode()

                jsonlen = buffer.get_UBInt16()
                jsonstr = buffer.get_bytes(jsonlen).decode()
                json = orjson.loads(jsonstr)

                self.bus.fire(key, json)
            except Exception as e:
                logger.error(f"Failed to encode event", exc_info=e)

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            logger.info("Connection closed")


async def main():
    parser = argparse.ArgumentParser(description="Interactive client for SockServer")
    parser.add_argument("-H", "--host", default="localhost")
    parser.add_argument("-p", "--port", type=int, default=2000)
    parser.add_argument("-v", "--verbose", default=False)
    args = parser.parse_args()

    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    client = SockClient(args.host, args.port)
    client.bus.on("message", lambda data: print(f"Received message: {data['message']}"))
    try:
        await client.connect()

        task1 = asyncio.create_task(client.on_receive())
        task2 = asyncio.create_task(send_loop(client))

        await asyncio.gather(task1, task2)
    except asyncio.CancelledError:
        pass  # Allow cancellation for graceful exit
    except Exception as e:
        logger.error(f"Unexpected error", exc_info=e)
    finally:
        await client.close()  # Ensure closure in all cases


async def send_loop(client):
    while True:
        message = await aioconsole.ainput("Enter message to send (or 'quit' to exit): ")
        if message == "quit":
            break
        await client.post_event("message", {"message": message})


if __name__ == "__main__":
    asyncio.run(main())
