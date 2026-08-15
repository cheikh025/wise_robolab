#!/usr/bin/env python3
"""Consistency-Consensus baseline (M-consensus): external, independent of WISE.

Implements the deployable test-time selection strategy from "Is the Future
Compatible? Diagnosing Dynamic Consistency in World Action Models"
(arXiv:2605.07514): sample K candidates from the same context, build a
consensus by averaging their predicted-future latents, score each candidate
by closeness to that consensus, and execute the winner's own action.

This is cited from the paper, not derived from anything WISE-specific. It is
one of the benchmark table's rows (`K=4 consensus`), evaluated purely as an
outside comparison point against `K=4 wise` and the individual r_exec / r_cons
/ r_task ablations -- it shares no code path with research/METHOD.md's WISE
score. In particular:

  - It scores CANDIDATES AGAINST EACH OTHER (mean of the K predicted-future
    latents), never against a real post-execution observation -- that would
    be the paper's other, non-deployable "Consistency-Exploring" variant,
    which needs environment resets and is not implemented here.
  - It executes the WINNING CANDIDATE'S OWN Cosmos-generated action, not an
    IDM-inferred one. Cosmos3-Edge-Policy-DROID is a joint-prediction WAM in
    the paper's taxonomy (it emits an observation and an action from one
    call, like the paper's Cosmos-Policy backbone) -- our IDM plays no role
    in this baseline at all. Contrast with r_cons (research/METHOD.md),
    which runs the IDM on the dream and compares the INFERRED action to
    Cosmos's own action; this baseline never touches the IDM.

Latent source: the raw pre-decode `vision_latent` field added to
action_policy_server_robolab.py's response (same tensor the model already
computes internally for `--decode-video`, exposed instead of only being used
to render RGB). Using the model's own latent avoids a wasteful decode-then-
re-encode round trip and is the most faithful match to the paper's "VAE
latent space" description, which does not name a specific external VAE.

Requires the policy server launched with `--decode-video` (that flag is what
makes `pred_vision_latent` get computed at all -- see
action_policy_server_robolab.py:617-624).

Run as a live smoke test (same wire format as RoboLab's
policies/cosmos3/client.py / research/tools/check_cosmos_diversity.py),
with the RoboLab interpreter (has openpi_client installed):

  /workspace/RoboLab/.venv/bin/python research/tools/consensus_baseline.py \
      --host localhost --port 8000 --k 4 \
      --instruction "Pick up the banana and place it in the bowl"
"""
from __future__ import annotations

import argparse
import json

import numpy as np

# Paper's default (Section 3.1): exp(-alpha * MSE_in_latent_space). Tuned to
# their own VAE's latent scale, not ours -- treat as a starting point only.
# Before trusting selected_index on real data, histogram mse_to_consensus
# across a held-out batch of candidates and re-derive alpha so that
# consistency_scores actually spreads across (0, 1] instead of saturating at
# one extreme (a symptom of alpha being wrong for this VAE's latent
# magnitude, not of the method being broken).
DEFAULT_ALPHA = 0.1


