import os


# serach for a .ioc file in the "./temp" directory
def read_project_config():
    for file in os.listdir("./temp"):
        if file.endswith(".ioc"):
            with open("./temp/" + file, 'r') as project_config:
                return project_config.readlines()
    return None
