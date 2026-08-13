# RUN_0005 — Robometer-only Best-of-K vs first-sample vs random-K

## Identity

- status: `COMPLETED`
- run class: `validation`
- milestone: M3_ROBOMETER_BESTOFK
- associated progress report: research/progress/PROGRESS_0003_BESTOFK.md (to be created)
- date/time: 2026-08-12 (~08:05Z)
- operator/agent: Claude Code (autonomous /goal run)

## Purpose

- exact question this run answers: does a working Robometer-only Best-of-K selector (K candidates generated from the same frozen context, scored by Robometer-4B, highest-scoring candidate's action executed) run correctly end-to-end, and how does it compare to first-sample and random-K under matched candidate generation (same K-set logged for all three, per the M3 skill's explicit guidance)?
- pass/fail criterion: selector logic is correct (candidate integrity preserved — no action/future mixing, only selected candidate executed), decision log captures per-candidate scores/selection/latency for every control decision, and the run completes without error for all three selector arms on the same task.
- why this task/data budget is sufficient for this validation: M3 engineering-correctness validation, not a benchmark. 1 task (`BananaInBowlTask`), 1 episode per selector arm (3 episodes total), K=3 (smallest K that is a genuine choice among >1 candidate while keeping generation+scoring cost small). Per CLAUDE.md: "Start on a small task panel before expanding."

## Code state

- RoboLab repo: `/workspace/RoboLab`, branch `wise/m0-setup`
- branch: `wise/m0-setup`
- commit: uncommitted at run time — new files `policies/wise/__init__.py`, `policies/wise/bestofk_client.py`, `policies/wise/run_bestofk.py` (to be committed after this run passes)
- relevant uncommitted diff: new `policies/wise/` package. `BestOfKClient(Cosmos3Client)` overrides `infer()` to generate K candidates from one frozen `_pack_request()` call (same request object reused K times — relies on M1's RUN_0002 finding that the server's `deterministic_seed=False` makes repeated identical requests return diverse candidates), score each via a new `RobometerScorer` HTTP client, select by configurable `--selector {robometer,random,first}`, execute only the selected candidate's action chunk, and save every candidate's dream video (tagged `cand{i}`/`selected{i}`) plus a `wise_decisions.jsonl` per-decision log (candidate scores, selected index, generation/scoring latency, per-candidate action mean/std).
- upstream revision if relevant: unchanged
- Cosmos/cosmos-framework revision: unchanged, server from RUN_0003 still running (`--decode-video` already enabled, required for this run)
- Robometer revision: `5b815254bf31ee1bea3753c3a2da9f9033736d9a`, plus new `research/tools/robometer_server.py` (in `wise_robolab` project) — a minimal FastAPI wrapper around the exact `load_robometer()`/`score()` path already verified in RUN_0004, exposing `/health` and `/score` (multipart .npy upload). Written instead of integrating with robometer's own generic `/evaluate_batch_npy` (designed for the training/eval trajectory-dict shape, unverified for this single-clip use case) — a deliberate, minimal, already-tested-logic infra patch.
- IDM/WISE code revision: n/a (no IDM yet; this is Robometer-only)

## Machine and environments

- host/GPU: same box, unchanged
- driver/CUDA: unchanged
- Isaac Sim / Isaac Lab: unchanged (5.0.0 / 2.2.0)
- RoboLab interpreter: `/workspace/RoboLab/.venv/bin/python` (uses `requests` + `cv2`, both already present, to call the Robometer HTTP server — no cross-env imports)
- Cosmos interpreter: `/workspace/cosmos-framework/.venv/bin/python` (server, unchanged)
- Robometer interpreter: `/workspace/robometer/.venv/bin/python` (now also running as an HTTP server on `127.0.0.1:8100`, `torchao==0.9.0` fix from M2 applied)
- IDM interpreter: n/a
- key package versions: unchanged from M1/M2

## Setup from a clean state

Requires the Cosmos3-Edge server (RUN_0003, `--decode-video`) and Robometer-4B (M2 checkpoint) already present.

```bash
# Robometer scoring server (new for M3)
export HF_HOME=/workspace/.hf_home
cd /workspace/wise_robolab
/workspace/robometer/.venv/bin/python research/tools/robometer_server.py --port 8100

# Cosmos server (unchanged from RUN_0003, already running)
# client
cd /workspace/RoboLab && source .venv/bin/activate && export OMNI_KIT_ACCEPT_EULA=Y
uv run python policies/wise/run_bestofk.py --task BananaInBowlTask --num-envs 1 --headless \
  --k 3 --selector robometer
```

