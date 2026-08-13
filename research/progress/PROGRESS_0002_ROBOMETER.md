# PROGRESS_0002 — M2 Robometer-4B offline validation

## Purpose

- associated run record(s): `research/runs/RUN_0004_robometer_offline.md`
- milestone: M2_ROBOMETER_OFFLINE
- question/decision: does general `robometer/Robometer-4B`, scored offline (no policy-loop coupling), give a meaningful instruction-conditioned progress signal on RoboLab real trajectories and Cosmos3-Edge imagined dreams, sufficient to serve as `r_task` in WISE?
- parent implementation/baseline: M1 (Cosmos3-Edge B=1 + dream-video retention)

## Exact code state

- repo: `robometer` @ `/workspace/robometer`, commit `5b815254bf31ee1bea3753c3a2da9f9033736d9a`
- branch: none yet (no code changes to the robometer repo itself; scoring script lives in `wise_robolab/research/tools/score_robometer.py`)
- commit: n/a for robometer repo; `wise_robolab` project has the new script (uncommitted, this is a research-notes repo not under strict git discipline the same way as RoboLab)
- diff summary: environment fix only (`torchao` pinned to `<0.10`, resolved `0.9.0`, via `uv pip install` in the robometer venv — not a `pyproject.toml` change, so it will revert on a fresh `uv sync --extra robometer`; **record this as a required post-sync step** until/unless upstream robometer pins a compatible torchao itself)

## Environment

- system-info artifact: not separately captured
- interpreter(s): `/workspace/robometer/.venv/bin/python` (3.10.20, torch 2.8.0+cu128, `torchao==0.9.0` after fix)
- GPU/driver/CUDA: unchanged (2x A100-SXM4-80GB, driver 580.95.05, CUDA 13.0)
- key package versions: `transformers==4.57.6`, `torchao==0.9.0` (downgraded from the transitively-resolved `0.18.0`)

## Configuration

- Cosmos checkpoint/revision: `nvidia/Cosmos3-Edge-Policy-DROID` (video reused from M1's RUN_0003, not re-run)
- Robometer checkpoint/revision: `robometer/Robometer-4B`, default revision
- IDM checkpoint/config if applicable: n/a
- RoboLab task(s): `BananaInBowlTask` (1 episode, reused from RUN_0003)
- num envs / runs: 1 episode, 5 policy chunks, 3 views x 2 sources (dream/real) = 30 scoring calls
- candidate budget K: n/a (offline)
- action prefix: n/a
- seeds/randomness: n/a (deterministic inference)
- score/calibration/fusion settings: `r_task` scalarization = final-frame progress (`last`), per-frame curves retained for future re-scalarization

## Commands

```bash
export HF_HOME=/workspace/.hf_home HF_HUB_DISABLE_XET=1
/workspace/robometer/.venv/bin/hf download robometer/Robometer-4B
cd /workspace/robometer && uv pip install "torchao<0.10"   # environment fix, see below

cd /workspace/wise_robolab
/workspace/robometer/.venv/bin/python research/tools/score_robometer.py \
  --run-dir /workspace/RoboLab/output/2026-08-12_07-37-11_cosmos3/BananaInBowlTask \
  --sensor-video ".../Pick_up_the_banana_and_place_it_in_the_bowl_0.mp4" \
  --task "Pick up the banana and place it in the bowl" \
  --out research/runs/RUN_0004_robometer_progress.json
```

## What happened

- runtime: checkpoint download ~15 min (slowed significantly mid-download, network-bound not stuck); scoring ~2.5 min for model load + 30 calls
- peak VRAM when useful: not sampled live (see RUN_0004 for caveat)
- failures/warnings: real `ImportError` (torchao/torch version skew) on first attempt, root-caused and fixed (see below); benign HF model-type warning; seam auto-detector found 359 vs ratio-predicted 352 for all 5 dream clips (used detected value, per script design — worth another look, not fully resolved)
- output paths: `research/runs/RUN_0004_robometer_progress.json`

## Evidence

### RoboLab outcome

- success: reused from RUN_0003 (success=true, grasp at step 82, final success at step 141)
- task-level results: n/a (not re-run)

### Candidate/selector evidence

- candidate diversity: n/a
- raw `r_exec`: n/a (not yet implemented — M3/M6)
- raw `r_cons`: n/a (IDM not yet built — M4/M5)
- raw `r_task`: see Robometer evidence below — this run establishes it
- selected candidate behavior: n/a (no selector yet)

### Robometer evidence

- view: all three (wrist, left, right) scored independently, no compositing
- per-frame progress behavior: real trajectory rises monotonically on all 3 views from ~0.3-0.5 at chunk 0 to ~0.82-0.86 at chunk 4 (post-success), closely tracking the actual grasp (step 82)/success (step 141) event timeline. Dream trajectory matches closely on wrist and left (both reach >0.8 by the final chunk); dream-right matches well through chunk 3 then collapses to ~0.08 on the final chunk specifically — an isolated, informative anomaly (likely Robometer's trained "not the same task" escape firing on a degenerate final-chunk right-eye dream), not a general Robometer or Cosmos failure.
- scalarization: `last` (final-frame progress) chosen as the initial `r_task` scalar; full per-frame curves retained in the JSON for revisiting this choice without re-running inference

## Decision

- `MILESTONE_PASS`
- reason: at least one (in fact, effectively all three) real-video input/view path gives clearly meaningful, monotonic, event-timeline-correlated progress behavior — the M2 skill's pass bar. The one dream-view anomaly is documented as a real finding to carry into M5, not swept aside.
- next action: M3 — `/run-robometer-bestofk`. The environment fix (`torchao<0.10`) must be re-applied after any fresh `uv sync --extra robometer` until upstream pins it; documented in RUNBOOK.md's "Known failures" section.

## Reproducibility checklist

- [x] exact commit recorded
- [x] exact commands recorded
- [x] revisions/checkpoints recorded
- [x] output artifacts preserved
- [x] no benchmark semantics silently changed (purely offline scoring, no RoboLab/Cosmos runs in this milestone)
