from ast import While
import json
import os
from app_message import AppMessage
import requests
import wget
from testing import test
import subprocess

from testing_schema import Schema
# st-flash --reset write led_f7.bin 0x8000000

TEST_SCRIPT_NAME = "TEST_SCRIPT_NAME.json"
BIN_NAME = "app.bin"
RESULT_NAME = "result.json"


def command_processing(message: AppMessage):
    if message['event'] == "incoming_work":
        res = requests.get(
            "http://cdn.crosszfrost.xyz:3001/queue/"+message['payload'])
        queue = json.loads(res.text)
        # remove file if exists
        if os.path.exists(TEST_SCRIPT_NAME):
            os.remove(TEST_SCRIPT_NAME)
        if os.path.exists(BIN_NAME):
            os.remove(BIN_NAME)
        if os.path.exists(RESULT_NAME):
            os.remove(RESULT_NAME)
        wget.download(queue['working']['lab']
                      ['test_script_url'], TEST_SCRIPT_NAME)
        file_name = None
        # waiting for compiling
        print('\ndownloading\n')
        while file_name is None:
            try:
                file_name = wget.download('http://cdn.crosszfrost.xyz:8888/student/{}/{}/bin/app.bin'.format(
                    queue['working']['lab']['id'], queue['id']), BIN_NAME)
            except:
                file_name = None
        print('loaded test script')
        test_script: list[Schema] = None
        with open(TEST_SCRIPT_NAME, 'r') as file:
            try:
                test_script = json.load(file)
            except:
                print('error')
                return AppMessage({
                    'id': message['id'],
                    'event': 'error',
                    'payload': 'Invalid test script',
                })
            file.close()
        if test_script is None:
            return AppMessage({
                'id': message['id'],
                'event': 'error',
                'payload': 'Invalid test script',
            })
        if os.path.exists(BIN_NAME) is False:
            return AppMessage({
                'id': message['id'],
                'event': 'error',
                'payload': 'Binary file not found',
            })
        # flash binary
        res = ""
        # always try to flash 2 times
        try:
            res = subprocess.check_output(
                ["st-flash", "--reset", "write", BIN_NAME, "0x8000000"]).decode('utf-8')
        except subprocess.CalledProcessError as e:
            res = "try1"

        if res == "try1":
            try:
                res = subprocess.check_output(
                    ["st-flash", "--reset", "write", BIN_NAME, "0x8000000"]).decode('utf-8')
            except:
                if("ERROR" in res):
                    return AppMessage({
                        'id': message['id'],
                        'event': 'error',
                        'payload': 'Flash error',
                    })
        if("ERROR" in res):
            return AppMessage({
                'id': message['id'],
                'event': 'error',
                'payload': 'Flash error',
            })
        # run test
        result = test(test_script)
        if(result is not None):
            with open(RESULT_NAME, 'rb') as file:
                requests.post('http://cdn.crosszfrost.xyz:8888/student/{}/{}/result/{}'.format(
                    queue['working']['lab']['id'], queue['id'], RESULT_NAME),files={'file': file})
            # clean up
            if os.path.exists(TEST_SCRIPT_NAME):
                os.remove(TEST_SCRIPT_NAME)
            if os.path.exists(BIN_NAME):
                os.remove(BIN_NAME)
            if os.path.exists(RESULT_NAME):
                os.remove(RESULT_NAME)
            if result == "pass":
                return AppMessage({
                    'id': message['id'],
                    'event': 'finished',
                    'payload': 'pass',
                })
            else:
                return AppMessage({
                    'id': message['id'],
                    'event': 'finished',
                    'payload': 'fail',
                })
