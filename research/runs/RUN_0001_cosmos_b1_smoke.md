# RUN_0001 — Cosmos3-Edge-Policy-DROID B=1 smoke through RoboLab

## Identity

- status: `COMPLETED`
- run class: `validation`
- milestone: M1_COSMOS
- associated progress report: research/progress/PROGRESS_0001_COSMOS.md (to be created)
- date/time: 2026-08-12 (start ~07:15Z)
- operator/agent: Claude Code (autonomous /goal run)

## Purpose

- exact question this run answers: does the frozen `nvidia/Cosmos3-Edge-Policy-DROID` checkpoint serve correctly through cosmos-framework's RoboLab policy server, and does the unmodified RoboLab `policies/cosmos3` client run one full episode end-to-end against it (request -> inference -> action -> env step -> episode output)?
- pass/fail criterion: server reports `ready` with the Edge checkpoint's config line (chunk=32, fps=15.0, action_dim=8, action_space=joint_pos); client connects; one `BananaInBowlTask` episode with `--num-envs 1 --headless` completes without a traceback and writes `episode_results.jsonl` + video.
- why this task/data budget is sufficient for this validation: M1 B=1 wiring smoke — 1 task, 1 env, 1 episode, per CLAUDE.md validation-budget discipline. Diversity/video-retention/baseline-measurement are separate, later steps in this same milestone (see M1 skill), each getting their own run record.

## Code state

- RoboLab repo: `/workspace/RoboLab`, branch `wise/m0-setup`, commit `4ab19bf` (HEAD after M0 uv.lock commit)
- branch: `wise/m0-setup` (continuing on same branch; will rename/tag at M1 close if warranted)
- commit: `4ab19bf...` (see RUNBOOK.md for full hash)
- relevant uncommitted diff: none for this specific run (using stock `policies/cosmos3/{client,run}.py`)
- upstream revision if relevant: unchanged from M0 (`97bc1e766300a8c95656067ecb81e267e7e11823`)
- Cosmos/cosmos-framework revision: `/workspace/cosmos-framework`, commit `a98dec05aa93ff6e2ebab2f38b590b86fe84f757` (HEAD at clone time, 2026-08-12)
- Robometer revision: n/a for this run
- IDM/WISE code revision: n/a for this run

## Machine and environments

- host/GPU: same box as M0 — 2x A100-SXM4-80GB, driver 580.95.05, CUDA 13.0
- driver/CUDA: 580.95.05 / 13.0
- Isaac Sim / Isaac Lab: 5.0.0 / 2.2.0 (unchanged from M0)
- RoboLab interpreter: `/workspace/RoboLab/.venv/bin/python` (3.11.15)
- Cosmos interpreter: `/workspace/cosmos-framework/.venv/bin/python` (3.13.13, torch 2.10.0+cu130) — verified against bootstrap notes' known-good check
- Robometer interpreter: n/a for this run
- IDM interpreter: n/a for this run
- key package versions: cosmos-framework torch 2.10.0+cu130; RoboLab torch 2.7.0+cu128. Two isolated envs, per CLAUDE.md environment discipline.

## Setup from a clean state

```bash
# server side (cosmos-framework already cloned+installed in M0 prep)
cd /workspace/cosmos-framework
export LD_LIBRARY_PATH=
export HF_HOME=/workspace/.hf_home
export HF_HUB_DISABLE_XET=1
/workspace/cosmos-framework/.venv/bin/python -m cosmos_framework.scripts.action_policy_server_robolab \
  --checkpoint-path nvidia/Cosmos3-Edge-Policy-DROID \
  --port 8000 \
  --format-prompt-as-json True

# client side (RoboLab)
cd /workspace/RoboLab
source .venv/bin/activate
export OMNI_KIT_ACCEPT_EULA=Y
uv run python policies/cosmos3/run.py --task BananaInBowlTask --num-envs 1 --headless
```

Required environment variables (names and non-secret values only):

```bash
LD_LIBRARY_PATH=            # blank — deliberate, see bootstrap notes; avoids Isaac Sim libs shadowing cosmos-framework's CUDA libs
HF_HOME=/workspace/.hf_home
HF_HUB_DISABLE_XET=1        # works around a known hf-xet hex-hash bug on guardrail download
OMNI_KIT_ACCEPT_EULA=Y
```

Flag names verified against this checkout's actual `--help` output (bootstrap notes used `--checkpoint_path` with an underscore; current tyro CLI exposes `--checkpoint-path` with a dash — both may work via tyro's normalization, but recording the verified form).

## Models and data

