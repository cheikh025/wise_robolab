# RUN_0004 — Robometer-4B offline validation on RoboLab sensor + Cosmos dream video

## Identity

- status: `COMPLETED`
- run class: `validation`
- milestone: M2_ROBOMETER_OFFLINE
- associated progress report: research/progress/PROGRESS_0002_ROBOMETER.md (to be created)
- date/time: 2026-08-12 (~07:50Z)
- operator/agent: Claude Code (autonomous /goal run)

## Purpose

- exact question this run answers: does general `robometer/Robometer-4B`, run offline (no policy loop coupling), produce meaningful instruction-conditioned progress signal on (a) RoboLab's real sensor video and (b) Cosmos3-Edge's imagined dream video, for the exact `BananaInBowlTask` episode already produced in M1?
- pass/fail criterion: at least one of {wrist, left, right} views shows progress that is not universally flat/NaN/zero, and ideally trends upward toward the episode's actual success point (per `log_0_env0.json` event timeline) on the real sensor video. Dream-video behavior is recorded regardless of whether it matches (that comparison is itself the point of M5's IDM/consistency work later).
- why this task/data budget is sufficient for this validation: single already-completed episode (RUN_0003, success=true, 141 steps, 5 policy calls) scored across 3 camera views x {dream, real} = 6 curves. This is exactly the M2 skill's offline-validation scope — no new sim/policy runs needed, reusing M1's artifacts.

## Code state

- RoboLab repo: unchanged, `/workspace/RoboLab` @ `wise/m0-setup` `16513ca` (source of the video artifacts, not executed in this run)
- branch: n/a (Robometer is a separate repo, not on a research branch yet — will create one before any code changes)
- commit: `/workspace/robometer` @ `5b815254bf31ee1bea3753c3a2da9f9033736d9a` (HEAD at clone time)
- relevant uncommitted diff: new scoring script added to `wise_robolab` project: `research/tools/score_robometer.py` (not part of the robometer repo itself)
- upstream revision if relevant: n/a (robometer is the working repo itself, no separate upstream tracked yet)
- Cosmos/cosmos-framework revision: unchanged (server still running from RUN_0003)
- Robometer revision: `5b815254bf31ee1bea3753c3a2da9f9033736d9a`
- IDM/WISE code revision: n/a

## Machine and environments

- host/GPU: same box, unchanged
- driver/CUDA: unchanged
- Isaac Sim / Isaac Lab: not used in this run
- RoboLab interpreter: not used in this run (only its already-produced output files)
- Cosmos interpreter: not used in this run
- Robometer interpreter: `/workspace/robometer/.venv/bin/python` (3.10.20, torch 2.8.0+cu128, CUDA available — verified during prep)
- IDM interpreter: n/a
- key package versions: robometer `--extra robometer` group (transformers>=4.57, trl==0.20.0)

## Setup from a clean state

```bash
cd /workspace/robometer
uv sync --extra robometer          # already done during prep; see STATE.md
export HF_HOME=/workspace/.hf_home
HF_HUB_DISABLE_XET=1 /workspace/robometer/.venv/bin/hf download robometer/Robometer-4B
```

Required environment variables:

```bash
HF_HOME=/workspace/.hf_home
HF_HUB_DISABLE_XET=1
```

## Models and data

- Cosmos checkpoint + exact revision: n/a (using already-produced video, not re-running Cosmos)
- Robometer checkpoint + exact revision: `robometer/Robometer-4B`, default revision (main)
- IDM checkpoint + exact revision: n/a
- DROID dataset release/split: n/a
- other inputs/assets:
  - sensor video: `/workspace/RoboLab/output/2026-08-12_07-37-11_cosmos3/BananaInBowlTask/Pick_up_the_banana_and_place_it_in_the_bowl_0.mp4` (2560x360, head|left|right|wrist, 140 frames)
  - dream videos: `/workspace/RoboLab/output/2026-08-12_07-37-11_cosmos3/BananaInBowlTask/dreams/dream_env0_call{000..004}.mp4` (5x, 640x528, 33 frames each)
  - event/success log: `/workspace/RoboLab/output/2026-08-12_07-37-11_cosmos3/BananaInBowlTask/log_0_env0.json`, `episode_results.jsonl` (success=true, episode_step=141, events: TARGET_OBJECT_DROPPED at some step)

## RoboLab / experiment configuration

