# RUN_0018 — WISE Best-of-K: r_cons-only selector test (M6 prep, using RUN_0009's v1 IDM)

## Identity

- status: `RUNNING`
- run class: `validation`
- milestone: M6_WISE_INTEGRATE (prep)
- associated progress report: research/progress/PROGRESS_0004_IDM.md (shared)
- date/time: 2026-08-12 (~22:33Z)
- operator/agent: Claude Code (autonomous /goal run, user-directed: "test best of k using the previous trained version of IDM and selector is consistency")

## Purpose

- exact question this run answers: does r_cons (IDM-vs-Cosmos co-generated-action agreement, computed via a newly-built cross-process scoring server wrapping RUN_0009's v1 IDM checkpoint) produce a meaningful, non-degenerate selection signal when used as the *sole* Best-of-K selector -- mirroring M3's Robometer-only test (RUN_0005), now for the second of the three WISE terms?
- pass/fail criterion: r_cons scores must discriminate between the K candidates at each decision (not saturate to identical/degenerate values) and the resulting `selected` index must not be trivially constant across all decisions (i.e. genuinely responsive to which candidate the IDM finds most self-consistent with Cosmos's own action, not an artifact of always picking index 0).
- why this task/data budget is sufficient for this validation: same task/K as M3 (`BananaInBowlTask`, K=3) for direct comparability; a single episode is enough to establish the selector is non-degenerate (the bar this run is checking), not to establish success-rate superiority (that is M7-lite's job with a larger panel).

## Code state

- repo: `wise_idm` @ commit `045c0e3` (v2 model, not used here) + new file `idm_server.py` (uncommitted at run start, committed after)
- repo: `RoboLab` @ branch `wise/m0-setup`, uncommitted diff to `policies/wise/bestofk_client.py` (new `IDMConsistencyScorer` class, `selector="consistency"` branch in `infer()`) and `policies/wise/run_bestofk.py` (`--idm-url` flag, `"consistency"` added to `--selector` choices)
- new file `/workspace/wise_idm/idm_server.py`: minimal FastAPI server wrapping RUN_0009's v1 `DroidIDM` checkpoint, following the exact same cross-process isolation pattern as `research/tools/robometer_server.py` (RoboLab is torch 2.7.0, wise_idm is torch 2.11.0 -- different runtimes, never imported directly into RoboLab's process). `/score_consistency` endpoint: takes the full dream panel (all 3 camera views, unlike Robometer's wrist-only crop -- the IDM was trained on all 3) + Cosmos's own co-generated action for that candidate, runs the IDM on the dream, denormalizes to radians, and returns `r_cons` (0.5*joint_cons + 0.5*gripper_cons): joint_cons = `exp(-mean_abs_normalized_joint_diff)` (normalized into the IDM's own per-joint standardized units, continuous, no hard reject -- matching `r_exec`'s established convention in this project), gripper_cons = thresholded binary agreement rate (per METHOD.md's explicit instruction to treat the gripper separately since its executed representation is discrete/thresholded).

## Machine and environments

- host/GPU: GPU0 (IDM server, ~negligible VRAM), GPU1 (Cosmos3-Edge server, ~16.4GB), Isaac Sim (RoboLab episode)
- IDM interpreter: `/workspace/wise_idm/.venv/bin/python` (idm_server.py)
- Cosmos interpreter: `/workspace/cosmos-framework/.venv/bin/python` (server, restarted fresh -- was stopped after M3 to free GPUs for IDM training)
- RoboLab interpreter: `/workspace/RoboLab/.venv/bin/python` (via `uv run`)

## Setup from a clean state

```bash
# 1. IDM r_cons server (wise_idm env)
cd /workspace/wise_idm && source .venv/bin/activate
uv pip install fastapi uvicorn python-multipart requests   # not previously installed in this venv
python3 idm_server.py --checkpoint checkpoints_500ep/best.pt --port 8101

# 2. Cosmos3-Edge server (cosmos-framework env) -- restarted, was stopped after M3
cd /workspace/cosmos-framework
export LD_LIBRARY_PATH= HF_HOME=/workspace/.hf_home HF_HUB_DISABLE_XET=1
CUDA_VISIBLE_DEVICES=1 /workspace/cosmos-framework/.venv/bin/python -m cosmos_framework.scripts.action_policy_server_robolab \
  --checkpoint-path nvidia/Cosmos3-Edge-Policy-DROID --port 8000 --format-prompt-as-json True --decode-video
```

Verified both servers end-to-end before the real episode: (1) `idm_server.py`'s `/health` returned the expected checkpoint metadata; (2) queried the live Cosmos server directly for one genuinely-paired (action, dream-video) sample and POSTed it to `/score_consistency` -- confirmed no crashes and a sane-shaped response (this test used a random-noise "observation" per the diversity-check request format, so the *value* of r_cons there was meaningless, only the plumbing was being verified).

## Models and data

- Cosmos checkpoint: `nvidia/Cosmos3-Edge-Policy-DROID` (same as M1/M3)
- IDM checkpoint: `/workspace/wise_idm/checkpoints_500ep/best.pt` (RUN_0009, v1 architecture, epoch 30/40, val_mean_joint_mae=0.06857) -- the best available checkpoint, explicitly per user direction to use "the previous trained version" (not the paused v2 redesign)
- task: `BananaInBowlTask`, instruction "Pick up the banana and place it in the bowl" (verbatim, same as M1/M3)

## RoboLab / experiment configuration

- task: `BananaInBowlTask`, num_envs=1, headless
- K: 3 (matching M3 exactly)
- selector: `consistency` (r_cons only, no Robometer/r_task, no r_exec -- single-term test, mirroring M3's Robometer-only test)
- seed: default (0, per env registration)

## Exact commands

```bash
cd /workspace/RoboLab && source .venv/bin/activate && export OMNI_KIT_ACCEPT_EULA=Y
uv run python policies/wise/run_bestofk.py --task BananaInBowlTask --num-envs 1 --headless --k 3 --selector consistency
```

## Expected outputs

- result directory: `/workspace/RoboLab/output/2026-08-12_22-33-59_wise_bestofk/BananaInBowlTask/`
- decision log: `wise_decisions.jsonl` (per-call k/selector/scores/selected/latency)
- dream videos: `dreams/dream_env0_call{NNN}_{cand{i}|selected{i}}.mp4`
- episode result: `episode_results.jsonl`

## Execution result

- start time: 2026-08-12T~22:33Z
- end time: TBD
- exit status: TBD

## Observed evidence

- Decision log (5 calls observed so far, episode still running):
  ```
  call=0 k=3 scores=[0.648, 0.644, 0.636] selected=0  gen_s=7.01 score_s=0.55
  call=1 k=3 scores=[0.648, 0.654, 0.644] selected=1  gen_s=6.82 score_s=0.70
  call=2 k=3 scores=[0.653, 0.630, 0.624] selected=0  gen_s=6.88 score_s=0.66
  call=3 k=3 scores=[0.654, 0.658, 0.668] selected=2  gen_s=6.86 score_s=0.70
  call=4 k=3 scores=[0.640, 0.648, 0.618] selected=1  gen_s=6.89 score_s=0.66
  ```
  Scores cluster in a ~0.62-0.67 band (not saturated at 0/1, not identical across candidates), and `selected` varies genuinely across calls (0,1,0,2,1) -- not a degenerate always-pick-index-0 pattern. Per-call latency: ~6.8-7.0s generation (K=3 Cosmos calls) + ~0.55-0.70s scoring (K=3 IDM calls) -- scoring is meaningfully faster than Robometer's (M3: ~1.7s for K=3), consistent with the IDM being a much smaller model (9M params vs Robometer-4B) than Robometer.
- artifact paths: `/workspace/RoboLab/output/2026-08-12_22-33-59_wise_bestofk/BananaInBowlTask/wise_decisions.jsonl`

## Outcome

- pass/fail: TBD (episode in progress -- non-degeneracy criterion already looks satisfied based on 5 calls, final episode success/step-count still pending)
- next action: TBD

## Reproducibility checklist

- [x] exact commits/revisions recorded (uncommitted diffs noted, will record final commits once episode completes)
- [x] exact environment/interpreters recorded
- [x] setup steps recorded
- [x] exact commands recorded
- [x] task/data budget recorded
- [x] seeds/randomness recorded
- [x] configs/model revisions recorded
- [ ] outputs/artifacts recorded
- [x] no secrets recorded
- [ ] failed run preserved if applicable
