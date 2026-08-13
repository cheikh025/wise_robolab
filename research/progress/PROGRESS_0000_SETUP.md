# PROGRESS_0000 — M0 setup and benchmark integrity

## Purpose

- associated run record(s): `research/runs/RUN_0000_setup_clone.md`
- milestone: M0_SETUP
- question/decision: does the working RoboLab fork install and run correctly (CUDA-backed) on this machine, with a reproducible research branch and runbook, so later milestones (Cosmos, Robometer, IDM, WISE) have a trustworthy simulator/benchmark base?
- parent implementation/baseline: none — first milestone

## Exact code state

- repo: `https://github.com/cheikh025/RoboLab` (`/workspace/RoboLab`)
- branch: `wise/m0-setup`
- commit: `0aef241fb088ca21bb4ebd24448940ed56620d17`
- diff summary: 1-line patch in `examples/run_empty.py` (`save_videos=False` -> `True` in the `run_empty_episode(...)` call), matching bootstrap-note guidance and independently re-verified against current source.

## Environment

- system-info artifact: not captured via `research/tools/capture_system_info.py` in this run (recorded manually in `RUNBOOK.md` instead — the tool should be run and attached in a later pass for full provenance)
- interpreter(s): `/workspace/RoboLab/.venv/bin/python` (3.11.15)
- GPU/driver/CUDA: 2x A100-SXM4-80GB, driver 580.95.05 (R580), CUDA 13.0
- key package versions: `torch==2.7.0+cu128`, Isaac Sim 5.0.0, Isaac Lab 2.2.0, `robolab==0.2.1`

## Configuration

- Cosmos checkpoint/revision: n/a
- Robometer checkpoint/revision: n/a
- IDM checkpoint/config if applicable: n/a
- RoboLab task(s): `BananaInBowlTask`
- num envs / runs: 1 env / 1 episode, 100 steps (random actions)
- candidate budget K: n/a
- action prefix: n/a
- seeds/randomness: env default seed=0; not a scored comparison
- score/calibration/fusion settings: n/a

## Commands

```bash
git lfs install
cd /workspace && git clone https://github.com/cheikh025/RoboLab.git && cd RoboLab
git remote add upstream https://github.com/NVlabs/RoboLab.git && git fetch upstream
git checkout -b wise/m0-setup

uv venv --python 3.11 && source .venv/bin/activate
uv sync --extra isaac50
export OMNI_KIT_ACCEPT_EULA=Y

# bare-container fix (see RUNBOOK.md "Known failures")
curl -s -X POST http://localhost:11111/capabilities/provision -H "Content-Type: application/json" \
  -d '{"inline_yaml": "version: 1\napt_packages:\n  - libatomic1\n  - libegl1\n  - libgl1\n  - libglu1-mesa\n  - libglx0\n  - libgomp1\n  - libsm6\n  - libxi6\n  - libxrandr2\n  - libxt6\n  - libglib2.0-0\n  - libnghttp2-14\n  - ca-certificates\n  - curl\n  - unzip\n  - libx11-dev\n  - tree\n  - wget\n"}'

uv run pytest tests/ -q
sed -i 's/save_videos=False)/save_videos=True)/' examples/run_empty.py
uv run python examples/run_empty.py --task BananaInBowlTask --headless --num-steps 100
```

## What happened

- runtime: ~16 minutes end to end (clone, install, lib fix, pytest, smoke run)
- peak VRAM when useful: not sampled
- failures/warnings: one benign Warp/CUDA driver-entry-point warning during `run_empty.py` boot (R580 driver, not the documented R590 failure mode); benign `omni.usd` unresolved-reference warnings for an unrelated scene (`ladle_pot.usda`) during startup scene validation. Neither affected correctness of the executed task.
- output paths: `/workspace/RoboLab/output/run_empty_env/BananaInBowlTask/{empty_0_numsteps100.mp4,env_cfg.json,log_0_env0.json}`, `/workspace/RoboLab/output/run_empty_env/episode_results.jsonl`

## Evidence

### RoboLab outcome

- success: n/a (random-action wiring smoke test) — `episode_results.jsonl`: `success=false, score=0.0` as expected for random actions
- task-level results: 1280x720 h264 video (6.67s, 100 steps @ ~15fps observation camera) confirms the sim renders and steps correctly; subtask state machine (`object_grabbed`, `object_in_container`) confirms the success-predicate path is wired and observable

### Candidate/selector evidence

- n/a for M0

### Robometer evidence

- n/a for M0

### IDM evidence

- n/a for M0

## Decision

- `MILESTONE_PASS`
- reason: all M0 exit criteria satisfied on measured (not merely plausible) evidence — fork/upstream/branch recorded, exact stack captured, CUDA-backed test suite passes (160/160, 0 skipped), one headless episode completes with expected artifacts, control-rate (15Hz) and timeout (50s) semantics confirmed from this run's own `env_cfg.json`, runbook filled with verified commands (including two machine-specific traps not in the bootstrap notes: no sudo, and `uv`'s python-install-dir permissions).
- next action: proceed to M1 — `/verify-cosmos-robolab` (RUN_0001), using the already-cloned and `uv sync`'d `/workspace/cosmos-framework` (verified interpreter: Python 3.13.13, torch 2.10.0+cu130).

## Reproducibility checklist

- [x] exact commit recorded
- [x] exact commands recorded
- [x] revisions/checkpoints recorded
- [x] output artifacts preserved
- [x] no benchmark semantics silently changed (only infra patch: enabling existing video-writing capability, per CLAUDE.md's explicit allowance)