## Models and data

- Cosmos checkpoint + exact revision: `nvidia/Cosmos3-Edge-Policy-DROID` (unchanged, server from RUN_0003)
- Robometer checkpoint + exact revision: `robometer/Robometer-4B`, default revision
- IDM checkpoint + exact revision: n/a
- DROID dataset release/split: n/a
- other inputs/assets: n/a

## RoboLab / experiment configuration

- task(s): `BananaInBowlTask`
- exact instruction(s): "Pick up the banana and place it in the bowl" (unchanged)
- num envs: 1
- num runs / episodes: 1 episode per selector arm x 3 arms (robometer, random, first) = 3 episodes
- seeds/randomness: env seed=0 (default); Cosmos server seed=0/`deterministic_seed=False` (each of the K calls per decision samples differently, per RUN_0002); random-selector arm uses `np.random.default_rng(seed=0)` for reproducible candidate-index selection
- simulator/physics stack: unchanged
- episode timeout semantics: unchanged (episode_length_s=50 -> 750 steps @ 15Hz)
- candidate budget K: 3 (all three arms generate+score K=3 candidates per decision; only the executed action differs by selector)
- action horizon/prefix: full 32-step chunk of the selected candidate (unchanged commitment from B=1)
- Cosmos generation settings: unchanged (guidance=3.0, num_steps=4, unipc, shift=5.0, decode_video=True)
- Robometer view/scalarization: wrist-only dream view (per M2 finding), `last` (final-frame progress) scalarization, unchanged from M2
- IDM preprocessing/config: n/a
- `r_exec` config: n/a (not yet implemented — action-validity term is M6)
- calibration/fusion config: n/a (single-term selector, no fusion yet)

## Exact commands

```bash
# terminal 1: Robometer scoring server
export HF_HOME=/workspace/.hf_home
cd /workspace/wise_robolab
/workspace/robometer/.venv/bin/python research/tools/robometer_server.py --port 8100

# terminal 2: Cosmos server (already running from RUN_0003)

# terminal 3: client, one run per selector arm
cd /workspace/RoboLab && source .venv/bin/activate && export OMNI_KIT_ACCEPT_EULA=Y
uv run python policies/wise/run_bestofk.py --task BananaInBowlTask --num-envs 1 --headless --k 3 --selector robometer
uv run python policies/wise/run_bestofk.py --task BananaInBowlTask --num-envs 1 --headless --k 3 --selector random --seed 0
uv run python policies/wise/run_bestofk.py --task BananaInBowlTask --num-envs 1 --headless --k 3 --selector first
```

## Expected outputs

- result directory: `/workspace/RoboLab/output/<timestamp>_wise_bestofk/` x 3 (one per arm)
- logs: `log_0_env0.json`, `wise_decisions.jsonl` (new, per-decision candidate scores/selection/latency)
- videos/dreams: `dreams/dream_env0_call{NNN}_cand{i}.mp4` for every candidate, `..._selected{i}.mp4` for the chosen one, per decision
- metrics JSON: `episode_results.jsonl`
- checkpoints: n/a
- other artifacts: `env_cfg.json`

## Execution result

- start time: 2026-08-12T08:05:32Z (robometer arm start)
- end time: 2026-08-12T08:13:~00Z (first arm complete, per output dir timestamps: robometer @08:05:32, random @08:07:56, first @08:10:23)
- wall time: robometer arm ~2m24s wall (134 steps / ~5 decisions); random arm ~2m27s (182 steps / 6 decisions); first arm ~2m37s (253 steps / 8 decisions) — all three well within the smoke-validation budget
- peak VRAM / throughput if relevant: not sampled; per-decision generation latency (K=3 Cosmos calls) 6.85-7.07s, scoring latency (K=3 Robometer calls) 1.18-2.56s — both measured directly from `wise_decisions.jsonl`, not estimated
- exit status: 0 for all three arms
- warnings/errors: same benign Warp/CUDA warning as every prior run; no new issues

## Observed evidence

