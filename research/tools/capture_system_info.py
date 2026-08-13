#!/usr/bin/env python3
"""Capture reproducibility information without dumping secrets/environment variables."""
from __future__ import annotations
import json, os, platform, shutil, subprocess, sys
from pathlib import Path


def run(cmd):
    try:
        p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
        return {"returncode": p.returncode, "output": p.stdout.strip()}
    except Exception as e:
        return {"error": repr(e)}


def main():
    out = {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "disk": shutil.disk_usage(str(Path.cwd()))._asdict() if hasattr(shutil.disk_usage(str(Path.cwd())), '_asdict') else tuple(shutil.disk_usage(str(Path.cwd()))),
        "git_status": run(["git","status","--short","--branch"]),
        "git_head": run(["git","rev-parse","HEAD"]),
        "git_remotes": run(["git","remote","-v"]),
        "nvidia_smi": run(["nvidia-smi"]),
        "pip_freeze": run([sys.executable,"-m","pip","freeze"]),
    }
    try:
        import torch
        out["torch"] = {
            "version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count(),
            "devices": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())] if torch.cuda.is_available() else [],
        }
    except Exception as e:
        out["torch"] = {"error": repr(e)}
    print(json.dumps(out, indent=2, default=str))

if __name__ == "__main__":
    main()
