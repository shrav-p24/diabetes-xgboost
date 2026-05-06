# Resource Graphs From Worker Metrics

Source 2-worker metrics file: `C:\Users\Shravani\Downloads\worker_system_metric_stats.json`

These graphs use worker metric samples, not request timing samples. They show resource behavior and routing/selection frequency, but they do not show true request latency.

## Generated Graphs

- `resource_cpu_timeseries_2_worker.svg`: CPU utilization over time for worker 1 and worker 2.
- `resource_memory_timeseries_2_worker.svg`: memory usage over time for worker 1 and worker 2.
- `resource_network_timeseries_2_worker.svg`: receive + send bandwidth over time.
- `resource_worker_selection_2_worker.svg`: number of metric samples selected from each worker.
- `resource_utilization_comparison_existing_1_worker_vs_new_2_worker.svg`: existing 1-worker metrics compared with the new 2-worker metrics.

## 2-Worker Selection Counts

- worker_1: 216 samples (19.0%)
- worker_2: 920 samples (81.0%)

## Summary Table

- existing 1 worker broker: CPU 15.14%, memory 78.17%, recv 0.0114 Mbps, send 0.0114 Mbps.
- existing 1 worker worker_1: CPU 4.37%, memory 12.34%, recv 0.0000 Mbps, send 0.0000 Mbps.
- new 2 worker worker_1: CPU 2.53%, memory 86.59%, recv 0.0935 Mbps, send 0.1556 Mbps.
- new 2 worker worker_2: CPU 3.44%, memory 86.50%, recv 0.1226 Mbps, send 0.1983 Mbps.