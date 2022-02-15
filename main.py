import asyncio
import signal
import websockets
import yaml
import json
from app_message import AppMessage
from config import Config


async def connection_process():
    # read yaml file
    config: Config = None
    with open("config.yaml", 'r') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)
        config_file.close()
    if config is None:
        raise Exception("Config file not found")
    if config['endpoint'] is None:
        raise Exception("Endpoint not found")
    if config['device_id'] is None:
        raise Exception("Device ID not found")
    async with websockets.connect(config['endpoint']) as websocket:
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(
            signal.SIGTERM, loop.create_task, websocket.close())
        if websocket.open:
            await websocket.send(json.dumps(AppMessage(
                id=config['device_id'],
                event='connect',
                payload='',
            )))
        async for message in websocket:
            data: AppMessage = json.loads(message)


if __name__ == "__main__":
    asyncio.run(connection_process())