- task(s): `BananaInBowlTask` (video already produced, not re-run)
- exact instruction(s): "Pick up the banana and place it in the bowl" (verbatim, sent as Robometer's prompt task string)
- num envs / episodes: 1 episode, already completed (RUN_0003)
- candidate budget K: n/a (offline scoring only)
- Robometer view/scalarization: one camera per call, no compositing (per M2 skill + bootstrap notes' rationale — RBM-1M contains no tiled frames, DROID deployment uses one exterior view). Scalarization: keep full per-frame curve, report both `last` (final frame progress) and `last-first` as candidate `r_task` scalarizations, decide later.
- IDM preprocessing/config: n/a
- `r_exec` config: n/a
- calibration/fusion config: n/a

## Exact commands

```bash
cd /workspace/wise_robolab
/workspace/robometer/.venv/bin/python research/tools/score_robometer.py \
  --run-dir /workspace/RoboLab/output/2026-08-12_07-37-11_cosmos3/BananaInBowlTask \
  --sensor-video "/workspace/RoboLab/output/2026-08-12_07-37-11_cosmos3/BananaInBowlTask/Pick_up_the_banana_and_place_it_in_the_bowl_0.mp4" \
  --task "Pick up the banana and place it in the bowl" \
  --out /workspace/wise_robolab/research/runs/RUN_0004_robometer_progress.json
```

## Expected outputs

- result directory: `research/runs/`
- logs: stdout, captured here
- videos/dreams: n/a (reusing existing)
- metrics JSON: `RUN_0004_robometer_progress.json` — per-call, per-view {dream_curve, real_curve, dream_last, real_last}
- checkpoints: none written (inference only)
- other artifacts: n/a

## Execution result

- start time: 2026-08-12T07:55Z (first attempt, failed on import); retried 2026-08-12T07:56:39Z after environment fix
- end time: 2026-08-12T07:59:17Z
- wall time: ~2.5 min for model load + 30 inference calls (5 chunks x 3 views x {dream, real}) -> roughly 4-5s/call average including model load amortization; not separately instrumented per-call, treat as approximate
- peak VRAM / throughput if relevant: not sampled live during the run (process had already exited by the time this was checked). Model is Qwen3-VL-4B-class, bf16 — expect ~8-10GB weights plus activations; precise measurement deferred to M3 when K-budget planning needs it.
- exit status: 0 (after fix; first attempt exited 1)
- warnings/errors: (1) **first attempt failed**: `ImportError: cannot import name 'ScalingType' from 'torch.nn.functional'`, raised while importing `robometer.utils.save` -> `peft` -> `transformers.quantizers.quantizer_torchao` -> `torchao`. Root cause: `torchao==0.18.0` (pulled transitively, not pinned in `robometer`'s `pyproject.toml` — likely via `unsloth`/`trl`) requires torch APIs newer than the pinned `torch==2.8.0`. Fixed with `uv pip install "torchao<0.10"` (resolved to `0.9.0`), verified the import chain clean before retrying. Per CLAUDE.md guidance, this is an environment/dependency-resolution bug, diagnosed at the smallest failing layer, not evidence against Robometer itself. (2) benign HF warning: "using a model of type qwen3_vl to instantiate a model of type qwen2_5_vl" (expected — Robometer-4B's Qwen3-VL backbone loads via a Qwen2.5-VL-compatible loader path). (3) seam auto-detection: ratio predicted row 352, detector found 359 for all 5 dream clips consistently — used the detected value (359) per the script's designed fallback; this pins down the previously-unresolved "12 lost rows" question from the bootstrap notes to a slightly different value (528*2/3=352 vs detected 359, a 7px difference) worth another look before treating it as fully settled, but the two disagree by less than the >4px threshold that would trigger investigation... actually they differ by 7px which DID trigger the fallback — recorded here rather than silently trusting either number.

## Observed evidence

- validation/benchmark result: **PASS**. `sensor video: (140, 360, 2560, 3)` (matches ffprobe). All 3 real views (wrist/left/right) and 2 of 3 dream views show clear, monotonically-increasing progress curves closely tracking each other and the ground-truth event timeline. No view is universally flat/NaN/zero.
- task-level result: reused from RUN_0003 — grasp (`OBJECT_GRABBED_SUCCESS`) at step 82 (~chunk 2 of 5), final success at step 141 (chunk 4, the last)
- candidate diversity: n/a
- Robometer: per-call **real** `last` progress (all 3 views, chunks 0-4):
  - wrist: 0.495 -> 0.529 -> 0.649 -> 0.846 -> **0.864**
  - left:  0.285 -> 0.482 -> 0.728 -> 0.786 -> **0.854**
  - right: 0.401 -> 0.595 -> 0.628 -> 0.810 -> **0.824**

  All three real views rise essentially monotonically from ~0.3-0.5 (chunk 0) to ~0.82-0.86 (chunk 4, at/after success) — textbook interpretable progress signal, closely tracking the actual grasp/success timeline.

  Per-call **dream** `last` progress:
  - wrist: 0.448 -> 0.488 -> 0.621 -> 0.813 -> **0.844**
  - left:  0.345 -> 0.594 -> 0.711 -> 0.830 -> **0.882**
  - right: 0.183 -> 0.596 -> 0.661 -> 0.848 -> **0.084** (anomaly on the final chunk — see below)

  Dream wrist and left both track their real counterparts closely across all 5 chunks (both rise to >0.8 by the end), evidence that Cosmos's imagined futures are broadly *task-progress-faithful*, not just visually plausible. Dream right matches real right well for chunks 0-3 (0.18->0.60->0.66->0.85, vs real 0.40->0.60->0.63->0.81) but then **collapses to 0.084 on chunk 4** (per-frame curve flat-low: `[0.18, 0.116, 0.133, 0.086, 0.087, 0.083, 0.089, 0.084]`) while real-right stays high (0.824) and both other dream views stay high. Per the M2 skill's reading table, a flat-near-zero result after a previously-informative view most likely means Robometer's learned "not the same task" escape fired for this one clip/view — i.e. something about the final chunk's imagined right-eye view reads as off-task or degenerate to Robometer, even though the wrist/left dreams for the same chunk look fine. This is exactly the kind of real-vs-generated-domain-shift evidence the project wants surfaced now, ahead of M5's systematic real-vs-dream consistency-distribution work — flagging it there rather than dismissing it as noise.
- IDM: n/a
- WISE: n/a
- artifact paths: `/workspace/wise_robolab/research/runs/RUN_0004_robometer_progress.json` (full per-call, per-view raw + curve data)

## Outcome

- pass/fail: **PASS**
- what was proven: Robometer-4B installs and runs correctly (after fixing a real transitive-dependency version conflict); it produces clearly interpretable, non-degenerate, monotonically-increasing progress on real RoboLab sensor video across all three DROID views, correlating with the actual grasp/success event timeline; it produces similarly interpretable progress on 2 of 3 Cosmos dream views, with one genuine, informative anomaly on the third (dream-right, final chunk) rather than uniform failure. `format_prompt_as_json`-style verbatim instruction conditioning works (same string used throughout). Per-frame curves are retained (not just last-frame), so the `r_task` scalarization choice (currently: final-frame progress, `last`) can be revisited without re-running inference.
- what was **not** proven: precise latency/VRAM budget for K-candidate planning (approximate only — ~4-5s/call, not per-call-instrumented; VRAM not sampled live) — worth a dedicated micro-benchmark before committing to a K value in M3. Also not proven: behavior on a *failed* trajectory (this episode succeeded) or on other tasks — both useful before generalizing beyond this one task/episode, per the M2 skill's guidance to include failed/partial trajectories "when available" (none were available yet from M1's 2 successful episodes).
- next action: write `PROGRESS_0002_ROBOMETER.md`, update `RUNBOOK.md`'s Robometer section (installed env + the torchao fix as a known trap), append the experiment, update `STATE.md`, mark M2 `MILESTONE_PASS`, hand off to M3 (`/run-robometer-bestofk`).

## Exact rerun recipe

```bash
cd /workspace/robometer && uv sync --extra robometer
export HF_HOME=/workspace/.hf_home HF_HUB_DISABLE_XET=1
/workspace/robometer/.venv/bin/hf download robometer/Robometer-4B
cd /workspace/wise_robolab
/workspace/robometer/.venv/bin/python research/tools/score_robometer.py \
  --run-dir /workspace/RoboLab/output/2026-08-12_07-37-11_cosmos3/BananaInBowlTask \
  --sensor-video "/workspace/RoboLab/output/2026-08-12_07-37-11_cosmos3/BananaInBowlTask/Pick_up_the_banana_and_place_it_in_the_bowl_0.mp4" \
  --task "Pick up the banana and place it in the bowl"
```

## Reproducibility checklist

- [x] exact commits/revisions recorded
- [x] exact environment/interpreters recorded
- [x] setup steps recorded
- [x] exact commands recorded
- [x] task/data budget recorded
- [x] seeds/randomness recorded (n/a — deterministic inference, no sampling)
- [x] configs/model revisions recorded
- [x] outputs/artifacts recorded
- [x] no secrets recorded
- [x] failed run preserved if applicable (first attempt's ImportError documented inline above)