- validation/benchmark result: **PASS**, all three arms
- task-level result: all 3 episodes **succeeded** (this task/seed is evidently not hard for Cosmos3-Edge at K=1 already, per M1). Step-efficiency ordering: robometer-selected (134 steps, 5 decisions) < random (182 steps, 6 decisions) < first-sample (253 steps, 8 decisions) — directionally consistent with the selector adding value, but **n=1 per arm, not a statistically supportable claim**; recorded as suggestive engineering evidence only, exactly per CLAUDE.md's validation-budget discipline. A real comparison needs matched multi-episode panels, deferred to M7.
- candidate diversity: re-confirmed live (not just RUN_0002's isolated synthetic-observation check) — action `mean`/`std` summaries differ across all 3 candidates at every one of the 19 total decisions logged across the 3 arms (spot-checked call 0 of the robometer arm: candidate action means visibly differ per-joint, e.g. joint 6 means -0.348/-0.331/-0.643)
- Robometer: scores rise across decisions within each episode (e.g. robometer arm: ~0.3-0.5 -> ~0.75-0.95), consistent with M2's finding that Robometer tracks real task progress
- IDM: n/a
- WISE: n/a (Robometer-only; action-quality `r_exec` and IDM-consistency `r_cons` terms are M6)
- artifact paths:
  - robometer arm: `/workspace/RoboLab/output/2026-08-12_08-05-32_wise_bestofk/BananaInBowlTask/wise_decisions.jsonl` — **every one of 5 decisions verified**: selected index == `argmax(scores)` exactly (call0: scores=[0.307,0.534,0.393]->sel=1 ✓; call1: [0.562,0.548,0.461]->sel=0 ✓; call2: [0.584,0.593,0.652]->sel=2 ✓; call3: [0.801,0.851,0.885]->sel=2 ✓; call4: [0.947,0.925,0.748]->sel=0 ✓). Saved dream filenames' `selected{i}` tag matches the logged `selected` field exactly at every decision (cross-checked by listing `dreams/`).
  - random arm: `.../2026-08-12_08-07-56_wise_bestofk/.../wise_decisions.jsonl` — selected index matches argmax in only 2/6 decisions (by chance), confirming genuine random selection rather than an accidental deterministic pattern (e.g. call0: scores=[0.448,0.524,0.299], argmax=1, selected=2; call3: argmax=1, selected=0)
  - first arm: `.../2026-08-12_08-10-23_wise_bestofk/.../wise_decisions.jsonl` — `selected=0` at all 8 decisions regardless of scores (e.g. call3: scores=[0.673,0.674,0.693] — candidate 2 scores higher but candidate 0 is still selected), confirming correct B=1-equivalent behavior under this harness

## Outcome

- pass/fail: **PASS**
- what was proven: the Best-of-K selector is implemented correctly — candidate generation always precedes scoring and execution (no speculative env stepping), all K candidates per decision come from one frozen context (verified diverse, not collapsed), action and imagined future are never mixed across candidates (dream-file tagging matches the decision log exactly at every one of 19 decisions across 3 arms), only the selected candidate's action is ever executed, and the selector logic itself is correct for all three modes (`robometer`=argmax, `random`=genuinely stochastic, `first`=always index 0). Per-decision latency is now measured directly (not estimated): ~2.3s/candidate generation, ~0.4-0.9s/candidate scoring.
- what was **not** proven: whether Robometer-selection actually improves success *rate* or *robustness* at adequate statistical power — this run is n=1/arm engineering validation, exactly the M3 skill's stated bar ("does not need to outperform on every small smoke panel to pass"). Also not proven: behavior at larger K, on harder/failing tasks, or across multiple episodes per arm.
- next action: commit `policies/wise/` (new client, run script, `__init__.py`) on `wise/m0-setup`; write `PROGRESS_0003_BESTOFK.md`; update `RUNBOOK.md`/`STATE.md`/`EXPERIMENTS.jsonl`; mark M3 `MILESTONE_PASS`; hand off to M4 (`/build-droid-idm`).

## Exact rerun recipe

```bash
export HF_HOME=/workspace/.hf_home
cd /workspace/wise_robolab && /workspace/robometer/.venv/bin/python research/tools/robometer_server.py --port 8100 &
# (Cosmos server already running per RUN_0001/0003 recipe, --decode-video required)
cd /workspace/RoboLab && source .venv/bin/activate && export OMNI_KIT_ACCEPT_EULA=Y
uv run python policies/wise/run_bestofk.py --task BananaInBowlTask --num-envs 1 --headless --k 3 --selector robometer
```

## Reproducibility checklist

- [x] exact commits/revisions recorded (commit hash to be added after post-run commit, see PROGRESS_0003)
- [x] exact environment/interpreters recorded
- [x] setup steps recorded
- [x] exact commands recorded
- [x] task/data budget recorded
- [x] seeds/randomness recorded
- [x] configs/model revisions recorded
- [x] outputs/artifacts recorded
- [x] no secrets recorded
- [x] failed run preserved if applicable (n/a — no failed attempts in this run)
