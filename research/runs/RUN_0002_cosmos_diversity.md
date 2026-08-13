# RUN_0002 — Cosmos3-Edge same-context candidate diversity

## Identity

- status: `COMPLETED`
- run class: `validation`
- milestone: M1_COSMOS
- associated progress report: research/progress/PROGRESS_0001_COSMOS.md
- date/time: 2026-08-12 (~07:38Z)
- operator/agent: Claude Code (autonomous /goal run)

## Purpose

- exact question this run answers: with `deterministic_seed=False` (confirmed in the server's ready line), do K repeated inference requests carrying the *exact same* observation/state/instruction return genuinely different action chunks, or does the server silently collapse to K duplicates?
- pass/fail criterion: no pair of the K returned action chunks is (near-)identical (`np.allclose` at 1e-6), and pairwise L2 distances are non-trivially > 0.
- why this task/data budget is sufficient for this validation: this is a wiring/stochasticity check, not a benchmark — K=5 repeated calls against the already-running server, no sim involved. Per CLAUDE.md: "Before Best-of-K, take one fixed pre-execution context and request multiple candidates... Measure action pairwise distances."

## Code state

- RoboLab repo: `/workspace/RoboLab`, branch `wise/m0-setup`
- branch: `wise/m0-setup`
- commit: unchanged from RUN_0001 (no RoboLab code touched by this check — it talks to the server directly via `openpi_client`, bypassing `policies/cosmos3/client.py`)
- relevant uncommitted diff: new file `research/tools/check_cosmos_diversity.py` in the `wise_robolab` project (not RoboLab)
- upstream revision if relevant: unchanged
- Cosmos/cosmos-framework revision: unchanged, server from RUN_0001 still running (same process, same loaded checkpoint)
- Robometer revision: n/a
- IDM/WISE code revision: n/a

## Machine and environments

- host/GPU: same box, unchanged
- driver/CUDA: unchanged
- Isaac Sim / Isaac Lab: not used in this run (no sim, direct websocket call)
- RoboLab interpreter: `/workspace/RoboLab/.venv/bin/python` (used only for its `openpi_client` install — no RoboLab/Isaac modules imported)
- Cosmos interpreter: server side unchanged (already running from RUN_0001)
- Robometer interpreter: n/a
- IDM interpreter: n/a
- key package versions: unchanged

## Setup from a clean state

Requires the Cosmos3-Edge server from RUN_0001 already running on `localhost:8000`, and RoboLab's `.venv` with `openpi_client` installed (see RUN_0001).

```bash
cd /workspace/wise_robolab
/workspace/RoboLab/.venv/bin/python research/tools/check_cosmos_diversity.py \
  --host localhost --port 8000 --k 5 \
  --instruction "Pick up the banana and place it in the bowl"
```

## Models and data

- Cosmos checkpoint + exact revision: `nvidia/Cosmos3-Edge-Policy-DROID` (same loaded server instance as RUN_0001)
- Robometer checkpoint + exact revision: n/a
- IDM checkpoint + exact revision: n/a
- DROID dataset release/split: n/a
- other inputs/assets: synthetic fixed observation (deterministic RNG seed=12345 for the image panels; zeros for joint/gripper proprioception) — deliberately not a real sim frame, to isolate server-side sampling stochasticity from any simulator state

## RoboLab / experiment configuration

- task(s): n/a (no sim; instruction text only, matching `BananaInBowlTask`'s instruction for realism)
- exact instruction(s): "Pick up the banana and place it in the bowl" (sent verbatim K times, unchanged)
- num envs: n/a
- num runs / episodes: K=5 inference calls, 0 episodes
- seeds/randomness: request payload fixed via local RNG seed=12345 (same every call); server-side sampling uses its own advancing RNG (`seed=0` base, `deterministic_seed=False` per ready line) — this run measures exactly that server-side randomness
- simulator/physics stack: n/a
- episode timeout semantics: n/a
- candidate budget K: 5
- action horizon/prefix: full returned chunk (32 steps x 8 dims) compared as-is
- Cosmos generation settings: guidance=3.0, num_steps=4, sampler=unipc, shift=5.0 (server defaults, unchanged from RUN_0001)
- Robometer view/scalarization: n/a
- IDM preprocessing/config: n/a
- `r_exec` config: n/a
- calibration/fusion config: n/a

## Exact commands

```bash
cd /workspace/wise_robolab
/workspace/RoboLab/.venv/bin/python research/tools/check_cosmos_diversity.py \
  --host localhost --port 8000 --k 5 \
  --instruction "Pick up the banana and place it in the bowl" \
  --out /workspace/wise_robolab/research/runs/RUN_0002_actions.npy
```

## Expected outputs

- result directory: stdout summary (printed JSON) + optional `.npy` of raw actions
- logs: printed to stdout, captured in this run file
- videos/dreams: n/a
- metrics JSON: printed inline
- checkpoints: n/a
- other artifacts: `RUN_0002_actions.npy` (K x chunk x action_dim raw actions, for later re-analysis)

## Execution result

- start time: 2026-08-12T07:38Z
- end time: 2026-08-12T07:38Z (fast — 5 sequential inference calls, no sim)
- wall time: a few seconds
- peak VRAM / throughput if relevant: n/a (not sampled; server was idle apart from these 5 calls)
- exit status: 0
- warnings/errors: none

## Observed evidence

- validation/benchmark result: **PASS**. K=5 calls with byte-identical request payload (fixed synthetic image via seeded RNG, zero proprioception, unchanged instruction string) returned 5 distinct `(32, 8)` action chunks.
- task-level result: n/a (no sim)
- candidate diversity: pairwise L2 distances over full action chunks: mean=2.057, min=1.258, max=2.701. Zero identical pairs (`np.allclose` at 1e-6). First-row (first timestep) values also visibly differ across all 5 calls, e.g. joint-0 command ranges 0.0199-0.0463 across calls.
- Robometer: n/a
- IDM: n/a
- WISE: n/a
- artifact paths: `/workspace/wise_robolab/research/runs/RUN_0002_actions.npy` (raw `(5, 32, 8)` array)

## Outcome

- pass/fail: **PASS**
- what was proven: `deterministic_seed=False` genuinely produces diverse candidates from identical context — the server does not silently collapse repeated same-context requests to duplicates. This is the necessary precondition for Best-of-K (M3) and full WISE (M6) to constitute real test-time scaling rather than K wasted copies.
- what was **not** proven: diversity under a *real* sim observation (this run used a synthetic fixed image to isolate server-side stochasticity) — a live same-context K-request test during an actual episode is deferred to M3's Best-of-K implementation, where it's needed anyway for the candidate-generation hook. Also not proven: whether diversity is *useful* (i.e., whether it actually helps selection) — that's the M7 scientific question, not M1's.
- next action: RUN_0003 — retain native imagined rollout video (`--decode-video` + minimal client patch).

## Exact rerun recipe

```bash
# with the Cosmos3-Edge server already running on localhost:8000 (see RUN_0001)
cd /workspace/wise_robolab
/workspace/RoboLab/.venv/bin/python research/tools/check_cosmos_diversity.py \
  --host localhost --port 8000 --k 5 \
  --instruction "Pick up the banana and place it in the bowl"
```

## Reproducibility checklist

- [x] exact commits/revisions recorded
- [x] exact environment/interpreters recorded
- [x] setup steps recorded
- [x] exact commands recorded
- [x] task/data budget recorded
- [x] seeds/randomness recorded
- [x] configs/model revisions recorded
- [ ] outputs/artifacts recorded
- [x] no secrets recorded
- [ ] failed run preserved if applicable
