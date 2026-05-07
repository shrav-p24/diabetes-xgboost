# HealthAIoT Progress Report

This report gathers the model, scheduler, latency, and resource graphs generated in this workspace.

## Current Temporal Run

- Source file: `../temporal_stats.json`
- Time window: `2026-05-06 22:55:27` to `2026-05-06 22:55:41`
- Requests logged: 140
- Routing: worker_1=140
- Average latency: 0.588 ms; median 0.084 ms; p95 3.564 ms; max 9.892 ms
- Average model execution: 1.306 ms
- Average total execution time: 1946.46 ms; p95 2296.29 ms

### Temporal Summary by System

| System | Requests | Avg latency (ms) | Median latency (ms) | P95 latency (ms) | Max latency (ms) | Avg total (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| worker_1 | 140 | 0.588 | 0.084 | 3.564 | 9.892 | 1946.46 |

## Temporal Latency Graph

![Temporal Request Latency](current_temporal_latency.svg)

## Disease Model Graphs

### Confusion Matrix With Percentages

![Confusion Matrix With Percentages](../plot_figures/confusion_matrix_with_percentages.png)

### SHAP Swarm Plot

![SHAP Swarm Plot](../plot_figures/shap_swarm_plot.png.png)

### Dataset Correlation Matrix

![Dataset Correlation Matrix](<../plot_figures/Dataset Correlation_Matrix.png>)

### SMOTE Preprocessing Comparison

![SMOTE Preprocessing Comparison](<../plot_figures/SMOTE Preprocessing Comparison.png>)

## Scheduler and Latency Graphs

### Cloud Scheduler Training Progress

![Cloud Scheduler Training Progress](scheduler_training_curve.svg)

### Latency Summary

![Latency Summary](latency_summary.svg)

### Latency Distribution

![Latency Distribution](latency_distribution.svg)

### End-to-End Time Breakdown

![End-to-End Time Breakdown](time_breakdown.svg)

### Request Routing

![Request Routing](request_routing.svg)

## Resource Graphs

### Average Resource Utilization

![Average Resource Utilization](resource_utilization.svg)

### 2-Worker CPU Time Series

![2-Worker CPU Time Series](resource_cpu_timeseries_2_worker.svg)

### 2-Worker Memory Time Series

![2-Worker Memory Time Series](resource_memory_timeseries_2_worker.svg)

### 2-Worker Network Time Series

![2-Worker Network Time Series](resource_network_timeseries_2_worker.svg)

### 2-Worker Selection Counts

![2-Worker Selection Counts](resource_worker_selection_2_worker.svg)

### Resource Utilization Comparison

![Resource Utilization Comparison](resource_utilization_comparison_existing_1_worker_vs_new_2_worker.svg)

### Network Comparison

![Network Comparison](resource_network_comparison_existing_1_worker_vs_new_2_worker.svg)

## Generated Files

- `current_temporal_latency.svg`: latency plot generated from `../temporal_stats.json`.
- `current_temporal_summary.csv`: per-system temporal summary for the current run.
- `PROGRESS_REPORT.md`: this progress report.
