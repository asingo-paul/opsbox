
# opsbox

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/asingo-paul/opsbox)](https://github.com/asingo-paul/opsbox/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/asingo-paul/opsbox?style=social)](https://github.com/asingo-paul/opsbox/stargazers)
[![Issues](https://img.shields.io/github/issues/asingo-paul/opsbox)](https://github.com/asingo-paul/opsbox/issues)
[![Last Commit](https://img.shields.io/github/last-commit/asingo-paul/opsbox)](https://github.com/asingo-paul/opsbox/commits/main)
[![Repo Size](https://img.shields.io/github/repo-size/asingo-paul/opsbox)](https://github.com/asingo-paul/opsbox)
[![CLI Tool](https://img.shields.io/badge/type-CLI%20Tool-black)](https://github.com/asingo-paul/opsbox)
[![DevOps](https://img.shields.io/badge/category-DevOps-orange)](https://github.com/topics/devops)
[![Open Source](https://img.shields.io/badge/Open%20Source-Yes-brightgreen)](https://opensource.org/)


🧰 **opsbox** is an open-source DevOps CLI tool that provides instant server health insights and log analysis using a single command.

Instead of running multiple Linux utilities, opsbox gives engineers a clear system status immediately.

```

opsbox health

```

---

## ✨ Features

-  CPU, RAM and Disk health monitoring
-  Status evaluation (OK / WARN / CRIT)
-  Threshold-based alerts
-  Log analysis (nginx / common access logs)
-  JSON output for automation & CI/CD
-  Monitoring-friendly exit codes
-  Global CLI command (`opsbox`)
-  Lightweight and fast

---

##  Why opsbox?

Typical workflow:

```

top
free -h
df -h
ping
netstat

```

With opsbox:

```

opsbox health

````

👉 One command → instant decision.

---

#  Installation

## Requirements

- Python **3.9+**
- Linux / macOS (recommended)

---

## Install from Source

Clone the repository:

```bash
git clone https://github.com/asingo-paul/opsbox.git
cd opsbox
````

(Optional) Create virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install globally:

```bash
pip install -e .
```

Verify installation:

```bash
opsbox --help
```

---

## Install on Servers (VPS / Cloud)

```bash
git clone https://github.com/asingo-paul/opsbox.git
cd opsbox
pip install -e .
opsbox health
```

Perfect for:

* cloud instances
* homelabs
* automation scripts
* monitoring experiments

---

# 🧭 Usage

General syntax:

```bash
opsbox <command> [options]
```

Commands:

```
health   → system monitoring
logs     → log analysis
```

---

# ❤️ HEALTH COMMAND

## Default Health Check

Runs CPU + RAM + Disk checks automatically:

```bash
opsbox health
```

---

## Individual Checks

CPU:

```bash
opsbox health --cpu
```

RAM:

```bash
opsbox health --ram
```

Disk:

```bash
opsbox health --disk
```

Specific filesystem:

```bash
opsbox health --disk --path /
opsbox health --disk --path .
```

Run all explicitly:

```bash
opsbox health --cpu --ram --disk --path .
```

---

## ⚠️ Threshold Configuration

CPU:

```bash
opsbox health --cpu --warn-cpu 70 --crit-cpu 90
```

RAM:

```bash
opsbox health --ram --warn-ram 75 --crit-ram 90
```

Disk:

```bash
opsbox health --disk --path . --warn-disk 80 --crit-disk 90
```

Combined example:

```bash
opsbox health --cpu --ram --disk --path . \
  --warn-cpu 70 --crit-cpu 90 \
  --warn-ram 75 --crit-ram 90 \
  --warn-disk 80 --crit-disk 90
```

---

## 🌐 Network Checks

Ping host:

```bash
opsbox health --ping 8.8.8.8
opsbox health --ping google.com
```

Check TCP port:

```bash
opsbox health --port 127.0.0.1 22
opsbox health --port 127.0.0.1 5432
```

Combine checks:

```bash
opsbox health --cpu --disk --path . --ping 8.8.8.8 --port 127.0.0.1 22
```

---

## 📤 Output Modes

### Normal Output

```bash
opsbox health --cpu --ram
```

---

### Quiet Mode (Automation)

```bash
opsbox health --quiet
```

Output:

```
STATUS: OK
```

---

### JSON Output

```bash
opsbox health --json
```

Useful for pipelines and scripts.

---

### Verbose Mode

```bash
opsbox health --verbose
```

---

## 🔢 Exit Codes

| Status  | Exit Code |
| ------- | --------- |
| OK      | 0         |
| WARN    | 1         |
| CRIT    | 2         |
| UNKNOWN | 3         |

Example automation:

```bash
opsbox health || echo "Server needs attention"
```

---

# 📊 LOGS COMMAND

Analyze nginx or common access logs.

---

## Basic Analysis

```bash
opsbox logs analyze /var/log/nginx/access.log
```

---

## Errors Only

```bash
opsbox logs analyze access.log --errors
```

---

## Filter Status Code

```bash
opsbox logs analyze access.log --status 500
opsbox logs analyze access.log --status 404
```

---

## Top Requests

```bash
opsbox logs analyze access.log --top-ip 10 --top-path 10
```

---

## JSON Output

```bash
opsbox logs analyze access.log --json
```

---

# 🧪 Example Output

```
================ OPSBOX HEALTH ================
CPU            : 22.3%                  OK
RAM            : 61.0%                  OK
DISK (.)       : 44.1%                  OK
-----------------------------------------------
STATUS: OK
```

---

# 🤝 Contributing

Contributions are welcome!

Ideas to improve:

* service checks (`systemctl`)
* time filtering in logs
* alert integrations
* remote host monitoring
* packaging for PyPI

Steps:

1. Fork repository
2. Create feature branch
3. Commit changes
4. Open Pull Request 

---

# 📄 License

MIT License

---

## ⭐ Support

If you find opsbox useful:

* Star the repo ⭐
* Open issues
* Suggest features
* Contribute improvements

Building in public 🚀

````


