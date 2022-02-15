from app_message import AppMessage
import subprocess

from utils import read_project_config


def command_processing(message: AppMessage):
    if message['event'] == "income_work":
        print(message['payload'])
        clone_process = subprocess.run([
            "git",
            "clone",
            message['payload'],
            "temp"
        ])
        try:
            clone_process.check_returncode()
        except subprocess.CalledProcessError:
            print("Error: git clone failed")
            return
        make_process = subprocess.run([
            "make",
            "-C",
            "temp",
            "all"
        ])
        try:
            make_process.check_returncode()
        except subprocess.CalledProcessError:
            print("Error: make failed")
            return
        binary_file_name: str = None
        project_config = read_project_config()
        for line in project_config:
            if "ProjectManager.ProjectName" in line:
                project_name = line.split("=")
                binary_file_name = project_name[-1]
                break
        print(binary_file_name)
        upload_process = subprocess.run([
            "openocd",
            "-f",
            "./openocd.cfg",
            "-c",
            f"program ./temp/build/{binary_file_name}.elf verify reset exit"
        ])
        try:
            upload_process.check_returncode()
        except subprocess.CalledProcessError:
            print("Error: openocd failed")
            return
        print("Success")
