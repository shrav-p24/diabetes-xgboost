# HealthAIoT Results Summary

This folder consolidates scheduler, latency, and system-utilization outputs generated from the repository logs.

## Cloud Scheduler Model

- Best logged scheduler test accuracy: 93.69% at epoch 37.
- Scheduler inputs: worker CPU, memory, receive bandwidth, and send bandwidth for two workers.
- Scheduler output: selected worker index.

## Latency Results

- 1 worker: 30 requests, average total 151.91 ms, p95 total 438.47 ms, average model inference 13.13 ms.
- 2 workers: 23 requests, average total 309.53 ms, p95 total 253.67 ms, average model inference 12.12 ms.

## Graph Files

- `latency_summary.svg`: average and p95 total execution time by scenario.
- `latency_distribution.svg`: spread of end-to-end execution time.
- `time_breakdown.svg`: average input, inference, and scheduler/network overhead.
- `request_routing.svg`: how requests were routed across worker and broker systems.
- `resource_utilization.svg`: average CPU and memory utilization by scenario/system.
- `scheduler_training_curve.svg`: scheduler train/test accuracy.

## Presentation Results You Can Show

- End-to-end latency: average, median, p95, and outlier behavior.
- Model execution time: diabetes predictor inference time on workers vs broker fallback.
- Scheduler/network overhead: total time minus model inference and input handling.
- Routing decisions: how often the scheduler selects worker 1, worker 2, or broker fallback.
- Worker utilization: CPU, memory, receive bandwidth, and send bandwidth at selected workers.
- 1-worker vs 2-worker comparison: latency distribution, average total time, and routing/fallback behavior.
- Scheduler model quality: training/test accuracy curve and best test accuracy.
- Reliability: broker fallback count when worker requests fail.
- Scalability: throughput from `simulation.py` using `NUM_REQUESTS` and `CONCURRENT_THREADS`.
- Sustainability-facing metrics, if collected in future runs: energy, carbon-free energy percentage, and cost.
