#!/usr/bin/env python3
"""Append one JSON experiment record with lightweight schema checks."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ALLOWED_MILESTONES = {"M0_SETUP","M1_COSMOS","M2_ROBOMETER_OFFLINE","M3_ROBOMETER_BESTOFK","M4_IDM_TRAIN","M5_IDM_VALIDATE","M6_WISE_INTEGRATE","M7_WISE_EXPERIMENT"}
ALLOWED_STATUS = {"planned","running","completed","aborted","failed","blocked"}
ALLOWED_DECISIONS = {"NONE","KEEP","REJECT","BRANCH","RETEST","MILESTONE_PASS","MILESTONE_FAIL","MILESTONE_BLOCKED","COMPARISON","ABORTED","SUPERSEDED"}

def validate(r):
    for k in ("id","name","milestone","status","decision","report"):
        if k not in r:
            raise ValueError(f"missing required field: {k}")
    if not isinstance(r["id"], int) or r["id"] < 0: raise ValueError("id must be nonnegative integer")
    if r["milestone"] not in ALLOWED_MILESTONES: raise ValueError("invalid milestone")
    if r["status"] not in ALLOWED_STATUS: raise ValueError("invalid status")
    if r["decision"] not in ALLOWED_DECISIONS: raise ValueError("invalid decision")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("record", help="JSON string or @path/to/record.json")
    p.add_argument("--ledger", default="research/EXPERIMENTS.jsonl")
    a=p.parse_args()
    text=Path(a.record[1:]).read_text() if a.record.startswith("@") else a.record
    r=json.loads(text); validate(r)
    path=Path(a.ledger); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f: f.write(json.dumps(r, sort_keys=True)+"\n")
    print(f"appended experiment {r['id']} to {path}")
if __name__=="__main__": main()