def select_consensus(candidates: list[dict], alpha: float = DEFAULT_ALPHA) -> dict:
    """Consistency-Consensus selection over K candidates from one decision point.

    candidates: list of K dicts, each with:
      - "action": (T, D) np.ndarray, the candidate's own Cosmos-generated action chunk
      - "vision_latent": (C, T, H, W) np.ndarray, the candidate's raw predicted-future latent
    All candidates must share the same latent shape (same context, same model).

    Returns selection + full diagnostics (nothing is hidden so a run can be
    audited after the fact, matching this project's convention in
    research/METHOD.md's "Store raw and calibrated values" and r_exec.py's
    all-subscores-returned style).
    """
    if not candidates:
        raise ValueError("at least one candidate is required")

    # The server returns vision_latent with a leading unit batch dim --
    # observed live as (1, C, T, H, W), e.g. (1, 48, 9, 33, 40) for a
    # 528x640 dream (H,W match the VAE's ~16x spatial downsampling: 528/16=33,
    # 640/16=40) -- squeeze down to plain (C,T,H,W) before use. Squeezing
    # defensively (any number of leading size-1 dims) rather than a single
    # fixed [0] index, so this keeps working if the server's own leading-dim
    # convention changes.
    def _squeeze_leading(latent: np.ndarray) -> np.ndarray:
        latent = np.asarray(latent)
        while latent.ndim > 4:
            if latent.shape[0] != 1:
                raise ValueError(f"unexpected vision_latent shape {latent.shape}, cannot squeeze to (C,T,H,W)")
            latent = latent[0]
        return latent

    latents = np.stack([_squeeze_leading(c["vision_latent"]).astype(np.float64) for c in candidates], axis=0)  # (K,C,T,H,W)
    k = latents.shape[0]

    consensus = latents.mean(axis=0)  # (C,T,H,W) -- Eq: obar = (1/N) sum_j ohat^(j)
    mse_to_consensus = ((latents - consensus[None]) ** 2).mean(axis=(1, 2, 3, 4))  # (K,)
    consistency_scores = np.exp(-alpha * mse_to_consensus)  # (K,)

    # Winner-take-all (not a weighted blend of actions): the paper found
    # averaging actions directly is wrong when the action space has
    # nonlinear/manifold components (rotations, poses) -- see the
    # Table-4-equivalent ablation in the paper. We always execute one
    # candidate's own complete action chunk.
    best_idx = int(np.argmax(consistency_scores))

    # Background-collapse diagnostic (paper Section on "background collapse" /
    # Figure 4): latent change magnitude within each candidate's own
    # trajectory. A candidate can win by consensus agreement while still
    # being a near-static, information-free dream -- this flags that case
    # rather than silently trusting a high consistency score. Not used to
    # veto the selection here (the paper's own fix is only partial and
    # explicitly left as future/training-time work); logged for analysis.
    delta_z = np.array([float(((lat[:, -1] - lat[:, 0]) ** 2).mean()) for lat in latents])

    return {
        "k": k,
        "alpha": alpha,
        "selected_index": best_idx,
        "selected_action": candidates[best_idx]["action"],
        "consistency_scores": consistency_scores.tolist(),
        "mse_to_consensus": mse_to_consensus.tolist(),
        "delta_z": delta_z.tolist(),
    }


def sample_k_candidates(client, request: dict, k: int) -> list[dict]:
    """Call the policy server k times with the SAME context (no sim stepping
    between calls -- same pattern as check_cosmos_diversity.py's diversity
    probe), returning the raw {action, vision_latent} needed by
    select_consensus. Requires the server to have been launched with
    --decode-video, or response["vision_latent"] will be absent.
    """
    candidates = []
    for i in range(k):
        response = client.infer(request)
        if "vision_latent" not in response:
            raise RuntimeError(
                "server response has no 'vision_latent' -- launch the policy server with "
                "--decode-video (see action_policy_server_robolab.py)"
            )
        candidates.append(
            {
                "action": np.asarray(response["action"]),
                "vision_latent": np.asarray(response["vision_latent"]),
            }
        )
        print(f"[consensus] candidate {i}: action.shape={candidates[-1]['action'].shape} "
              f"vision_latent.shape={candidates[-1]['vision_latent'].shape}")
    return candidates


def main() -> None:
    from openpi_client import websocket_client_policy

    p = argparse.ArgumentParser()
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--k", type=int, default=4)
    p.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    p.add_argument("--instruction", default="Pick up the banana and place it in the bowl")
    args = p.parse_args()

    # Fixed synthetic observation, same panel geometry as
    # check_cosmos_diversity.py/Cosmos3Client._pack_request: wrist 360x640
    # stacked over left|right each 180x320 -> 540x640 uint8 RGB. Swap this
    # for a real RoboLab observation once wired into the full K-candidate
    # harness; this script's job is to validate the consensus mechanism
    # against a live server in isolation first.
    rng = np.random.default_rng(12345)
    wrist = rng.integers(0, 256, size=(360, 640, 3), dtype=np.uint8)
    left = rng.integers(0, 256, size=(180, 320, 3), dtype=np.uint8)
    right = rng.integers(0, 256, size=(180, 320, 3), dtype=np.uint8)
    image = np.concatenate((wrist, np.concatenate((left, right), axis=1)), axis=0)
    request = {
        "observation/image": image,
        "observation/joint_position": np.zeros(7, dtype=np.float32),
        "observation/gripper_position": np.zeros(1, dtype=np.float32),
        "prompt": args.instruction,
    }

    client = websocket_client_policy.WebsocketClientPolicy(args.host, args.port)
    print(f"[consensus] connected, server_metadata={client.get_server_metadata()}")

    candidates = sample_k_candidates(client, request, args.k)
    result = select_consensus(candidates, alpha=args.alpha)
    print("[consensus] SUMMARY:", json.dumps({k: v for k, v in result.items() if k != "selected_action"}, indent=2))
    print(f"[consensus] selected candidate {result['selected_index']}, "
          f"action.shape={result['selected_action'].shape}")


if __name__ == "__main__":
    main()
