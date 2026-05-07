# Matching Our Results To The HealthAIoT Paper

This document explains how to present our implementation results so they match the paper's results and analysis structure.

## Paper Results Structure

The paper evaluates HealthAIoT in two categories:

1. AI model performance
   - Diabetes predictor accuracy
   - Diabetes predictor F1-score
   - Scheduler model accuracy
   - Explainability through SHAP

2. Cloud/QoS performance
   - Latency
   - Total execution time
   - Energy consumption
   - Carbon-free energy usage
   - Cost
   - Resource utilization
   - Worker/broker operation modes

The paper reports that the diabetes predictor reaches 78.30% accuracy and F1-score 0.7719, while the cloud scheduler reaches about 93.6% accuracy. It also evaluates the system across Broker-only, 1-Worker, and 2-Worker modes.

## What We Can Match Directly

| Paper result/analysis item | Our matching artifact | What to say |
|---|---|---|
| HealthAIoT architecture | `README.md`, `scheduler.py`, `worker/app.py` | Our implementation follows the same Broker + Worker architecture. Broker hosts the frontend and scheduler. Workers host the diabetes prediction model. |
| Diabetes risk predictor | `disease_model/best_model.pth`, `disease_model/diabetic_model_train_val_test_log.txt` | The implementation includes the MLP diabetes predictor trained on CDC diabetes health indicators. |
| Scheduler model | `vm_selector_model.pth`, `scheduler_train_test_log.txt` | The scheduler is an MLP model trained on BitBrains cloud workload data to select the better worker. |
| Scheduler accuracy | `results/scheduler_training_curve.svg`, `results/scheduler_training_curve.csv` | Our logged scheduler best test accuracy is 93.69%, which matches the paper's reported scheduler accuracy of about 93.6%. |
| Latency and execution time | `1_node_time_stats.json`, `2_node_time_stats.json`, `results/latency_summary.svg`, `results/latency_distribution.svg` | These show broker-side request timing and can be compared with paper QoS latency/execution-time analysis. |
| 1-worker mode | `1_node_time_stats.json`, `1_node_operation.json` | This is our baseline where one worker handles the request stream. |
| 2-worker mode | `2_node_time_stats.json`, new resource JSON, `results/resource_*_2_worker.svg` | This shows scheduler-based worker selection and resource behavior with two workers. |
| Resource utilization | `results/resource_utilization*.svg`, `results/resource_summary_existing_1_worker_vs_new_2_worker.csv` | We show CPU, memory, and network usage for the workers, matching the paper's resource-efficiency analysis theme. |
| Broker fallback/reliability | `temporal_summary_by_system.csv`, routing graphs | Broker fallback demonstrates fault tolerance when a worker is unavailable. |
| SHAP/explainability | `plot_figures/shap_swarm_plot.png.png` | This supports the paper's XAI discussion by showing feature contribution in diabetes prediction. |

## What We Partially Match

| Paper metric | Our current status | How to present honestly |
|---|---|---|
| Energy consumption | Not directly measured in current logs | We can say this implementation reproduces the scheduler and latency/resource analysis, but not CloudAIBus energy measurement unless we add power/energy instrumentation. |
| Carbon-free energy usage | Not directly measured | We need cloud-region carbon data or CloudAIBus-style metrics to reproduce this. |
| Cost | Not directly measured | We can estimate EC2 cost from instance type and runtime, but that is not currently logged by the app. |
| Full Broker-only mode | Broker fallback records exist, but no clean dedicated Broker-only experiment | We can run a separate experiment with no workers reachable and collect `temporal_stats.json`. |
| New 2-worker latency | Your uploaded `worker_system_metric_stats.json` does not include timing | We can show resource behavior from it, but need `temporal_stats.json` for true latency. |

## Presentation Flow

### Slide 1: Paper Goal

Say:

> The paper proposes HealthAIoT, an AIoT healthcare architecture that combines diabetes risk prediction with cloud resource scheduling. The goal is not only prediction accuracy, but also efficient cloud execution.

### Slide 2: Our Implementation

Show:

- `scheduler.py` as Broker
- `worker/app.py` as Worker
- MLP diabetes predictor
- MLP scheduler
- Web form and simulator

Say:

> We implemented the same Broker-Worker design. The Broker collects worker metrics, uses the scheduler model to choose a worker, sends the patient request to that worker, and records timing/resource statistics.

