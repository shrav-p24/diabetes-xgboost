import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(__file__).resolve().parent


TIME_FILES = {
    "1 worker": ROOT / "1_node_time_stats.json",
    "2 workers": ROOT / "2_node_time_stats.json",
}

OPERATION_FILES = {
    "1 worker": ROOT / "1_node_operation.json",
    "2 workers": ROOT / "2_node_operation.json",
}


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def percentile(values, pct):
    if not values:
        return 0
    sorted_values = sorted(values)
    rank = (len(sorted_values) - 1) * pct
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = rank - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def seconds_to_ms(seconds):
    return seconds * 1000


def summarize_temporal(records):
    by_system = defaultdict(list)
    for record in records:
        by_system[record["system"]].append(record)

    rows = []
    for system, system_records in sorted(by_system.items()):
        total_ms = [seconds_to_ms(r["total_execution_time"]) for r in system_records]
        model_ms = [seconds_to_ms(r["model_execution_time"]) for r in system_records]
        latency_ms = [seconds_to_ms(r["latency"]) for r in system_records]
        overhead_ms = [
            max(0, seconds_to_ms(r["total_execution_time"] - r["model_execution_time"] - r["latency"]))
            for r in system_records
        ]
        rows.append(
            {
                "system": system,
                "requests": len(system_records),
                "avg_total_ms": mean(total_ms),
                "median_total_ms": median(total_ms),
                "p95_total_ms": percentile(total_ms, 0.95),
                "avg_model_ms": mean(model_ms),
                "avg_latency_ms": mean(latency_ms),
                "avg_scheduler_network_overhead_ms": mean(overhead_ms),
            }
        )
    return rows


def summarize_operations(records):
    by_system = defaultdict(list)
    for record in records:
        by_system[record["system"]].append(record["stats"])

    rows = []
    for system, stats in sorted(by_system.items()):
        rows.append(
            {
                "system": system,
                "samples": len(stats),
                "avg_cpu_percent": mean(s["cpu_utilization"] for s in stats),
                "avg_memory_percent": mean(s["memory_usage_percent"] for s in stats),
                "avg_recv_mbps": mean(s["network_bandwidth"]["recv_bandwidth_mbps"] for s in stats),
                "avg_send_mbps": mean(s["network_bandwidth"]["send_bandwidth_mbps"] for s in stats),
            }
        )
    return rows


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_scheduler_log(path):
    pattern = re.compile(
        r"Epoch (?P<epoch>\d+)/(?P<epochs>\d+), Train Loss: (?P<loss>[\d.]+), "
        r"Train Acc: (?P<train>[\d.]+), Test Acc: (?P<test>[\d.]+)"
    )
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.search(line)
        if match:
            rows.append(
                {
                    "epoch": int(match.group("epoch")),
                    "train_loss": float(match.group("loss")),
                    "train_accuracy": float(match.group("train")),
                    "test_accuracy": float(match.group("test")),
                }
            )
    return rows


COLORS = ["#2563eb", "#f97316", "#16a34a", "#9333ea", "#dc2626", "#0891b2"]


def svg_header(width, height):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#111827}.title{font-size:22px;font-weight:700}.axis{font-size:12px}.legend{font-size:13px}.label{font-size:12px}</style>',
    ]


def save_svg(path, parts):
    path.write_text("\n".join(parts + ["</svg>"]), encoding="utf-8")


def save_bar_chart(path, title, labels, series, ylabel):
    width, height = 920, 540
    left, right, top, bottom = 80, 30, 70, 95
    plot_w, plot_h = width - left - right, height - top - bottom
    all_values = [value for values in series.values() for value in values]
    y_max = max(all_values) * 1.18 if all_values else 1
    parts = svg_header(width, height)
    parts.append(f'<text x="{width/2}" y="34" text-anchor="middle" class="title">{escape(title)}</text>')
    parts.append(f'<text x="22" y="{top + plot_h/2}" transform="rotate(-90 22 {top + plot_h/2})" class="axis">{escape(ylabel)}</text>')
    for tick in range(6):
        value = y_max * tick / 5
        y = top + plot_h - (value / y_max) * plot_h
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" class="axis">{value:.1f}</text>')
    parts.append(f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="#374151"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="#374151"/>')

    group_w = plot_w / len(labels)
    bar_w = group_w / (len(series) + 1.3)
    for series_idx, (name, values) in enumerate(series.items()):
        for label_idx, value in enumerate(values):
            x = left + label_idx * group_w + (series_idx + 0.35) * bar_w
            bar_h = (value / y_max) * plot_h
            y = top + plot_h - bar_h
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w*0.86:.1f}" height="{bar_h:.1f}" fill="{COLORS[series_idx % len(COLORS)]}"/>')
            parts.append(f'<text x="{x + bar_w*0.43:.1f}" y="{y-5:.1f}" text-anchor="middle" class="label">{value:.1f}</text>')
    for idx, label in enumerate(labels):
        x = left + idx * group_w + group_w / 2
        parts.append(f'<text x="{x:.1f}" y="{height-52}" text-anchor="middle" class="axis">{escape(label)}</text>')
    for idx, name in enumerate(series):
        x = left + idx * 175
        parts.append(f'<rect x="{x}" y="{height-25}" width="16" height="16" fill="{COLORS[idx % len(COLORS)]}"/>')
        parts.append(f'<text x="{x+23}" y="{height-12}" class="legend">{escape(name)}</text>')
    save_svg(path, parts)


