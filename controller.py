from app_message import AppMessage
import subprocess

from utils import read_project_config


def command_processing(message: AppMessage):
    if message['event'] == "incoming_work":
        pass
