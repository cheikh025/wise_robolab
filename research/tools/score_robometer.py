#!/usr/bin/env python3
"""M2: score Cosmos3 dreams and matching real RoboLab sensor frames with Robometer-4B.

Offline only — no policy-loop coupling. One camera per Robometer call, three
views scored separately, no rescaling (per M2 skill: DROID deployments use a
single exterior view; RBM-1M contains no tiled frames).

Adapted from research/bootstrap/robometer_progress_test.md, re-verified
against the current robometer checkout (commit recorded in the RUN file)
before use, per CLAUDE.md's source-hierarchy rule.

Run with the robometer interpreter:
  /workspace/robometer/.venv/bin/python research/tools/score_robometer.py \
      --run-dir <dir with dreams/dream_env0_call*.mp4> \
      --sensor-video <path to the matching sensor .mp4> \
      --task "<verbatim env instruction>"
"""
import argparse
import glob
import json
import os

import cv2
import numpy as np
import torch

from robometer.utils.save import load_model_from_hf
from robometer.utils.setup_utils import setup_batch_collator
from robometer.evals.eval_server import process_batch_helper
from robometer.evals.eval_utils import raw_dict_to_sample

CHUNK = 32  # env steps per policy call (== Cosmos3-Edge action chunk size, verified in M1)


def read_video(path):
    cap = cv2.VideoCapture(path)
    frames = []
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    cap.release()
    return np.asarray(frames, dtype=np.uint8)


def detect_seam(frame):
    """Row of the wrist / exterior boundary, found by max row-to-row change."""
    g = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(np.float32)
    d = np.abs(np.diff(g, axis=0)).mean(axis=1)
    lo, hi = int(len(d) * 0.55), int(len(d) * 0.78)
    return lo + int(d[lo:hi].argmax())


def split_dream(dream):
    """(T, H, W, 3) -> {'wrist','left','right'}, each (T, h, w, 3).

    Client stacks wrist over [left|right]; wrist owns the top 2/3 by design,
    but VAE decode rounds height to a multiple of 16, so derive the seam by
    ratio and cross-check against the detected edge rather than hardcoding.
    """
    h, w = dream.shape[1:3]
    seam = round(h * 2 / 3)
    found = detect_seam(dream[0])
    if abs(found - seam) > 4:
        print(f"  !! seam mismatch: ratio says {seam}, image says {found}. Using {found}.")
        seam = found
    else:
        print(f"  seam row {seam} (detected {found})")
    return {"wrist": dream[:, :seam],
            "left":  dream[:, seam:, : w // 2],
            "right": dream[:, seam:, w // 2:]}


def split_sensor(sensor, start, n):
    """2560x360 sensor video -> the three policy-input cameras at native 360x640.

    Panel layout is head | left | right | wrist at 640px each (verified via
    ffprobe against RoboLab's own output in this checkout). head is rendered
    by the sim but never sent to the policy, so it is skipped here.
    """
    clip = sensor[start:start + n]
    return {"wrist": clip[:, :, 1920:2560],
            "left":  clip[:, :, 640:1280],
            "right": clip[:, :, 1280:1920]}


def load_robometer(path, device):
    dev = torch.device(device)
    exp_config, tokenizer, processor, model = load_model_from_hf(model_path=path, device=dev)
    model.eval()
    collator = setup_batch_collator(processor, tokenizer, exp_config, is_eval=True)
    loss_cfg = getattr(exp_config, "loss", None)
    return {
        "model": model, "tokenizer": tokenizer, "collator": collator, "device": dev,
        "is_discrete": getattr(loss_cfg, "progress_loss_type", "l2").lower() == "discrete",
        "num_bins": getattr(loss_cfg, "progress_discrete_bins", None)
                    or getattr(exp_config.model, "progress_discrete_bins", 10),
        "max_frames": int(getattr(getattr(exp_config, "data", None), "max_frames", 8)),
        "model_type": exp_config.model.model_type,
    }


def score(rm, frames, task):
    """One clip -> (per_frame_progress, last_frame_progress)."""
    raw = {"frames": np.ascontiguousarray(frames), "task": task, "id": "0",
           "metadata": {"subsequence_length": int(frames.shape[0])},
           "video_embeddings": None, "text_embedding": None}
    s = raw_dict_to_sample(raw_data=raw, max_frames=rm["max_frames"], sample_type="progress")
    # autocast required -- upstream issue #38 (BFloat16/Float mismatch on
    # some GPUs); harmless to keep even if not strictly needed on this GPU.
    with torch.autocast("cuda", dtype=torch.bfloat16):
        out = process_batch_helper(
            model_type=rm["model_type"], model=rm["model"], tokenizer=rm["tokenizer"],
            batch_collator=rm["collator"], device=rm["device"],
            batch_data=[s.model_dump()], job_id=0,
            is_discrete_mode=rm["is_discrete"], num_bins=rm["num_bins"],
            use_frame_steps=False,
        )
    per_frame = [float(x) for x in out["outputs_progress"]["progress_pred"][0]]
    return per_frame, max(0.0, min(1.0, per_frame[-1]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-dir", required=True)
    p.add_argument("--sensor-video", required=True)
    p.add_argument("--task", required=True, help="verbatim env instruction")
    p.add_argument("--model-path", default="robometer/Robometer-4B")
    p.add_argument("--device", default="cuda")
    p.add_argument("--out", default=None)
    a = p.parse_args()

    rm = load_robometer(a.model_path, a.device)
    print(f"loaded: max_frames={rm['max_frames']} bins={rm['num_bins']} "
          f"discrete={rm['is_discrete']} model_type={rm['model_type']}")

    sensor = read_video(a.sensor_video)
    print(f"sensor video: {sensor.shape}")

    rows = []
    dream_glob = os.path.join(a.run_dir, "dreams", "dream_env0_call*.mp4")
    for path in sorted(glob.glob(dream_glob)):
        k = int(path.split("call")[-1].split(".")[0])
        dream = read_video(path)
        print(f"call {k:03d}  dream {dream.shape}")

        dream_views = split_dream(dream)
        real_views = split_sensor(sensor, k * CHUNK, len(dream))
        if len(real_views["wrist"]) == 0:
            print("    (no real frames for this call, skipping)")
            continue

        row = {"call": k}
        for v in ("wrist", "left", "right"):
            dv, rv = dream_views[v], real_views[v]
            d_curve, d_last = score(rm, dv, a.task)
            r_curve, r_last = score(rm, rv, a.task)
            print(f"    {v:<5} dream {dv.shape[1]}x{dv.shape[2]} last={d_last:.3f} | "
                  f"real {rv.shape[1]}x{rv.shape[2]} last={r_last:.3f}")
            print(f"          dream {[round(x, 3) for x in d_curve]}")
            print(f"          real  {[round(x, 3) for x in r_curve]}")
            row[v] = {"dream_last": d_last, "real_last": r_last,
                      "dream_curve": d_curve, "real_curve": r_curve}
        rows.append(row)

    out_path = a.out or os.path.join(a.run_dir, "robometer_progress.json")
    with open(out_path, "w") as f:
        json.dump(rows, f, indent=2)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
