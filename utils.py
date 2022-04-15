import subprocess
import os


# serach for a .ioc file in the "./temp" directory
def read_project_config():
    for file in os.listdir("./temp"):
        if file.endswith(".ioc"):
            with open("./temp/" + file, 'r') as project_config:
                return project_config.readlines()
    return None


micro_mult = 0.000001
milli_mul = 0.001


def system_utilization_usage(log_file_name: str = "ps.log") -> subprocess.Popen:
    return subprocess.Popen(
        ["while true; do (echo \" % CPU % MEM ARGS $(date)\" && ps  -e -o pcpu,pmem,args --sort=pcpu | grep 'python3\|pigpiod$' | cut -d\" \" -f1-5 | tail) >> {}; sleep 1; done".format(log_file_name)],
        shell=True,
    )