### Slide 3: AI Model Results

Show:

- Paper diabetes accuracy: 78.30%
- Paper diabetes F1-score: 0.7719
- Paper scheduler accuracy: 93.6%
- Our scheduler accuracy: 93.69%
- `scheduler_training_curve.svg`

Say:

> The scheduler result matches very closely. Our scheduler training log reaches 93.69% test accuracy, consistent with the paper's 93.6% reported value.

### Slide 4: 1-Worker vs 2-Worker Latency

Show:

- `latency_summary.svg`
- `latency_distribution.svg`
- `time_breakdown.svg`

Say:

> The paper evaluates QoS using latency and execution time. Our timing files reproduce the same type of analysis. We compare 1-worker and 2-worker modes using average, median, P95, and max execution time.

Important:

> For the new uploaded 2-worker file, we cannot calculate latency because it only contains worker resource metrics. For latency, we need `temporal_stats.json`.

### Slide 5: Resource Utilization

Show:

- `resource_worker_selection_2_worker.svg`
- `resource_cpu_timeseries_2_worker.svg`
- `resource_memory_timeseries_2_worker.svg`
- `resource_network_timeseries_2_worker.svg`
- `resource_utilization_comparison_existing_1_worker_vs_new_2_worker.svg`

Say:

> The paper analyzes resource-efficient cloud scheduling. Our resource graphs show the selected worker metrics: CPU, memory, and network bandwidth. Worker 2 was selected more often in our new run, and both workers had low CPU utilization but high memory usage.

### Slide 6: Reliability/Fallback

Show:

- `request_routing.svg`
- `temporal_summary_by_system.csv`

Say:

> If the optimal worker is unavailable, the Broker falls back to local prediction. This keeps the healthcare service available even when worker communication fails.

### Slide 7: What We Did Not Fully Reproduce

Say:

> The original paper uses CloudAIBus for energy, carbon-free energy, and cost analysis. Our current implementation reproduces the core software architecture, scheduler accuracy, latency/execution-time analysis, and resource-utilization analysis. To fully match the sustainability part, we would need energy, carbon, and cost telemetry.

## Best Results To Put In A Table

| Category | Paper | Our implementation |
|---|---:|---:|
| Diabetes predictor accuracy | 78.30% | Use paper/repo log value unless retrained |
| Diabetes predictor F1-score | 0.7719 | Use paper/repo log value unless retrained |
| Scheduler accuracy | 93.6% | 93.69% |
| 1-worker avg total execution time | Paper reports QoS timing | 151.91 ms from existing logs |
| 1-worker P95 total execution time | Paper reports QoS timing | 438.47 ms from existing logs |
| 2-worker avg total execution time | Paper reports QoS timing | 309.53 ms from existing logs |
| 2-worker P95 total execution time | Paper reports QoS timing | 253.67 ms from existing logs |
| New 2-worker CPU | Not directly comparable | worker_1 2.53%, worker_2 3.44% |
| New 2-worker memory | Not directly comparable | worker_1 86.59%, worker_2 86.50% |
| New 2-worker selection share | Scheduler behavior | worker_1 19%, worker_2 81% |

## Exact Explanation For Matching The Paper

Use this wording:

> Our implementation matches the paper at the architectural and scheduler-model level. The same two-module design is used: an MLP diabetes predictor and an MLP cloud scheduler. The scheduler accuracy from our logs is 93.69%, effectively matching the paper's reported 93.6%. For QoS analysis, we reproduce the paper's latency and execution-time style of evaluation using 1-worker and 2-worker timing logs. We also generate CPU, memory, and network graphs to support the resource-utilization analysis. The only parts not fully reproduced are energy consumption, carbon-free energy usage, and cost, because those require CloudAIBus or cloud provider telemetry that is not currently logged by this implementation.

## What To Collect Next For A Stronger Match

1. Run Broker-only mode and save `temporal_stats.json`.
2. Run 1-worker mode and save both:
   - `temporal_stats.json`
   - `worker_system_metric_stats.json`
3. Run 2-worker mode and save both:
   - `temporal_stats.json`
   - `worker_system_metric_stats.json`
4. Record EC2 instance type and runtime to estimate cost.
5. Record region and use cloud carbon-intensity data to estimate carbon-free energy.
6. Use a power model or CloudAIBus-like telemetry for energy consumption.

