#!/usr/bin/env python3
import argparse
import json
import re
import socket
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import psutil


APP_VERSION = "0.1.0"
# ----------------------------
# CLI wiring
# ----------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="opsbox for health and logs")
    parser.add_argument("--version", action="version", version=f"opsbox {APP_VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # health
    health = subparsers.add_parser("health", help="Check server health")

    health.add_argument("--cpu", action="store_true", help="Show CPU usage")
    health.add_argument("--ram", action="store_true", help="Show RAM usage")
    health.add_argument("--disk", action="store_true", help="Show disk usage")
    health.add_argument("--path", default=".", help="Path to check disk usage for (default: current directory)")

    health.add_argument("--warn-cpu", type=float, default=70.0, help="CPU WARN threshold (percent)")
    health.add_argument("--crit-cpu", type=float, default=90.0, help="CPU CRIT threshold (percent)")
    health.add_argument("--warn-ram", type=float, default=75.0, help="RAM WARN threshold (percent)")
    health.add_argument("--crit-ram", type=float, default=90.0, help="RAM CRIT threshold (percent)")
    health.add_argument("--warn-disk", type=float, default=80.0, help="Disk WARN threshold (percent)")
    health.add_argument("--crit-disk", type=float, default=90.0, help="Disk CRIT threshold (percent)")

    health.add_argument("--json", action="store_true", help="Output JSON (for scripts/automation)")
    health.add_argument("--no-color", action="store_true", help="Disable colored output")
    health.add_argument("--quiet", action="store_true", help="Only print final STATUS line")
    health.add_argument("--verbose", action="store_true", help="Show extra details per check")

    health.add_argument("--ping", metavar="HOST", help="Ping a host (basic reachability)")
    health.add_argument("--port", nargs=2, metavar=("HOST", "PORT"), help="Check TCP port reachability (HOST PORT)")

    health.set_defaults(func=run_health)

    # logs (with subcommand analyze)
    logs = subparsers.add_parser("logs", help="Analyze server logs")
    logs_sub = logs.add_subparsers(dest="logs_cmd", required=True)

    analyze = logs_sub.add_parser("analyze", help="Analyze an access log file (nginx/common format)")
    analyze.add_argument("file", help="Path to log file (e.g. /var/log/nginx/access.log)")
    analyze.add_argument("--errors", action="store_true", help="Only count error lines (4xx/5xx)")
    analyze.add_argument("--status", type=int, help="Only count a specific status code (e.g. 500)")
    analyze.add_argument("--top-ip", type=int, default=5, help="Show top N IPs (default: 5)")
    analyze.add_argument("--top-path", type=int, default=5, help="Show top N paths (default: 5)")
    analyze.add_argument("--json", action="store_true", help="Output JSON")
    analyze.set_defaults(func=run_logs_analyze)

    args = parser.parse_args()
    args.func(args)

# ----------------------------
# Coloring (safe fallback)
# ----------------------------
def _supports_color() -> bool:
    return sys.stdout.isatty()


def _color(text: str, color_name: str, enable: bool) -> str:
    if not enable or not _supports_color():
        return text

    # Try colorama if installed
    try:
        import colorama  # type: ignore
        from colorama import Fore, Style  # type: ignore

        colorama.init()
        mapping = {
            "green": Fore.GREEN,
            "yellow": Fore.YELLOW,
            "red": Fore.RED,
            "gray": Fore.LIGHTBLACK_EX,
            "reset": Style.RESET_ALL,
        }
        return f"{mapping.get(color_name,'')}{text}{mapping['reset']}"
    except Exception:
        mapping = {
            "green": "\033[32m",
            "yellow": "\033[33m",
            "red": "\033[31m",
            "gray": "\033[90m",
            "reset": "\033[0m",
        }
        return f"{mapping.get(color_name,'')}{text}{mapping['reset']}"


# ----------------------------
# Status helpers
# ----------------------------
STATUS_ORDER = {"OK": 0, "WARN": 1, "CRIT": 2, "UNKNOWN": 3}


def status_from_threshold(value: float, warn: float, crit: float) -> str:
    if value >= crit:
        return "CRIT"
    if value >= warn:
        return "WARN"
    return "OK"


def worst_status(a: str, b: str) -> str:
    return b if STATUS_ORDER[b] > STATUS_ORDER[a] else a


def exit_code(status: str) -> int:
    return {"OK": 0, "WARN": 1, "CRIT": 2, "UNKNOWN": 3}.get(status, 3)


def status_color(status: str) -> str:
    return {"OK": "green", "WARN": "yellow", "CRIT": "red", "UNKNOWN": "gray"}.get(status, "gray")


# ----------------------------
# Formatting helpers
# ----------------------------
def bytes_to_gb(num_bytes: float) -> float:
    return num_bytes / (1024 ** 3)


def fmt_pct(x: float) -> str:
    return f"{x:.1f}%"


def pad(s: str, width: int) -> str:
    return s + " " * max(0, width - len(s))


# ----------------------------
# Health checks
# ----------------------------
@dataclass
class MetricResult:
    name: str
    value: Optional[float]
    status: str
    summary: str
    details: Optional[Dict[str, Any]] = None
    recommendation: Optional[str] = None


def check_cpu(warn: float, crit: float) -> MetricResult:
    cpu = float(psutil.cpu_percent(interval=1))
    st = status_from_threshold(cpu, warn, crit)
    rec = None
    if st == "WARN":
        rec = "CPU is elevated. Check top processes (top/htop) and recent deployments."
    elif st == "CRIT":
        rec = "CPU is critical. Identify runaway processes and consider scaling or restarting services."
    return MetricResult("CPU", cpu, st, fmt_pct(cpu), {"cpu_percent": cpu}, rec)


def check_ram(warn: float, crit: float) -> MetricResult:
    vm = psutil.virtual_memory()
    ram_pct = float(vm.percent)
    st = status_from_threshold(ram_pct, warn, crit)

    used_gb = bytes_to_gb(vm.used)
    total_gb = bytes_to_gb(vm.total)
    avail_gb = bytes_to_gb(vm.available)

    rec = None
    if st == "WARN":
        rec = "RAM usage is high. Check memory-heavy processes and caches."
    elif st == "CRIT":
        rec = "RAM is critical. Risk of OOM. Investigate memory leaks, restart services, or add memory."

    summary = f"{fmt_pct(ram_pct)}  used {used_gb:.2f}/{total_gb:.2f}GB  avail {avail_gb:.2f}GB"
    return MetricResult(
        "RAM",
        ram_pct,
        st,
        summary,
        {"ram_percent": ram_pct, "used_gb": used_gb, "total_gb": total_gb, "available_gb": avail_gb},
        rec,
    )


def check_disk(path: str, warn: float, crit: float) -> MetricResult:
    du = psutil.disk_usage(path)
    disk_pct = float(du.percent)
    st = status_from_threshold(disk_pct, warn, crit)

    used_gb = bytes_to_gb(du.used)
    total_gb = bytes_to_gb(du.total)
    free_gb = bytes_to_gb(du.free)

    rec = None
    if st == "WARN":
        rec = "Disk usage is high. Consider clearing old logs, temp files, or unused images."
    elif st == "CRIT":
        rec = "Disk is nearly full. Free space urgently (logs, caches) to avoid outages."

    summary = f"{fmt_pct(disk_pct)}  used {used_gb:.2f}/{total_gb:.2f}GB  free {free_gb:.2f}GB"
    return MetricResult(
        f"DISK ({path})",
        disk_pct,
        st,
        summary,
        {"path": path, "disk_percent": disk_pct, "used_gb": used_gb, "total_gb": total_gb, "free_gb": free_gb},
        rec,
    )


def check_ping(host: str, timeout_s: int = 2) -> MetricResult:
    try:
        proc = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout_s), host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        ok = proc.returncode == 0
        st = "OK" if ok else "CRIT"
        rec = None if ok else f"Host {host} not reachable. Check network/DNS/firewall."
        return MetricResult(f"PING ({host})", None, st, "reachable" if ok else "unreachable", {"host": host}, rec)
    except Exception:
        return MetricResult(
            f"PING ({host})",
            None,
            "UNKNOWN",
            "ping not available",
            {"host": host},
            "Ping command not available. Install ping/iputils or use port checks.",
        )


