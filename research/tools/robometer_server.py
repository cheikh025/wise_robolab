#!/usr/bin/env python3
"""Minimal Robometer-4B scoring HTTP server for WISE Best-of-K (M3).

RoboLab (Python 3.11, torch 2.7.0+cu128) and Robometer (Python 3.10, torch
2.8.0+cu128) are incompatible in-process (CLAUDE.md environment discipline:
treat as separate runtimes). Rather than integrate with robometer's generic
multi-sample /evaluate_batch_npy API (designed for the training/eval
pipeline's own trajectory-dict shape, unverified against our single-clip
use case), this wraps the exact load_robometer()/score() path already
verified end-to-end offline in RUN_0004 behind a minimal endpoint.

Run with the robometer interpreter:
  /workspace/robometer/.venv/bin/python research/tools/robometer_server.py --port 8100

Endpoints:
  GET  /health -> {"status": "ok", "model_type": ...}
  POST /score  -> multipart form: file="frames.npy" ((T,H,W,3) uint8 RGB), field="task"
                  returns {"per_frame": [...], "last": float}
"""
import argparse
import io

import numpy as np
import torch
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile

from robometer.utils.save import load_model_from_hf
from robometer.utils.setup_utils import setup_batch_collator
from robometer.evals.eval_server import process_batch_helper
from robometer.evals.eval_utils import raw_dict_to_sample

app = FastAPI(title="WISE Robometer scoring server (M3)")
_state = {}


def load_robometer(path: str, device: str):
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
    raw = {"frames": np.ascontiguousarray(frames), "task": task, "id": "0",
           "metadata": {"subsequence_length": int(frames.shape[0])},
           "video_embeddings": None, "text_embedding": None}
    s = raw_dict_to_sample(raw_data=raw, max_frames=rm["max_frames"], sample_type="progress")
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


@app.get("/health")
async def health():
    return {"status": "ok", "model_type": _state["rm"]["model_type"]}


@app.post("/score")
async def score_endpoint(file: UploadFile = File(...), task: str = Form(...)):
    raw_bytes = await file.read()
    frames = np.load(io.BytesIO(raw_bytes))
    per_frame, last = score(_state["rm"], frames, task)
    return {"per_frame": per_frame, "last": last}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model-path", default="robometer/Robometer-4B")
    p.add_argument("--device", default="cuda")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8100)
    a = p.parse_args()

    print(f"[robometer-server] loading {a.model_path} on {a.device} ...")
    _state["rm"] = load_robometer(a.model_path, a.device)
    print(f"[robometer-server] loaded: model_type={_state['rm']['model_type']} "
          f"max_frames={_state['rm']['max_frames']} bins={_state['rm']['num_bins']}")
    print(f"[robometer-server] ready on {a.host}:{a.port}")
    uvicorn.run(app, host=a.host, port=a.port)


if __name__ == "__main__":
    main()
