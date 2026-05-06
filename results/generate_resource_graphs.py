import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(__file__).resolve().parent
DEFAULT_TWO_WORKER_METRICS = Path(r"C:\Users\Shravani\Downloads\worker_system_metric_stats.json")
ONE_WORKER_METRICS = ROOT / "1_node_operation.json"

COLORS = ["#2563eb", "#f97316", "#16a34a", "#9333ea", "#dc2626", "#0891b2"]


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_time(value):
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def svg_header(width, height):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#111827}.title{font-size:22px;font-weight:700}.axis{font-size:12px}.legend{font-size:13px}.label{font-size:12px}</style>',
    ]


def save_svg(path, parts):
    path.write_text("\n".join(parts + ["</svg>"]), encoding="utf-8")


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summarize(records, scenario):
    grouped = defaultdict(list)
    for record in records:
        grouped[record["system"]].append(record["stats"])

    rows = []
    for system, stats in sorted(grouped.items()):
        rows.append(
            {
                "scenario": scenario,
                "system": system,
                "samples": len(stats),
                "avg_cpu_percent": mean(s["cpu_utilization"] for s in stats),
                "avg_memory_percent": mean(s["memory_usage_percent"] for s in stats),
                "avg_recv_mbps": mean(s["network_bandwidth"]["recv_bandwidth_mbps"] for s in stats),
                "avg_send_mbps": mean(s["network_bandwidth"]["send_bandwidth_mbps"] for s in stats),
            }
        )
    return rows


def save_bar_chart(path, title, labels, series, ylabel):
    width, height = 980, 560
    left, right, top, bottom = 86, 35, 70, 115
    plot_w, plot_h = width - left - right, height - top - bottom
    all_values = [value for values in series.values() for value in values]
    y_max = max(all_values) * 1.18 if all_values else 1
    if y_max == 0:
        y_max = 1

    parts = svg_header(width, height)
    parts.append(f'<text x="{width/2}" y="35" text-anchor="middle" class="title">{escape(title)}</text>')
    parts.append(f'<text x="24" y="{top + plot_h/2}" transform="rotate(-90 24 {top + plot_h/2})" class="axis">{escape(ylabel)}</text>')
    for tick in range(6):
        value = y_max * tick / 5
        y = top + plot_h - (value / y_max) * plot_h
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" class="axis">{value:.1f}</text>')
    parts.append(f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="#374151"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="#374151"/>')

    group_w = plot_w / max(len(labels), 1)
    bar_w = group_w / (len(series) + 1.3)
    for series_idx, (name, values) in enumerate(series.items()):
        for label_idx, value in enumerate(values):
            x = left + label_idx * group_w + (series_idx + 0.35) * bar_w
            bar_h = (value / y_max) * plot_h
            y = top + plot_h - bar_h
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w*0.86:.1f}" height="{bar_h:.1f}" fill="{COLORS[series_idx % len(COLORS)]}"/>')
            parts.append(f'<text x="{x + bar_w*0.43:.1f}" y="{max(y-5, top+12):.1f}" text-anchor="middle" class="label">{value:.1f}</text>')

    for idx, label in enumerate(labels):
        x = left + idx * group_w + group_w / 2
        parts.append(f'<text x="{x:.1f}" y="{height-70}" text-anchor="middle" class="axis">{escape(label)}</text>')

    for idx, name in enumerate(series):
        x = left + idx * 190
        parts.append(f'<rect x="{x}" y="{height-26}" width="16" height="16" fill="{COLORS[idx % len(COLORS)]}"/>')
        parts.append(f'<text x="{x+23}" y="{height-13}" class="legend">{escape(name)}</text>')
    save_svg(path, parts)