def check_port(host: str, port: int, timeout_s: float = 1.5) -> MetricResult:
    reachable = False
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            reachable = True
    except Exception:
        reachable = False

    st = "OK" if reachable else "CRIT"
    rec = None if reachable else f"Port {port} on {host} is not reachable. Check service/firewall/security groups."
    return MetricResult(
        f"PORT ({host}:{port})", None, st, "open" if reachable else "closed", {"host": host, "port": port}, rec
    )


def build_table(results: List[MetricResult], overall: str, use_color: bool, verbose: bool) -> str:
    title = "OPSBOX HEALTH"
    lines: List[str] = []
    lines.append("=" * (len(title) + 10))
    lines.append(f"     {title}")
    lines.append("=" * (len(title) + 10))

    name_w = max(6, max(len(r.name) for r in results))
    stat_w = 7

    for r in results:
        st_txt = _color(r.status, status_color(r.status), use_color)
        lines.append(f"{pad(r.name, name_w)} : {pad(r.summary, 34)} {pad(st_txt, stat_w)}")
        if verbose and r.details:
            for k, v in r.details.items():
                lines.append(f"  - {k}: {v}")

    lines.append("-" * (len(title) + 10))
    overall_colored = _color(overall, status_color(overall), use_color)
    lines.append(f"STATUS: {overall_colored}")

    recs = [r.recommendation for r in results if r.recommendation]
    if recs:
        lines.append("")
        lines.append("RECOMMENDATIONS:")
        for rec in recs:
            lines.append(f"- {rec}")

    return "\n".join(lines)