- Cosmos checkpoint + exact revision: `nvidia/Cosmos3-Edge-Policy-DROID`, revision=`main` (default `--hf-revision`)
- Robometer checkpoint + exact revision: n/a for this run
- IDM checkpoint + exact revision: n/a for this run
- DROID dataset release/split: n/a for this run
- other inputs/assets: RoboLab `BananaInBowlTask` scene assets (already verified present in M0)

## RoboLab / experiment configuration

- task(s): `BananaInBowlTask`
- exact instruction(s) when relevant: env-provided default instruction (expect "Pick up the banana and place it in the bowl", per M0)
- num envs: 1
- num runs / episodes: 1
- seeds/randomness: server `--seed 0`, `--deterministic-seed False` (default) — repeated same-context calls should differ; not exercised in this smoke run (single episode, single pass through the policy)
- simulator/physics stack: Isaac Sim 5.0.0 / Isaac Lab 2.2.0, unchanged from M0
- episode timeout semantics: unchanged from M0 (`episode_length_s=50`, 15Hz -> ~750 steps); `run.py` uses `robolab/eval/runner.py`'s default episode length/step budget rather than `run_empty.py`'s explicit `--num-steps`
- candidate budget K: 1 (B=1 baseline by definition)
- action horizon/prefix: server chunk=32 @ 15Hz conditioning fps; client `OPEN_LOOP_HORIZON=32` (executes the full chunk before re-querying)
- Cosmos generation settings: guidance=3.0, num_steps=4 (denoising steps), sampler=unipc, shift=5.0 (all defaults)
- Robometer view/scalarization: n/a
- IDM preprocessing/config: n/a
- `r_exec` config: n/a
- calibration/fusion config: n/a

## Exact commands

```bash
# terminal/process 1 — server
cd /workspace/cosmos-framework
export LD_LIBRARY_PATH=
export HF_HOME=/workspace/.hf_home
export HF_HUB_DISABLE_XET=1
/workspace/cosmos-framework/.venv/bin/python -m cosmos_framework.scripts.action_policy_server_robolab \
  --checkpoint-path nvidia/Cosmos3-Edge-Policy-DROID --port 8000 --format-prompt-as-json True

# terminal/process 2 — client
cd /workspace/RoboLab
source .venv/bin/activate
export OMNI_KIT_ACCEPT_EULA=Y
uv run python policies/cosmos3/run.py --task BananaInBowlTask --num-envs 1 --headless
```

## Expected outputs

- result directory: `/workspace/RoboLab/output/<timestamp>_cosmos3/`
- logs: `log_0_env0.json`
- videos/dreams: sensor/viewport video per `--video-mode` default (`all`); no Cosmos dream video yet (decode-video not enabled in this run — that is a separate follow-up run)
- metrics JSON: `episode_results.jsonl`
- checkpoints: n/a (server downloads Cosmos3-Edge-Policy-DROID + Cosmos-Guardrail1 to `$HF_HOME`)
- other artifacts: `env_cfg.json`

## Execution result

