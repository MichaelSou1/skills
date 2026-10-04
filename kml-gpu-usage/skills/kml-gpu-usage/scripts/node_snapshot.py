#!/usr/bin/env python3
"""Read-only node inventory; no torch import, CUDA allocation, or benchmark."""

import argparse
import csv
import importlib.metadata
import io
import json
import os
from pathlib import Path
import re
import resource
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
import xml.etree.ElementTree as ET


def run_command(argv, timeout):
    if not shutil.which(argv[0]):
        return {"status": "unavailable", "command": argv}
    try:
        result = subprocess.run(argv, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=timeout, check=False)
        return {"status": "ok" if result.returncode == 0 else "error",
                "returncode": result.returncode,
                "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "command": argv, "timeout_seconds": timeout}
    except OSError as exc:
        return {"status": "error", "command": argv, "error": str(exc)}


def read_text(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def parse_gpu_csv(text):
    fields = ("index", "uuid", "name", "memory_total_mib", "memory_free_mib",
              "utilization_gpu_percent", "driver_version")
    rows = []
    for row in csv.reader(io.StringIO(text)):
        if not row:
            continue
        if len(row) != len(fields):
            raise ValueError("Unexpected nvidia-smi GPU CSV columns")
        rows.append(dict(zip(fields, (value.strip() for value in row))))
    return rows


def parse_fabric_xml(text):
    root = ET.fromstring(text)
    rows = []
    for gpu in root.findall("gpu"):
        fabric = gpu.find("fabric")
        rows.append({"uuid": gpu.findtext("uuid"),
                     "state": fabric.findtext("state") if fabric is not None else None,
                     "status": fabric.findtext("status") if fabric is not None else None})
    return rows


def rdma_ports(root):
    rows = []
    if not root.exists():
        return {"status": "unavailable", "ports": rows}
    try:
        for device in sorted(root.iterdir()):
            net = device / "device/net"
            interfaces = sorted(p.name for p in net.iterdir()) if net.exists() else []
            for port in sorted((device / "ports").glob("*")):
                rows.append({"device": device.name, "port": port.name,
                             "interfaces_visible_at_device": interfaces,
                             "state": read_text(port / "state"),
                             "rate": read_text(port / "rate"),
                             "link_layer": read_text(port / "link_layer")})
        return {"status": "ok", "ports": rows}
    except OSError as exc:
        return {"status": "error", "ports": rows, "error": str(exc)}


def package_versions():
    result = {}
    for name in ("torch", "triton", "flash-attn", "flash-attn-3", "flash-attn-4",
                 "transformer-engine", "deepspeed", "accelerate"):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def snapshot(mount, timeout):
    query = "index,uuid,name,memory.total,memory.free,utilization.gpu,driver_version"
    gpu = run_command(["nvidia-smi", "--query-gpu=" + query,
                       "--format=csv,noheader,nounits"], timeout)
    if gpu["status"] == "ok":
        try:
            gpu["devices"] = parse_gpu_csv(gpu.pop("stdout"))
        except ValueError as exc:
            gpu["status"], gpu["error"] = "parse_error", str(exc)
    fabric = run_command(["nvidia-smi", "-q", "-x"], timeout)
    if fabric["status"] == "ok":
        try:
            fabric["devices"] = parse_fabric_xml(fabric.pop("stdout"))
        except ET.ParseError as exc:
            fabric["status"], fabric["error"] = "parse_error", str(exc)
    # Do not expose the full XML (process inventory and irrelevant host metadata).
    fabric.pop("stdout", None)
    topology = run_command(["nvidia-smi", "topo", "-m"], timeout)
    if "stdout" in topology:
        topology["stdout"] = re.sub(r"\x1b\[[0-9;]*m", "", topology["stdout"])
    status = read_text("/proc/self/status") or ""
    affinity = {line.split(":", 1)[0]: line.split(":", 1)[1].strip()
                for line in status.splitlines()
                if line.startswith(("Cpus_allowed_list:", "Mems_allowed_list:"))}
    limits = {}
    for relative in ("cpu.max", "cpuset.cpus.effective", "memory.max", "memory.current",
                     "cpu/cpu.cfs_quota_us", "cpu/cpu.cfs_period_us",
                     "cpu,cpuacct/cpu.cfs_quota_us", "cpu,cpuacct/cpu.cfs_period_us",
                     "memory/memory.limit_in_bytes", "cpuset/cpuset.cpus"):
        value = read_text(Path("/sys/fs/cgroup") / relative)
        if value is not None:
            limits[relative] = value
    storage = run_command(["findmnt", "--json", "--target", str(mount),
                           "--output", "TARGET,FSTYPE"], timeout)
    if storage["status"] == "ok":
        try:
            storage["mounts"] = json.loads(storage.pop("stdout")).get("filesystems", [])
        except ValueError as exc:
            storage["status"], storage["error"] = "parse_error", str(exc)
    shm = {}
    if Path("/dev/shm").exists():
        try:
            total, used, free = shutil.disk_usage("/dev/shm")
            shm = {"total_bytes": total, "used_bytes": used, "free_bytes": free}
        except OSError as exc:
            shm = {"error": str(exc)}
    return {
        "schema_version": 1,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "python": {"executable": sys.executable, "version": sys.version.split()[0],
                   "package_metadata": package_versions()},
        "gpu": gpu, "fabric": fabric, "topology": topology,
        "rdma": rdma_ports(Path("/sys/class/infiniband")),
        "ibdev2netdev": run_command(["ibdev2netdev"], timeout),
        "cpu": {"logical_cpus_visible": os.cpu_count(), "affinity": affinity,
                "proc_self_cgroup": read_text("/proc/self/cgroup"),
                "visible_cgroup_limits": limits},
        "memory": {"proc_meminfo": read_text("/proc/meminfo"),
                   "memlock_soft_hard_bytes": list(resource.getrlimit(resource.RLIMIT_MEMLOCK))},
        "storage": {"requested_path": str(mount), "exists": mount.exists(),
                    "findmnt": storage, "dev_shm": shm},
        "notes": ["Read-only inventory; no CUDA initialization or collective benchmark.",
                  "Package metadata describes this interpreter, not an arbitrary project environment.",
                  "Visible host/cgroup values are not a guarantee of exclusive capacity.",
                  "Missing/error fields are unknown; link rate is not measured NCCL bandwidth."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mount", type=Path, default=Path("/mmu_vlm_hdd"))
    parser.add_argument("--output", type=Path,
                        help="Save JSON in the project run directory; otherwise print to stdout")
    parser.add_argument("--timeout", type=float, default=15,
                        help="Per-command timeout in seconds (default: 15)")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if sys.platform != "linux":
        parser.error("Run this snapshot on the target Linux KML node, not the local workstation")
    payload = json.dumps(snapshot(args.mount, args.timeout), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        # Refuse to overwrite an existing snapshot or follow an existing symlink.
        with args.output.open("x") as handle:
            handle.write(payload)
        print(str(args.output))
    else:
        sys.stdout.write(payload)


if __name__ == "__main__":
    main()
