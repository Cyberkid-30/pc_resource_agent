import psutil


# First call to cpu_percent() always returns 0.0 — we need to prime it.
# By calling process_iter once at import time, subsequent calls within
# MONITOR_INTERVAL will return meaningful delta-based CPU readings.
for _proc in psutil.process_iter(["cpu_percent"]):
    pass


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
