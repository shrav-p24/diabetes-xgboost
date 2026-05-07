import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(__file__).resolve().parent
PLOT_FIGURES = ROOT / "plot_figures"
TEMPORAL_FILE = ROOT / "temporal_stats.json"

COLORS = {
    "worker_1": "#2563eb",
    "worker_2": "#16a34a",
    "broker": "#f97316",
}
FALLBACK_COLORS = ["#9333ea", "#dc2626", "#0891b2", "#4b5563"]


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


def svg_header(width, height):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        (
            "<style>"
            "text{font-family:Arial,sans-serif;fill:#111827}"
            ".title{font-size:22px;font-weight:700}"
            ".subtitle{font-size:13px;fill:#4b5563}"
            ".axis{font-size:12px;fill:#374151}"
            ".legend{font-size:13px}"
            ".label{font-size:11px;fill:#374151}"
            "</style>"
        ),
    ]


def save_svg(path, parts):
    path.write_text("\n".join(parts + ["</svg>"]), encoding="utf-8")


def system_color(system):
    if system in COLORS:
        return COLORS[system]
    index = sum(ord(char) for char in system) % len(FALLBACK_COLORS)
    return FALLBACK_COLORS[index]


def summarize_temporal(records):
    rows = []
    by_system = defaultdict(list)
    for record in records:
        by_system[record["system"]].append(record)

    for system, system_records in sorted(by_system.items()):
        latencies = [seconds_to_ms(record["latency"]) for record in system_records]
        models = [seconds_to_ms(record["model_execution_time"]) for record in system_records]
        totals = [seconds_to_ms(record["total_execution_time"]) for record in system_records]
        rows.append(
            {
                "system": system,
                "requests": len(system_records),
                "avg_latency_ms": mean(latencies),
                "median_latency_ms": median(latencies),
                "p95_latency_ms": percentile(latencies, 0.95),
                "max_latency_ms": max(latencies),
                "avg_model_ms": mean(models),
                "avg_total_ms": mean(totals),
                "p95_total_ms": percentile(totals, 0.95),
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


def save_temporal_latency_chart(path, records):
    width, height = 980, 560
    left, right, top, bottom = 82, 42, 82, 92
    plot_w, plot_h = width - left - right, height - top - bottom
    values = [seconds_to_ms(record["latency"]) for record in records]
    y_max = max(values) * 1.15 if values else 1
    y_max = max(y_max, 1)
    parts = svg_header(width, height)
    parts.append(f'<text x="{width/2}" y="34" text-anchor="middle" class="title">Temporal Request Latency</text>')
    parts.append(
        f'<text x="{width/2}" y="56" text-anchor="middle" class="subtitle">'
        f'Source: {escape(TEMPORAL_FILE.name)}; {len(records)} requests from {escape(records[0]["timestamp"])} to {escape(records[-1]["timestamp"])}</text>'
    )
    parts.append(f'<text x="24" y="{top + plot_h/2}" transform="rotate(-90 24 {top + plot_h/2})" class="axis">latency (ms)</text>')

    for tick in range(6):
        value = y_max * tick / 5
        y = top + plot_h - (value / y_max) * plot_h
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" class="axis">{value:.2f}</text>')
    parts.append(f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="#374151"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="#374151"/>')

    points_by_system = defaultdict(list)
    for index, record in enumerate(records, start=1):
        x = left + ((index - 1) / max(len(records) - 1, 1)) * plot_w
        y = top + plot_h - (seconds_to_ms(record["latency"]) / y_max) * plot_h
        points_by_system[record["system"]].append((x, y))

    for system, points in sorted(points_by_system.items()):
        point_string = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        color = system_color(system)
        parts.append(f'<polyline points="{point_string}" fill="none" stroke="{color}" stroke-width="2.2" opacity="0.85"/>')
        for x, y in points:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{color}" opacity="0.78"/>')

    for tick in range(6):
        request_index = 1 + round((len(records) - 1) * tick / 5)
        x = left + ((request_index - 1) / max(len(records) - 1, 1)) * plot_w
        parts.append(f'<text x="{x:.1f}" y="{height-52}" text-anchor="middle" class="axis">{request_index}</text>')
    parts.append(f'<text x="{left + plot_w/2}" y="{height-24}" text-anchor="middle" class="axis">request sequence</text>')

    for idx, system in enumerate(sorted(points_by_system)):
        x = left + idx * 150
        y = height - 18
        parts.append(f'<circle cx="{x}" cy="{y-5}" r="6" fill="{system_color(system)}"/>')
        parts.append(f'<text x="{x+14}" y="{y}" class="legend">{escape(system)}</text>')
    save_svg(path, parts)


def markdown_graph(path, title, note=None):
    image_path = f"<{path}>" if any(char in path for char in " ()") else path
    lines = [f"### {title}", "", f"![{title}]({image_path})"]
    if note:
        lines.extend(["", note])
    return lines


def write_report(path, records, summary_rows):
    counts = Counter(record["system"] for record in records)
    all_latencies = [seconds_to_ms(record["latency"]) for record in records]
    all_totals = [seconds_to_ms(record["total_execution_time"]) for record in records]
    all_models = [seconds_to_ms(record["model_execution_time"]) for record in records]
    lines = [
        "# HealthAIoT Progress Report",
        "",
        "This report gathers the model, scheduler, latency, and resource graphs generated in this workspace.",
        "",
        "## Current Temporal Run",
        "",
        f"- Source file: `../temporal_stats.json`",
        f"- Time window: `{records[0]['timestamp']}` to `{records[-1]['timestamp']}`",
        f"- Requests logged: {len(records)}",
        f"- Routing: {', '.join(f'{system}={count}' for system, count in sorted(counts.items()))}",
        f"- Average latency: {mean(all_latencies):.3f} ms; median {median(all_latencies):.3f} ms; p95 {percentile(all_latencies, 0.95):.3f} ms; max {max(all_latencies):.3f} ms",
        f"- Average model execution: {mean(all_models):.3f} ms",
        f"- Average total execution time: {mean(all_totals):.2f} ms; p95 {percentile(all_totals, 0.95):.2f} ms",
        "",
        "### Temporal Summary by System",
        "",
        "| System | Requests | Avg latency (ms) | Median latency (ms) | P95 latency (ms) | Max latency (ms) | Avg total (ms) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['system']} | {row['requests']} | {row['avg_latency_ms']:.3f} | "
            f"{row['median_latency_ms']:.3f} | {row['p95_latency_ms']:.3f} | "
            f"{row['max_latency_ms']:.3f} | {row['avg_total_ms']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Temporal Latency Graph",
            "",
            "![Temporal Request Latency](current_temporal_latency.svg)",
            "",
            "## Disease Model Graphs",
            "",
        ]
    )
    lines.extend(markdown_graph("../plot_figures/confusion_matrix_with_percentages.png", "Confusion Matrix With Percentages"))
    lines.extend([""])
    lines.extend(markdown_graph("../plot_figures/shap_swarm_plot.png.png", "SHAP Swarm Plot"))
    lines.extend([""])
    lines.extend(markdown_graph("../plot_figures/Dataset Correlation_Matrix.png", "Dataset Correlation Matrix"))
    lines.extend([""])
    lines.extend(markdown_graph("../plot_figures/SMOTE Preprocessing Comparison.png", "SMOTE Preprocessing Comparison"))

    lines.extend(
        [
            "",
            "## Scheduler and Latency Graphs",
            "",
        ]
    )
    for filename, title in [
        ("scheduler_training_curve.svg", "Cloud Scheduler Training Progress"),
        ("latency_summary.svg", "Latency Summary"),
        ("latency_distribution.svg", "Latency Distribution"),
        ("time_breakdown.svg", "End-to-End Time Breakdown"),
        ("request_routing.svg", "Request Routing"),
    ]:
        if (RESULTS / filename).exists():
            lines.extend(markdown_graph(filename, title))
            lines.append("")

    lines.extend(["## Resource Graphs", ""])
    for filename, title in [
        ("resource_utilization.svg", "Average Resource Utilization"),
        ("resource_cpu_timeseries_2_worker.svg", "2-Worker CPU Time Series"),
        ("resource_memory_timeseries_2_worker.svg", "2-Worker Memory Time Series"),
        ("resource_network_timeseries_2_worker.svg", "2-Worker Network Time Series"),
        ("resource_worker_selection_2_worker.svg", "2-Worker Selection Counts"),
        ("resource_utilization_comparison_existing_1_worker_vs_new_2_worker.svg", "Resource Utilization Comparison"),
        ("resource_network_comparison_existing_1_worker_vs_new_2_worker.svg", "Network Comparison"),
    ]:
        if (RESULTS / filename).exists():
            lines.extend(markdown_graph(filename, title))
            lines.append("")

    lines.extend(
        [
            "## Generated Files",
            "",
            "- `current_temporal_latency.svg`: latency plot generated from `../temporal_stats.json`.",
            "- `current_temporal_summary.csv`: per-system temporal summary for the current run.",
            "- `PROGRESS_REPORT.md`: this progress report.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    records = load_json(TEMPORAL_FILE)
    if not records:
        raise ValueError(f"No records found in {TEMPORAL_FILE}")
    summary_rows = summarize_temporal(records)
    write_csv(RESULTS / "current_temporal_summary.csv", summary_rows)
    save_temporal_latency_chart(RESULTS / "current_temporal_latency.svg", records)
    write_report(RESULTS / "PROGRESS_REPORT.md", records, summary_rows)
    print(f"Generated {RESULTS / 'PROGRESS_REPORT.md'}")
    print(f"Generated {RESULTS / 'current_temporal_latency.svg'}")


if __name__ == "__main__":
    main()
