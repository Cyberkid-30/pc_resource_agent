# monitor.py

import psutil


def get_processes():

    processes = []

    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            process_info = {
                "pid": proc.info["pid"],
                "name": proc.info["name"],
                "cpu": proc.info["cpu_percent"],
                "memory": proc.info["memory_percent"],
            }

            processes.append(process_info)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return processes


def terminate_process(pid):

    try:
        proc = psutil.Process(pid)
        proc.terminate()
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False
