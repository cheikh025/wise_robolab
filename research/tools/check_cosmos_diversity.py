#!/usr/bin/env python3
"""M1 candidate-diversity check: fixed context, K repeated requests, measure spread.

Sends the exact same observation/state/instruction to the running Cosmos3-Edge
policy server K times (no sim stepping between calls) and reports whether the
returned action chunks differ. Uses the same request wire format as
RoboLab's stock policies/cosmos3/client.py (Cosmos3Client._pack_request), but
against a fixed synthetic observation instead of a live sim frame, so this
tests server-side sampling stochasticity in isolation from the simulator.

Run with the RoboLab interpreter (has openpi_client installed):
  /workspace/RoboLab/.venv/bin/python research/tools/check_cosmos_diversity.py \
      --host localhost --port 8000 --k 5 \
      --instruction "Pick up the banana and place it in the bowl"
"""
from __future__ import annotations

import argparse
import json

import numpy as np
from openpi_client import websocket_client_policy


def build_fixed_request(instruction: str, seed: int = 12345) -> dict:
    rng = np.random.default_rng(seed)
    # Same panel geometry as Cosmos3Client: wrist 360x640 stacked over
    # left|right each resized to 180x320 -> total 540x640, uint8 RGB.
    wrist = rng.integers(0, 256, size=(360, 640, 3), dtype=np.uint8)
    left = rng.integers(0, 256, size=(180, 320, 3), dtype=np.uint8)
    right = rng.integers(0, 256, size=(180, 320, 3), dtype=np.uint8)
    image = np.concatenate((wrist, np.concatenate((left, right), axis=1)), axis=0)
    joint_position = np.zeros(7, dtype=np.float32)
    gripper_position = np.zeros(1, dtype=np.float32)
    return {
        "observation/image": image,
        "observation/joint_position": joint_position,
        "observation/gripper_position": gripper_position,
        "prompt": instruction,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--instruction", default="Pick up the banana and place it in the bowl")
    p.add_argument("--out", default=None, help="Optional path to write raw actions as .npy")
    a = p.parse_args()

    client = websocket_client_policy.WebsocketClientPolicy(a.host, a.port)
    print(f"[diversity-check] connected, server_metadata={client.get_server_metadata()}")

    request = build_fixed_request(a.instruction)
    actions = []
    for i in range(a.k):
        resp = client.infer(request)
        action = np.asarray(resp["action"])
        actions.append(action)
        print(f"[diversity-check] call {i}: action.shape={action.shape} "
              f"first_row={np.round(action[0], 4).tolist()}")

    actions = np.stack(actions, axis=0)  # (K, chunk, action_dim)

    # Pairwise L2 distance between full action chunks, and identity check.
    k = actions.shape[0]
    dists = np.zeros((k, k))
    identical_pairs = []
    for i in range(k):
        for j in range(i + 1, k):
            d = float(np.linalg.norm(actions[i] - actions[j]))
            dists[i, j] = dists[j, i] = d
            if np.allclose(actions[i], actions[j], atol=1e-6):
                identical_pairs.append((i, j))

    off_diag = dists[np.triu_indices(k, k=1)]
    summary = {
        "k": k,
        "action_shape": list(actions.shape[1:]),
        "pairwise_l2_mean": float(off_diag.mean()) if len(off_diag) else None,
        "pairwise_l2_min": float(off_diag.min()) if len(off_diag) else None,
        "pairwise_l2_max": float(off_diag.max()) if len(off_diag) else None,
        "identical_pairs": identical_pairs,
        "verdict": "DIVERSE" if len(identical_pairs) == 0 and (len(off_diag) == 0 or off_diag.min() > 1e-6) else "COLLAPSED/DUPLICATE",
    }
    print("[diversity-check] SUMMARY:", json.dumps(summary, indent=2))

    if a.out:
        np.save(a.out, actions)
        print(f"[diversity-check] raw actions saved to {a.out}")


if __name__ == "__main__":
    main()
