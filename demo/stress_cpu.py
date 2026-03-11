# stress_cpu.py
import multiprocessing


def burn_cpu():
    while True:
        _ = sum(i * i for i in range(10_000))


if __name__ == "__main__":
    # Spawn workers to max out CPU
    for _ in range(multiprocessing.cpu_count()):
        p = multiprocessing.Process(target=burn_cpu)
        p.start()