def save_boxplot(path, records_by_config):
    rows = []
    for label, records in records_by_config.items():
        values = [seconds_to_ms(r["total_execution_time"]) for r in records]
        rows.append(
            {
                "scenario": label,
                "min": min(values),
                "median": percentile(values, 0.50),
                "p95": percentile(values, 0.95),
                "max": max(values),
            }
        )
    save_bar_chart(
        path,
        "End-to-End Execution Time Distribution",
        [row["scenario"] for row in rows],
        {
            "Median": [row["median"] for row in rows],
            "P95": [row["p95"] for row in rows],
            "Max": [row["max"] for row in rows],
        },
        "milliseconds",
    )


def save_routing_chart(path, records_by_config):
    systems = sorted({r["system"] for records in records_by_config.values() for r in records})
    labels = list(records_by_config.keys())
    save_bar_chart(
        path,
        "Request Routing by System",
        labels,
        {system: [Counter(r["system"] for r in records_by_config[label])[system] for label in labels] for system in systems},
        "request count",
    )


def save_resource_chart(path, operation_summaries):
    labels = [row["scenario"] + " " + row["system"] for row in operation_summaries]
    save_bar_chart(
        path,
        "Average System Utilization During Scheduler Runs",
        labels,
        {
            "CPU": [row["avg_cpu_percent"] for row in operation_summaries],
            "Memory": [row["avg_memory_percent"] for row in operation_summaries],
        },
        "percent",
    )


