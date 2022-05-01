import asyncio
from email import message
import signal

from controller import command_processing
import websockets
import yaml
import json
from app_message import AppMessage
from config import Config

config: Config = None


async def connection_process():
    # read yaml file
    global config
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
            print(config)
            await websocket.send(json.dumps(AppMessage(
                id=config['device_id'],
                event='connected',
                payload='',
            )))
        while websocket.open:
            message = await websocket.recv()
            data: AppMessage = json.loads(message)
            print(data)
            if(data.get('id') == config.get('device_id')):
                r = command_processing(data)
                if r is not None:
                    await websocket.send(json.dumps(r))
                    print("sended")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(connection_process())
