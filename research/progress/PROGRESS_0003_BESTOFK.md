# PROGRESS_0003 — M3 Robometer-only Best-of-K

## Purpose

- associated run record(s): `research/runs/RUN_0005_bestofk.md`
- milestone: M3_ROBOMETER_BESTOFK
- question/decision: is the simplest serious test-time selector (K same-context Cosmos candidates, Robometer scores each imagined future, execute the paired action of the best) implemented correctly, with verified candidate integrity, before adding the IDM?
- parent implementation/baseline: M1 (B=1 Cosmos), M2 (Robometer offline validation)

## Exact code state

- repo: `https://github.com/cheikh025/RoboLab`
- branch: `wise/m0-setup`
- commit: `74d3090`
- diff summary: new `policies/wise/` package (+273 lines) — `BestOfKClient`, `RobometerScorer` (HTTP), `run_bestofk.py`. No changes to action/observation semantics or success predicates.

## Environment

- system-info artifact: not separately captured
- interpreter(s): RoboLab (3.11.15/torch 2.7.0+cu128), Cosmos server (3.13.13/torch 2.10.0+cu130), Robometer server (3.10.20/torch 2.8.0+cu128, now also serving HTTP on `127.0.0.1:8100`)
- GPU/driver/CUDA: unchanged
- key package versions: unchanged; new `research/tools/robometer_server.py` in the `wise_robolab` project (FastAPI wrapper, `fastapi`/`uvicorn` already present as robometer deps)

## Configuration

- Cosmos checkpoint/revision: `nvidia/Cosmos3-Edge-Policy-DROID` (server unchanged since RUN_0003, `--decode-video` required)
- Robometer checkpoint/revision: `robometer/Robometer-4B`
- IDM checkpoint/config if applicable: n/a
- RoboLab task(s): `BananaInBowlTask`
- num envs / runs: 1 env, 3 episodes (one per selector arm)
- candidate budget K: 3
- action prefix: full 32-step chunk of the selected candidate
- seeds/randomness: env seed=0; Cosmos server `deterministic_seed=False`; random-selector RNG seed=0
- score/calibration/fusion settings: single-term `r_task` only (Robometer `last`), no calibration/fusion yet (M6)

## Commands

```bash
export HF_HOME=/workspace/.hf_home
cd /workspace/wise_robolab && /workspace/robometer/.venv/bin/python research/tools/robometer_server.py --port 8100 &

cd /workspace/RoboLab && source .venv/bin/activate && export OMNI_KIT_ACCEPT_EULA=Y
uv run python policies/wise/run_bestofk.py --task BananaInBowlTask --num-envs 1 --headless --k 3 --selector robometer
uv run python policies/wise/run_bestofk.py --task BananaInBowlTask --num-envs 1 --headless --k 3 --selector random --seed 0
uv run python policies/wise/run_bestofk.py --task BananaInBowlTask --num-envs 1 --headless --k 3 --selector first
```

## What happened

- runtime: ~2.5 min per episode (5-8 policy decisions each, ~8-9s/decision for K=3 generate+score)
- peak VRAM when useful: not sampled
- failures/warnings: none beyond the standing benign Warp/CUDA warning
- output paths: `output/2026-08-12_08-{05:32,07:56,10:23}_wise_bestofk/`

## Evidence

### RoboLab outcome

- success: all 3 episodes succeeded
- task-level results: robometer-selected 134 steps; random-selected 182 steps; first-sample 253 steps (n=1/arm, suggestive not confirmatory)

### Candidate/selector evidence

- candidate diversity: re-confirmed live at every decision (action mean/std differ across all K=3 candidates every time)
- raw `r_exec`: n/a (not implemented — M6)
- raw `r_cons`: n/a (no IDM yet — M4/M5)
- raw `r_task`: Robometer `last` score per candidate, logged for all 19 decisions across 3 arms in `wise_decisions.jsonl` files
- selected candidate behavior: **verified exactly correct** for all three selector modes — robometer arm selects argmax every time (5/5), random arm matches argmax only by chance (2/6), first arm always selects index 0 (8/8) regardless of scores. Dream-file tags match the logged selection at every decision.

### Robometer evidence

- view: wrist-only (per M2 finding)
- per-frame progress behavior: rises across decisions within each episode, consistent with M2
- scalarization: `last` (final-frame progress), unchanged from M2

### IDM evidence

- n/a for M3

## Decision

- `MILESTONE_PASS`
- reason: selector is correct, stable, and compared against first-sample/random baselines under matched K-candidate generation, satisfying the M3 skill's explicit pass bar ("does not need to outperform on every small smoke panel to pass engineering validation"). Candidate integrity (no action/future mixing, no speculative execution, only the selected candidate ever stepped) is verified by direct cross-check of the decision log against saved artifact filenames, not merely asserted.
- next action: M4 — `/build-droid-idm`. The `RobometerScorer` HTTP pattern (minimal FastAPI wrapper around already-verified scoring code, called cross-process over HTTP) is a reusable template for wiring the IDM's `r_cons` term into the same selector in M6.

## Reproducibility checklist

- [x] exact commit recorded
- [x] exact commands recorded
- [x] revisions/checkpoints recorded
- [x] output artifacts preserved
- [x] no benchmark semantics silently changed