def save_training_curve(path, scheduler_rows):
    width, height = 920, 540
    left, right, top, bottom = 75, 35, 70, 80
    plot_w, plot_h = width - left - right, height - top - bottom
    epochs = [row["epoch"] for row in scheduler_rows]
    parts = svg_header(width, height)
    parts.append(f'<text x="{width/2}" y="34" text-anchor="middle" class="title">Cloud Scheduler Training Progress</text>')
    for tick in range(6):
        value = tick / 5
        y = top + plot_h - value * plot_h
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" class="axis">{value:.1f}</text>')
    parts.append(f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="#374151"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="#374151"/>')

    def points(values):
        max_epoch = max(epochs)
        return " ".join(
            f'{left + ((epoch - 1) / (max_epoch - 1)) * plot_w:.1f},{top + plot_h - value * plot_h:.1f}'
            for epoch, value in zip(epochs, values)
        )

    parts.append(f'<polyline points="{points([row["train_accuracy"] for row in scheduler_rows])}" fill="none" stroke="{COLORS[0]}" stroke-width="3"/>')
    parts.append(f'<polyline points="{points([row["test_accuracy"] for row in scheduler_rows])}" fill="none" stroke="{COLORS[1]}" stroke-width="3"/>')
    parts.append(f'<text x="{left + plot_w/2}" y="{height-34}" text-anchor="middle" class="axis">epoch</text>')
    for idx, name in enumerate(["Train accuracy", "Test accuracy"]):
        x = left + idx * 180
        parts.append(f'<rect x="{x}" y="{height-24}" width="16" height="16" fill="{COLORS[idx]}"/>')
        parts.append(f'<text x="{x+23}" y="{height-11}" class="legend">{name}</text>')
    save_svg(path, parts)


def save_breakdown_chart(path, summary_rows):
    labels = [row["scenario"] for row in summary_rows]
    save_bar_chart(
        path,
        "Average End-to-End Time Breakdown",
        labels,
        {
            "Input handling latency": [row["avg_latency_ms"] for row in summary_rows],
            "Model inference": [row["avg_model_ms"] for row in summary_rows],
            "Scheduler + network overhead": [row["avg_scheduler_network_overhead_ms"] for row in summary_rows],
        },
        "milliseconds",
    )


def write_markdown_summary(path, scenario_summaries, scheduler_rows):
    best_scheduler = max(scheduler_rows, key=lambda row: row["test_accuracy"])
    lines = [
        "# HealthAIoT Results Summary",
        "",
        "This folder consolidates scheduler, latency, and system-utilization outputs generated from the repository logs.",
        "",
        "## Cloud Scheduler Model",
        "",
        f"- Best logged scheduler test accuracy: {best_scheduler['test_accuracy'] * 100:.2f}% at epoch {best_scheduler['epoch']}.",
        "- Scheduler inputs: worker CPU, memory, receive bandwidth, and send bandwidth for two workers.",
        "- Scheduler output: selected worker index.",
        "",
        "## Latency Results",
        "",
    ]
    for row in scenario_summaries:
        lines.append(
            f"- {row['scenario']}: {row['requests']} requests, "
            f"average total {row['avg_total_ms']:.2f} ms, "
            f"p95 total {row['p95_total_ms']:.2f} ms, "
            f"average model inference {row['avg_model_ms']:.2f} ms."
        )
    lines.extend(
        [
            "",
            "## Graph Files",
            "",
            "- `latency_summary.svg`: average and p95 total execution time by scenario.",
            "- `latency_distribution.svg`: spread of end-to-end execution time.",
            "- `time_breakdown.svg`: average input, inference, and scheduler/network overhead.",
            "- `request_routing.svg`: how requests were routed across worker and broker systems.",
            "- `resource_utilization.svg`: average CPU and memory utilization by scenario/system.",
            "- `scheduler_training_curve.svg`: scheduler train/test accuracy.",
            "",
            "## Presentation Results You Can Show",
            "",
            "- End-to-end latency: average, median, p95, and outlier behavior.",
            "- Model execution time: diabetes predictor inference time on workers vs broker fallback.",
            "- Scheduler/network overhead: total time minus model inference and input handling.",
            "- Routing decisions: how often the scheduler selects worker 1, worker 2, or broker fallback.",
            "- Worker utilization: CPU, memory, receive bandwidth, and send bandwidth at selected workers.",
            "- 1-worker vs 2-worker comparison: latency distribution, average total time, and routing/fallback behavior.",
            "- Scheduler model quality: training/test accuracy curve and best test accuracy.",
            "- Reliability: broker fallback count when worker requests fail.",
            "- Scalability: throughput from `simulation.py` using `NUM_REQUESTS` and `CONCURRENT_THREADS`.",
            "- Sustainability-facing metrics, if collected in future runs: energy, carbon-free energy percentage, and cost.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    records_by_config = {label: load_json(path) for label, path in TIME_FILES.items()}
    temporal_rows = []
    scenario_rows = []
    for scenario, records in records_by_config.items():
        rows = summarize_temporal(records)
        for row in rows:
            row["scenario"] = scenario
            temporal_rows.append(row)
        totals = [seconds_to_ms(r["total_execution_time"]) for r in records]
        models = [seconds_to_ms(r["model_execution_time"]) for r in records]
        latencies = [seconds_to_ms(r["latency"]) for r in records]
        overheads = [
            max(0, seconds_to_ms(r["total_execution_time"] - r["model_execution_time"] - r["latency"]))
            for r in records
        ]
        scenario_rows.append(
            {
                "scenario": scenario,
                "requests": len(records),
                "avg_total_ms": mean(totals),
                "median_total_ms": median(totals),
                "p95_total_ms": percentile(totals, 0.95),
                "avg_model_ms": mean(models),
                "avg_latency_ms": mean(latencies),
                "avg_scheduler_network_overhead_ms": mean(overheads),
            }
        )

    operation_rows = []
    for scenario, path in OPERATION_FILES.items():
        for row in summarize_operations(load_json(path)):
            row["scenario"] = scenario
            operation_rows.append(row)

    scheduler_rows = parse_scheduler_log(ROOT / "scheduler_train_test_log.txt")

    write_csv(RESULTS / "temporal_summary_by_system.csv", temporal_rows)
    write_csv(RESULTS / "temporal_summary_by_scenario.csv", scenario_rows)
    write_csv(RESULTS / "operation_summary.csv", operation_rows)
    write_csv(RESULTS / "scheduler_training_curve.csv", scheduler_rows)

    save_bar_chart(
        RESULTS / "latency_summary.svg",
        "Cloud Scheduler Latency Summary",
        [row["scenario"] for row in scenario_rows],
        {
            "Average total": [row["avg_total_ms"] for row in scenario_rows],
            "P95 total": [row["p95_total_ms"] for row in scenario_rows],
        },
        "milliseconds",
    )
    save_boxplot(RESULTS / "latency_distribution.svg", records_by_config)
    save_routing_chart(RESULTS / "request_routing.svg", records_by_config)
    save_resource_chart(RESULTS / "resource_utilization.svg", operation_rows)
    save_training_curve(RESULTS / "scheduler_training_curve.svg", scheduler_rows)
    save_breakdown_chart(RESULTS / "time_breakdown.svg", scenario_rows)
    write_markdown_summary(RESULTS / "README.md", scenario_rows, scheduler_rows)


if __name__ == "__main__":
    main()