- start time: 2026-08-12T07:10Z (server launch) / 2026-08-12T07:30:46Z (episode start, per output dir timestamp)
- end time: 2026-08-12T07:31:53Z (episode complete; server checkpoint downloads took ~19 min: 07:10-07:29)
- wall time: episode itself: 66.86s wall (`wall_total_s` in results); server cold-start (checkpoint downloads + model load): ~19 min one-time cost
- peak VRAM / throughput if relevant: not sampled; policy inference averaged 167.5ms/call, env step averaged 246.4ms/step, 2.32 it/s overall
- exit status: 0 (client); server still running (long-lived process)
- warnings/errors: (1) first attempt failed with `ModuleNotFoundError: No module named 'openpi_client'` — RoboLab's `pyproject.toml` does not declare this dependency (matches bootstrap notes' finding); fixed by `uv pip install --no-cache-dir --no-deps "openpi-client @ git+https://github.com/xuningy/openpi@aa6420561529593114160d05e5ad155792b272f3#subdirectory=packages/openpi-client"` into `/workspace/RoboLab/.venv` (note: `.venv/bin/python -m pip` doesn't work — this uv-managed venv has no pip; used `uv pip install` instead). Pinned commit re-verified as current `xuningy/openpi` main HEAD before installing. (2) One transient issue during server boot: a `hf download` sub-process for `Cosmos-Guardrail1` appeared to hang on a lock file for >200s in the captured stdout; cross-checking `debug.log` (which is not delayed the same way stdout capture was) showed it had actually progressed already — not a real hang, just delayed stdout buffering. (3) Same benign `Warp CUDA error: cuDeviceGetUuid` warning as M0, no impact. (4) Guardrail auxiliary checkpoints (`Qwen3Guard-Gen-0.6B`, `Wan2.2` VAE) were downloaded implicitly and are not mentioned in the bootstrap notes — record them here for future reproduction.

## Observed evidence

- validation/benchmark result: **PASS**. Server reports `ready domain='droid_lerobot' resolution='480' action_space=joint_pos action_dim=8 chunk=32 history=1 use_state=True image=540x640 fps=15.0 guidance=3.0 num_steps=4 shift=5.0 seed=0 deterministic_seed=False` — matches bootstrap notes' known-good line exactly. `/healthz` returns `OK`. Server received a well-formed JSON-structured prompt (`format_prompt_as_json=True` confirmed working: `{"cinematography": {...}, "actions": [{"time": "0:00-0:02", "description": "Pick up the banana and place it in the bowl."}], "duration": "2s", "fps": 15.0, "resolution": {"H": 544, "W": 736}, ...}`) and ran UniPC diffusion sampling (shift=5.0, num_steps=4) as configured.
- task-level result: `BananaInBowlTask_0`, 1 episode, **success=true, score=1.0**, completed in 155/750 steps (10.33s sim time), reason: "Completed subtask 'pick_and_place' 1/1", event `TARGET_OBJECT_DROPPED: 1`. This is a genuine B=1 Cosmos3-Edge policy success on this task/seed — not a random-action smoke test.
- candidate diversity: not measured in this run (RUN_0002)
- Robometer: n/a
- IDM: n/a
- WISE: n/a
- artifact paths:
  - `/workspace/RoboLab/output/2026-08-12_07-30-46_cosmos3/BananaInBowlTask/Pick_up_the_banana_and_place_it_in_the_bowl_0.mp4` (sensor/observation video)
  - `/workspace/RoboLab/output/2026-08-12_07-30-46_cosmos3/BananaInBowlTask/Pick_up_the_banana_and_place_it_in_the_bowl_0_viewport.mp4`
  - `/workspace/RoboLab/output/2026-08-12_07-30-46_cosmos3/BananaInBowlTask/run_0.hdf5`
  - `/workspace/RoboLab/output/2026-08-12_07-30-46_cosmos3/BananaInBowlTask/log_0_env0.json`
  - `/workspace/RoboLab/output/2026-08-12_07-30-46_cosmos3/BananaInBowlTask/env_cfg.json`
  - `/workspace/RoboLab/output/2026-08-12_07-30-46_cosmos3/episode_results.jsonl`

## Outcome

- pass/fail: **PASS**
- what was proven: the Edge checkpoint (not Nano) is verifiably loaded and serving; observation/action wire format between RoboLab's stock `policies/cosmos3` client and cosmos-framework's server agree; action space is `joint_pos`, 8-D (7 joints + gripper), chunk=32 @ 15Hz, matching the DROID env's control rate measured in M0; one full episode runs end to end through the normal (unmodified) client and produces a real task success.
- what was **not** proven: native dream/rollout video retention (video field is returned by the server when `--decode-video` is set, but the stock client discards it — separate patch needed, RUN_0003); same-context candidate diversity (RUN_0002); a statistically broader B=1 baseline (n=1 here is a wiring+first-baseline-datapoint result, not a confirmation-grade measurement — consistent with CLAUDE.md's validation-budget discipline, which explicitly reserves broader fixed panels for M7).
- next action: RUN_0002 (candidate diversity), then RUN_0003 (video retention patch).

## Exact rerun recipe

From a clean checkout/machine with M0 already done:

```bash
cd /workspace/cosmos-framework
export LD_LIBRARY_PATH= HF_HOME=/workspace/.hf_home HF_HUB_DISABLE_XET=1
/workspace/cosmos-framework/.venv/bin/python -m cosmos_framework.scripts.action_policy_server_robolab \
  --checkpoint-path nvidia/Cosmos3-Edge-Policy-DROID --port 8000 --format-prompt-as-json True &
# wait for ready line
cd /workspace/RoboLab && source .venv/bin/activate && export OMNI_KIT_ACCEPT_EULA=Y
uv run python policies/cosmos3/run.py --task BananaInBowlTask --num-envs 1 --headless
```

## Reproducibility checklist

- [x] exact commits/revisions recorded
- [x] exact environment/interpreters recorded
- [x] setup steps recorded
- [x] exact commands recorded
- [x] task/data budget recorded
- [x] seeds/randomness recorded
- [x] configs/model revisions recorded
- [x] outputs/artifacts recorded
- [x] no secrets recorded
- [x] failed run preserved if applicable (first attempt's `ModuleNotFoundError` documented inline above rather than a separate file, since it's the same run intent)