def build_json(results: List[MetricResult], overall: str) -> str:
    payload: Dict[str, Any] = {"status": overall, "checks": []}
    for r in results:
        payload["checks"].append(
            {
                "name": r.name,
                "status": r.status,
                "value": r.value,
                "summary": r.summary,
                "details": r.details or {},
                "recommendation": r.recommendation,
            }
        )
    return json.dumps(payload, indent=2)


# ----------------------------
# Logs analyzer
# ----------------------------
# Supports Common Log Format and many Nginx "combined" logs:
#   127.0.0.1 - - [10/Oct/2000:13:55:36 +0000] "GET /path HTTP/1.1" 200 123 "-" "UA..."
LOG_RE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+) \S+" (?P<status>\d{3}) (?P<size>\S+)'
)


@dataclass
class LogStats:
    total: int
    errors: int
    status_counts: Dict[str, int]
    top_ips: List[Tuple[str, int]]
    top_paths: List[Tuple[str, int]]
    bytes_total: int
    parse_failed: int


def iter_lines(path: str) -> Iterable[str]:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            yield line.rstrip("\n")


def analyze_log(
    file_path: str,
    only_errors: bool = False,
    status_filter: Optional[int] = None,
    top_ip: int = 5,
    top_path: int = 5,
) -> LogStats:
    total = 0
    errors = 0
    bytes_total = 0
    parse_failed = 0

    ip_counter: Counter[str] = Counter()
    path_counter: Counter[str] = Counter()
    status_counter: Counter[str] = Counter()

    for line in iter_lines(file_path):
        m = LOG_RE.match(line)
        if not m:
            parse_failed += 1
            continue

        ip = m.group("ip")
        path = m.group("path")
        status = int(m.group("status"))
        size_raw = m.group("size")

        # Filters
        if status_filter is not None and status != status_filter:
            continue

        is_error = 400 <= status <= 599
        if only_errors and not is_error:
            continue

        total += 1
        if is_error:
            errors += 1

        ip_counter[ip] += 1
        path_counter[path] += 1
        status_counter[str(status)] += 1

        if size_raw.isdigit():
            bytes_total += int(size_raw)

    return LogStats(
        total=total,
        errors=errors,
        status_counts=dict(status_counter),
        top_ips=ip_counter.most_common(top_ip),
        top_paths=path_counter.most_common(top_path),
        bytes_total=bytes_total,
        parse_failed=parse_failed,
    )