def save_time_series(path, title, records, metric_getter, ylabel):
    by_system = defaultdict(list)
    for record in records:
        stats = record["stats"]
        by_system[record["system"]].append((parse_time(stats["timestamp"]), metric_getter(stats)))

    all_times = [time for points in by_system.values() for time, _ in points]
    all_values = [value for points in by_system.values() for _, value in points]
    start, end = min(all_times), max(all_times)
    duration = max((end - start).total_seconds(), 1)
    y_max = max(all_values) * 1.18 if all_values else 1
    if y_max == 0:
        y_max = 1

    width, height = 980, 560
    left, right, top, bottom = 85, 35, 70, 85
    plot_w, plot_h = width - left - right, height - top - bottom
    parts = svg_header(width, height)
    parts.append(f'<text x="{width/2}" y="35" text-anchor="middle" class="title">{escape(title)}</text>')
    parts.append(f'<text x="24" y="{top + plot_h/2}" transform="rotate(-90 24 {top + plot_h/2})" class="axis">{escape(ylabel)}</text>')

    for tick in range(6):
        value = y_max * tick / 5
        y = top + plot_h - (value / y_max) * plot_h
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" class="axis">{value:.1f}</text>')
    parts.append(f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="#374151"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="#374151"/>')

    for idx, (system, points) in enumerate(sorted(by_system.items())):
        points = sorted(points)
        coords = []
        for time, value in points:
            x = left + ((time - start).total_seconds() / duration) * plot_w
            y = top + plot_h - (value / y_max) * plot_h
            coords.append(f"{x:.1f},{y:.1f}")
        parts.append(f'<polyline points="{" ".join(coords)}" fill="none" stroke="{COLORS[idx % len(COLORS)]}" stroke-width="2.5"/>')
        legend_x = left + idx * 150
        parts.append(f'<rect x="{legend_x}" y="{height-26}" width="16" height="16" fill="{COLORS[idx % len(COLORS)]}"/>')
        parts.append(f'<text x="{legend_x+23}" y="{height-13}" class="legend">{escape(system)}</text>')

    parts.append(f'<text x="{left}" y="{height-48}" class="axis">{start.strftime("%H:%M:%S")}</text>')
    parts.append(f'<text x="{left+plot_w}" y="{height-48}" text-anchor="end" class="axis">{end.strftime("%H:%M:%S")}</text>')
    save_svg(path, parts)


def save_readme(path, two_worker_path, rows, two_worker_records):
    counts = Counter(record["system"] for record in two_worker_records)
    total = sum(counts.values())
    lines = [
        "# Resource Graphs From Worker Metrics",
        "",
        f"Source 2-worker metrics file: `{two_worker_path}`",
        "",
        "These graphs use worker metric samples, not request timing samples. They show resource behavior and routing/selection frequency, but they do not show true request latency.",
        "",
        "## Generated Graphs",
        "",
        "- `resource_cpu_timeseries_2_worker.svg`: CPU utilization over time for worker 1 and worker 2.",
        "- `resource_memory_timeseries_2_worker.svg`: memory usage over time for worker 1 and worker 2.",
        "- `resource_network_timeseries_2_worker.svg`: receive + send bandwidth over time.",
        "- `resource_worker_selection_2_worker.svg`: number of metric samples selected from each worker.",
        "- `resource_utilization_comparison_existing_1_worker_vs_new_2_worker.svg`: existing 1-worker metrics compared with the new 2-worker metrics.",
        "",
        "## 2-Worker Selection Counts",
        "",
    ]
    for system, count in sorted(counts.items()):
        percentage = count / total * 100 if total else 0
        lines.append(f"- {system}: {count} samples ({percentage:.1f}%)")
    lines.extend(["", "## Summary Table", ""])
    for row in rows:
        lines.append(
            f"- {row['scenario']} {row['system']}: CPU {row['avg_cpu_percent']:.2f}%, "
            f"memory {row['avg_memory_percent']:.2f}%, recv {row['avg_recv_mbps']:.4f} Mbps, "
            f"send {row['avg_send_mbps']:.4f} Mbps."
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    two_worker_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TWO_WORKER_METRICS
    one_worker_records = load_json(ONE_WORKER_METRICS)
    two_worker_records = load_json(two_worker_path)

    rows = summarize(one_worker_records, "existing 1 worker") + summarize(two_worker_records, "new 2 worker")
    write_csv(RESULTS / "resource_summary_existing_1_worker_vs_new_2_worker.csv", rows)

    two_worker_labels = [row["system"] for row in rows if row["scenario"] == "new 2 worker"]
    two_worker_rows = [row for row in rows if row["scenario"] == "new 2 worker"]
    save_bar_chart(
        RESULTS / "resource_worker_selection_2_worker.svg",
        "2-Worker Metric Sample Counts",
        sorted(Counter(record["system"] for record in two_worker_records)),
        {"Samples": [Counter(record["system"] for record in two_worker_records)[system] for system in sorted(Counter(record["system"] for record in two_worker_records))]},
        "sample count",
    )

    save_bar_chart(
        RESULTS / "resource_utilization_comparison_existing_1_worker_vs_new_2_worker.svg",
        "Resource Utilization: Existing 1 Worker vs New 2 Worker",
        [f"{row['scenario']} {row['system']}" for row in rows],
        {
            "CPU": [row["avg_cpu_percent"] for row in rows],
            "Memory": [row["avg_memory_percent"] for row in rows],
        },
        "percent",
    )

    save_bar_chart(
        RESULTS / "resource_network_comparison_existing_1_worker_vs_new_2_worker.svg",
        "Network Utilization: Existing 1 Worker vs New 2 Worker",
        [f"{row['scenario']} {row['system']}" for row in rows],
        {
            "Receive": [row["avg_recv_mbps"] for row in rows],
            "Send": [row["avg_send_mbps"] for row in rows],
        },
        "Mbps",
    )

    save_time_series(
        RESULTS / "resource_cpu_timeseries_2_worker.svg",
        "2-Worker CPU Utilization Over Time",
        two_worker_records,
        lambda stats: stats["cpu_utilization"],
        "CPU percent",
    )
    save_time_series(
        RESULTS / "resource_memory_timeseries_2_worker.svg",
        "2-Worker Memory Usage Over Time",
        two_worker_records,
        lambda stats: stats["memory_usage_percent"],
        "memory percent",
    )
    save_time_series(
        RESULTS / "resource_network_timeseries_2_worker.svg",
        "2-Worker Network Bandwidth Over Time",
        two_worker_records,
        lambda stats: stats["network_bandwidth"]["recv_bandwidth_mbps"] + stats["network_bandwidth"]["send_bandwidth_mbps"],
        "receive + send Mbps",
    )

    save_readme(RESULTS / "RESOURCE_GRAPHS.md", two_worker_path, rows, two_worker_records)
    print(f"Generated resource graphs from {two_worker_path}")


if __name__ == "__main__":
    main()
