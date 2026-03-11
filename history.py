# history.py

import time
from collections import defaultdict

import config


class ProcessHistory:
    """Tracks per-process resource readings over time to enable time-based decisions."""

    def __init__(self):
        # {pid: [{"cpu": float, "memory": float, "timestamp": float}, ...]}
        self._records = defaultdict(list)

    def record(self, pid, cpu, memory):
        now = time.time()

        self._records[pid].append(
            {
                "cpu": cpu,
                "memory": memory,
                "timestamp": now,
            }
        )

        # Prune entries older than the history window
        cutoff = now - config.HISTORY_WINDOW
        self._records[pid] = [r for r in self._records[pid] if r["timestamp"] >= cutoff]

    def is_sustained_cpu(self, pid):
        """Return True if the process has been above the CPU critical threshold
        for at least SUSTAINED_DURATION seconds."""
        return self._is_sustained(pid, "cpu", config.CPU_CRITICAL_THRESHOLD)

    def is_sustained_memory(self, pid):
        """Return True if the process has been above the memory critical threshold
        for at least SUSTAINED_DURATION seconds."""
        return self._is_sustained(pid, "memory", config.MEMORY_CRITICAL_THRESHOLD)

    def _is_sustained(self, pid, metric, threshold):
        records = self._records.get(pid, [])

        if not records:
            return False

        now = time.time()
        cutoff = now - config.SUSTAINED_DURATION

        # We need readings spanning at least SUSTAINED_DURATION
        relevant = [r for r in records if r["timestamp"] >= cutoff]

        if not relevant:
            return False

        # Check that the earliest relevant record is old enough
        time_span = now - relevant[0]["timestamp"]
        if time_span < config.SUSTAINED_DURATION * 0.8:
            return False

        # All relevant readings must exceed the threshold
        return all(r[metric] > threshold for r in relevant)

    def remove(self, pid):
        self._records.pop(pid, None)

    def get_violation_duration(self, pid, metric, threshold):
        """Return how long (seconds) a process has been continuously above threshold."""
        records = self._records.get(pid, [])

        if not records:
            return 0.0

        now = time.time()

        # Walk backwards to find the first record that drops below threshold
        for i in range(len(records) - 1, -1, -1):
            if records[i][metric] <= threshold:
                if i + 1 < len(records):
                    return now - records[i + 1]["timestamp"]
                return 0.0

        # All records exceed threshold
        return now - records[0]["timestamp"]