def render_logs_text(file_path: str, stats: LogStats) -> str:
    title = "OPSBOX LOGS"
    lines: List[str] = []
    lines.append("=" * (len(title) + 10))
    lines.append(f"     {title}")
    lines.append("=" * (len(title) + 10))
    lines.append(f"File: {file_path}")
    lines.append("")
    lines.append(f"Total matched lines : {stats.total}")
    lines.append(f"Errors (4xx/5xx)    : {stats.errors}")
    lines.append(f"Bytes transferred   : {stats.bytes_total}")
    lines.append(f"Parse failures      : {stats.parse_failed}")
    lines.append("")
    lines.append("Top IPs:")
    if stats.top_ips:
        for ip, c in stats.top_ips:
            lines.append(f"  - {ip}: {c}")
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("Top Paths:")
    if stats.top_paths:
        for p, c in stats.top_paths:
            lines.append(f"  - {p}: {c}")
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("Status counts:")
    if stats.status_counts:
        for k in sorted(stats.status_counts.keys(), key=lambda x: int(x)):
            lines.append(f"  - {k}: {stats.status_counts[k]}")
    else:
        lines.append("  (none)")

    return "\n".join(lines)


def render_logs_json(file_path: str, stats: LogStats) -> str:
    payload = {
        "file": file_path,
        "total": stats.total,
        "errors": stats.errors,
        "bytes_total": stats.bytes_total,
        "parse_failed": stats.parse_failed,
        "top_ips": stats.top_ips,
        "top_paths": stats.top_paths,
        "status_counts": stats.status_counts,
    }
    return json.dumps(payload, indent=2)




def run_health(args: argparse.Namespace) -> None:

    if not (args.cpu or args.ram or args.disk or args.ping or args.port):
        args.cpu = True
        args.ram = True
        args.disk = True
        
    use_color = not args.no_color
    selected_any = False
    results: List[MetricResult] = []
    overall = "OK"

    if args.cpu:
        selected_any = True
        r = check_cpu(args.warn_cpu, args.crit_cpu)
        results.append(r)
        overall = worst_status(overall, r.status)

    if args.ram:
        selected_any = True
        r = check_ram(args.warn_ram, args.crit_ram)
        results.append(r)
        overall = worst_status(overall, r.status)

    if args.disk:
        selected_any = True
        r = check_disk(args.path, args.warn_disk, args.crit_disk)
        results.append(r)
        overall = worst_status(overall, r.status)

    if args.ping:
        selected_any = True
        r = check_ping(args.ping)
        results.append(r)
        overall = worst_status(overall, r.status)

    if args.port:
        selected_any = True
        host, port_str = args.port
        try:
            port = int(port_str)
        except ValueError:
            r = MetricResult(
                f"PORT ({host}:{port_str})",
                None,
                "UNKNOWN",
                "invalid port",
                {"host": host, "port": port_str},
                "Provide a numeric port, e.g. --port 127.0.0.1 5432",
            )
        else:
            r = check_port(host, port)
        results.append(r)
        overall = worst_status(overall, r.status)

    if not selected_any:
        msg = "Nothing selected. Try: opsbox health --cpu --ram --disk"
        if args.json:
            print(json.dumps({"status": "UNKNOWN", "error": msg}, indent=2))
        else:
            print(msg)
        sys.exit(3)

    if args.json:
        print(build_json(results, overall))
        sys.exit(exit_code(overall))

    if args.quiet:
        print(f"STATUS: {overall}")
        sys.exit(exit_code(overall))

    print(build_table(results, overall, use_color=use_color, verbose=args.verbose))
    sys.exit(exit_code(overall))


def run_logs_analyze(args: argparse.Namespace) -> None:
    stats = analyze_log(
        file_path=args.file,
        only_errors=args.errors,
        status_filter=args.status,
        top_ip=args.top_ip,
        top_path=args.top_path,
    )

    if args.json:
        print(render_logs_json(args.file, stats))
    else:
        print(render_logs_text(args.file, stats))


if __name__ == "__main__":
    main()