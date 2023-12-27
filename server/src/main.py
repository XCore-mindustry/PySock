import asyncio
import argparse
import logging

logger = logging.getLogger(__name__)

clients = set()


async def broadcast(data, exclude=None):
    if not clients:
        return

    for writer in clients:
        if writer is not exclude:
            writer.write(data)
            await writer.drain()


async def client_handle(reader, writer):
    clients.add(writer)

    peername = writer.transport.get_extra_info('peername')
    ip = f"{peername[0]}:{peername[1]}"
    logger.info(f"{ip} connected")

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
            logger.debug(f"{ip}: received data {data!r}")
            await broadcast(data, exclude=writer)

    except asyncio.CancelledError:
        pass  # Cancellation is expected on closing
    except Exception as exc:
        logger.error(f"{ip}: crashed", exc_info=exc)

    finally:
        logger.info(f"{ip}: connection closed")
        writer.close()


async def main(port):
    server = await asyncio.start_server(client_handle, 'localhost', port)
    logger.info(f"Listening on port {port}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-p", "--port", type=int, default=2000)
    parser.add_argument("-v", "--verbose", default=False)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(name)s:%(levelname)s:%(message)s',
    )

    asyncio.run(main(args.port))
