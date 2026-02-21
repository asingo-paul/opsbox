Perfect — below is an **updated README.md** that already includes a clear **USAGE section** (like professional CLI tools).

Just **replace your current README.md** with this one.

---

# ✅ `README.md` (FULL — with Usage Commands)

````md
# opsbox

`opsbox` is a DevOps-style CLI tool written in Python for:

✅ Server health monitoring  
✅ Log analysis  
✅ Automation-friendly output (JSON + exit codes)  

Built for learning backend and DevOps engineering concepts:
- CLI design
- system monitoring
- log parsing
- streaming large files
- thresholds & alert logic

---

# Installation

## Requirements

- Python 3.9+
- Linux/macOS recommended
- `psutil`

Install dependencies:

```bash
python3 -m pip install psutil
````

(Optional — better colors)

```bash
python3 -m pip install colorama
```

---

# Running opsbox

From project directory:

```bash
python3 cli.py --help
```

---

# USAGE

General structure:

```bash
python3 cli.py <command> [options]
```

Commands:

```
health   → system health monitoring
logs     → log analysis
```

---

# HEALTH COMMAND

## Basic Usage

Check CPU:

```bash
python3 cli.py health --cpu
```

Check RAM:

```bash
python3 cli.py health --ram
```

Check disk (current filesystem):

```bash
python3 cli.py health --disk
```

Check disk for a specific path:

```bash
python3 cli.py health --disk --path /
python3 cli.py health --disk --path /home
python3 cli.py health --disk --path .
```

Run all checks:

```bash
python3 cli.py health --cpu --ram --disk --path .
```

---

## Threshold Usage (WARN / CRIT)

CPU thresholds:

```bash
python3 cli.py health --cpu --warn-cpu 70 --crit-cpu 90
```

RAM thresholds:

```bash
python3 cli.py health --ram --warn-ram 75 --crit-ram 90
```

Disk thresholds:

```bash
python3 cli.py health --disk --path . --warn-disk 80 --crit-disk 90
```

All together:

```bash
python3 cli.py health --cpu --ram --disk --path . \
  --warn-cpu 70 --crit-cpu 90 \
  --warn-ram 75 --crit-ram 90 \
  --warn-disk 80 --crit-disk 90
```

---

## Network Checks

Ping a host:

```bash
python3 cli.py health --ping 8.8.8.8
python3 cli.py health --ping google.com
```

Check TCP port:

```bash
python3 cli.py health --port 127.0.0.1 22
python3 cli.py health --port 127.0.0.1 5432
```

Combine checks:

```bash
python3 cli.py health --cpu --disk --path . --ping 8.8.8.8 --port 127.0.0.1 22
```

---

## Output Modes

### Normal output

(default readable table)

```bash
python3 cli.py health --cpu --ram
```

### Quiet mode (automation)

```bash
python3 cli.py health --cpu --quiet
```

Output:

```
STATUS: OK
```

---

### JSON Output (for scripts)

```bash
python3 cli.py health --cpu --ram --json
```

---

### Verbose Output

```bash
python3 cli.py health --cpu --verbose
```

Shows internal metric details.

---

## Exit Codes

opsbox follows monitoring standards:

| Status  | Exit Code |
| ------- | --------- |
| OK      | 0         |
| WARN    | 1         |
| CRIT    | 2         |
| UNKNOWN | 3         |

Example automation:

```bash
python3 cli.py health --cpu || echo "Server needs attention"
```

---

# LOGS COMMAND

opsbox can analyze access logs (nginx / common log format).

---

## Basic Usage

Analyze log file:

```bash
python3 cli.py logs analyze /var/log/nginx/access.log
```

---

## Error Analysis

Show only error responses:

```bash
python3 cli.py logs analyze access.log --errors
```

---

## Filter by Status Code

```bash
python3 cli.py logs analyze access.log --status 500
python3 cli.py logs analyze access.log --status 404
```

---

## Top Requests

Show top IPs and endpoints:

```bash
python3 cli.py logs analyze access.log --top-ip 10 --top-path 10
```

---

## JSON Output

```bash
python3 cli.py logs analyze access.log --json
```

---

## Combined Examples

Errors + Top Requests:

```bash
python3 cli.py logs analyze access.log --errors --top-ip 20 --top-path 20
```

Specific status + JSON:

```bash
python3 cli.py logs analyze access.log --status 500 --json
```

---

# Example Output

```
================ OPSBOX HEALTH ================
CPU            : 22.3%                  OK
RAM            : 61.0%                  OK
DISK (.)       : 44.1%                  OK
-----------------------------------------------
STATUS: OK
```

---

# Why opsbox?

Instead of running multiple commands:

```
top
free -h
df -h
ping
netstat
```

You run:

```bash
opsbox health
```

One command → instant decision.

---

# Future Improvements

Ideas you can implement:

* Service checks (`systemctl`)
* Time filtering in logs
* Slow request detection
* Email/webhook alerts
* Installable CLI (`pip install opsbox`)
* Remote host monitoring

---

# License

MIT

```

---



You built:

- Multi-command CLI
- Monitoring tool
- Threshold engine
- Structured output
- JSON automation support
- Streaming log analyzer
- Real README like production tools



---


