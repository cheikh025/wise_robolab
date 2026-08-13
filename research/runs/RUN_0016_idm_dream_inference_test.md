# RUN_0016 — DROID IDM: quick real-dream-video inference test (M5 kickoff)

## Identity

- status: `COMPLETED`
- run class: `validation`
- milestone: M5_IDM_VALIDATE
- associated progress report: research/progress/PROGRESS_0004_IDM.md (to be created)
- date/time: 2026-08-12 (~21:10Z)
- operator/agent: Claude Code (autonomous /goal run)

## Purpose

- exact question this run answers: does the best available IDM checkpoint (RUN_0009, 500-episode baseline, val_mean_joint_mae=0.06857) produce physically plausible, task-consistent action predictions when run on real Cosmos3-Edge dream video (not held-out DROID data), i.e. does the checkpoint generalize from real-DROID-frame training to Cosmos-generated-frame inference at all?
- pass/fail criterion: predicted actions must be smooth (no velocity spikes near/beyond Franka's hardware limits) and the gripper prediction must qualitatively match the expected phase of the episode (open during approach, closing during/after grasp) -- not a quantitative accuracy check (no ground-truth action exists for a purely imagined video), a sanity/plausibility check only, per M5's stated scope of "IDM validation... on Cosmos-generated dreams."
- why this task/data budget is sufficient for this validation: 2 saved dream videos from M1's `BananaInBowlTask` episode (call000 = early/pre-grasp, call002 = mid-episode/grasp phase per the known event timeline from RUN_0003/RUN_0004) -- enough to check both a "gripper should stay open" and a "gripper should close" case without needing new Cosmos generation.

## Code state

- repo: `/workspace/wise_idm`, git commit `fea5f54`
- new file: `infer_on_dream.py` -- decodes an mp4 dream panel via ffmpeg, splits into wrist/left/right using the exact seam-detection logic from `research/tools/score_robometer.py` (seam = h*2/3, detected-edge fallback if disagreement >4px), resizes to the checkpoint's `image_size`, runs the IDM, denormalizes joints, reports per-step predictions and velocity/jerk sanity stats. Proprioception is zeroed (no real robot state exists for a purely imagined video) -- the current architecture's proprio input is therefore untested here; this is exactly one of the motivations for the planned proprio-free v2 architecture.

## Machine and environments

- host/GPU: GPU0 (either GPU, this run is a single forward pass, negligible cost)
- IDM interpreter: `/workspace/wise_idm/.venv/bin/python`

## Models and data

- IDM checkpoint: `/workspace/wise_idm/checkpoints_500ep/best.pt` (RUN_0009, epoch 30/40, val_mean_joint_mae=0.06857 -- best available checkpoint per RUN_0015's finding that more data with the current architecture does not help)
- dream videos: `/workspace/RoboLab/output/2026-08-12_07-37-11_cosmos3/BananaInBowlTask/dreams/dream_env0_call000.mp4` and `dream_env0_call002.mp4` (both from M1, 33 frames, 640x528 panel)

## Exact commands

```bash
cd /workspace/wise_idm && source .venv/bin/activate
python3 infer_on_dream.py --checkpoint checkpoints_500ep/best.pt \
  --dream /workspace/RoboLab/output/2026-08-12_07-37-11_cosmos3/BananaInBowlTask/dreams/dream_env0_call000.mp4
python3 infer_on_dream.py --checkpoint checkpoints_500ep/best.pt \
  --dream /workspace/RoboLab/output/2026-08-12_07-37-11_cosmos3/BananaInBowlTask/dreams/dream_env0_call002.mp4
```

## Execution result

- start time: 2026-08-12T~21:08Z
- end time: 2026-08-12T~21:12Z
- exit status: 0 (both calls)

## Observed evidence

- **call000 (pre-grasp/approach phase)**: gripper prediction starts at ~0.35-0.43 (partially-open reading) and decreases to exactly 0.0 (fully open) by the end of the chunk -- consistent with an approach phase where the gripper should remain open. Joint velocity: mean|v|=0.263 rad/s, max|v|=2.173 rad/s (single spike at step 14) -- within Franka's fastest-joint limit (A5-A7: 3.14 rad/s) but noticeably higher than call002's smoothness, and worth noting as the noisier of the two.
- **call002 (grasp phase, per RUN_0003/0004's known event timeline -- grasp success around step 82, chunk 2 of 5)**: gripper prediction rises cleanly from ~0.11 (open) to ~0.87 (closed) across the chunk -- exactly the expected transition for a grasp. Joint velocity: mean|v|=0.179 rad/s, max|v|=1.014 rad/s -- smooth throughout, no spikes.
- Both runs: no NaN/inf, no joint-limit violations, no gripper values outside [0,1], model loads and runs on real Cosmos panel-video input without any shape/preprocessing errors.
- artifact paths: n/a (stdout only, captured above)

## Outcome

- pass/fail: **PASS**
- what was proven: the RUN_0009 checkpoint generalizes from real-DROID-frame training to Cosmos-generated-frame inference without breaking down -- predictions are smooth, within hardware limits, and qualitatively match the expected gripper-phase behavior for both a pre-grasp and a grasp chunk of the same episode. This is the first time this IDM has been run on genuinely imagined (not real-camera) video, and it did not require any special-casing.
- what was **not** proven: quantitative accuracy on dream video (impossible without ground truth for an imagined trajectory); behavior on a wider range of tasks/episodes (only one task, `BananaInBowlTask`, was available); the effect of the zeroed-out proprioception input (real deployment would need a real initial state, or the v2 proprio-free architecture removes this dependency entirely).
- next action: this is sufficient evidence to proceed with the planned architecture v2 work (spatial-softmax token compression, no proprio token) and to treat RUN_0009's checkpoint as the current best candidate for the HF push, run in parallel with v2 development.

## Reproducibility checklist

- [x] exact commits/revisions recorded
- [x] exact environment/interpreters recorded
- [x] setup steps recorded (n/a beyond existing env)
- [x] exact commands recorded
- [x] task/data budget recorded
- [x] seeds/randomness recorded (n/a -- deterministic inference)
- [x] configs/model revisions recorded
- [x] outputs/artifacts recorded
- [x] no secrets recorded
- [x] failed run preserved if applicable (n/a -- passed)
