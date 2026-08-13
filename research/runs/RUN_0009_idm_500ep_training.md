# RUN_0009 — DROID IDM: 500-episode training (scaled from debug subset)

## Identity

- status: `COMPLETED`
- run class: `validation`
- milestone: M4_IDM_TRAIN
- associated progress report: research/progress/PROGRESS_0004_IDM.md (to be created)
- date/time: 2026-08-12 (~09:05Z)
- operator/agent: Claude Code (autonomous /goal run, user-directed scale-up)

## Purpose

- exact question this run answers: does the now-validated training recipe (BCE gripper loss + pos_weight + grad clipping + OneCycleLR + full 33-frame temporal density) continue to improve when scaled ~18x from the 27-episode debug subset to 500 episodes, producing a materially stronger checkpoint?
- pass/fail criterion: val metrics improve meaningfully beyond RUN_0008's debug-subset result (val_mean_joint_mae=0.516, val_gripper_accuracy=0.976 at 27 episodes) or at minimum match it without degrading, confirming the recipe scales rather than being an artifact of the tiny debug subset.
- why this task/data budget is sufficient for this validation: per user direction, this project has moved past pure debug-subset economy once the training recipe was validated (RUN_0007/RUN_0008) -- 500 episodes is an explicit, deliberate scale-up for a "very good, robust" final IDM, with a further 5000-episode download running in parallel in the background for a possible final retrain.

## Code state

- repo: `/workspace/wise_idm` (still no git repo -- flagged repeatedly, must fix before M4 close-out)
- relevant uncommitted diff since RUN_0008: `droid_dataset.py` generalized to (a) read multiple video cache files per camera (keyed by chunk/file, not a single per-camera file) and (b) read multiple DATA parquet files when the episode range spans more than ~1216 episodes (not yet exercised at 500, but required for the parallel 5000-episode download); `preprocess_videos.py` generalized the same way, downloading per-(camera,chunk,file) video files on demand via `hf_hub_download` instead of assuming everything is already local.
- upstream revision if relevant: `nvidia/Cosmos3-DROID` dataset revision `5c11a20accb11497270a5247a7f1e66ad04c956c`
- IDM/WISE code revision: this run's train.py/model.py (unchanged from RUN_0008's corrected recipe)

## Machine and environments

- host/GPU: same box; this run on GPU0 (fully free -- Cosmos/Robometer servers were stopped after M3 to free both A100s for IDM training, per user direction). A parallel `preprocess_videos.py --num-episodes 5000` background job (CPU/network-bound, not GPU) is downloading further episodes concurrently.
- IDM interpreter: `/workspace/wise_idm/.venv/bin/python` (3.11, torch 2.11.0+cu128)

## Setup from a clean state

Same as RUN_0008, with `preprocess_videos.py --num-episodes 500` (RUN_0006/RUN_0008 already covered episodes 0-26; this extends the video cache to 0-499, ~21GB total, 29 video files across 3 cameras).

## Models and data

- DROID dataset release/split: `nvidia/Cosmos3-DROID`, `success` split, episodes 0-449 (train) / 450-499 (val) -- 4,314 total windows across 500 episodes (RUN_0006's 27-episode debug subset is a subset of this range)
- IDM checkpoint + exact revision: builds on RUN_0008's validated recipe; this run's `checkpoints/best.pt` will overwrite RUN_0008's (same output path) -- record the new episode range/window count for provenance

## RoboLab / experiment configuration

n/a (no RoboLab/Cosmos/Robometer execution)

- IDM config: unchanged from RUN_0008 (image_size=128, num_frames=33, 16 spatial tokens/pair, d_model=256, 4+4 transformer layers, 8 heads, ~9.0M params)
- training config: batch_size=16 (increased from 8, more data + free GPU headroom), lr=3e-4, AdamW, OneCycleLR, grad clip 1.0, BCE gripper loss with pos_weight computed from the 450-episode train split, epochs=40, seed=0

## Exact commands

```bash
cd /workspace/wise_idm && source .venv/bin/activate
python3 train.py --mode train \
  --train-episodes $(seq 0 449 | tr '\n' ' ') \
  --val-episodes $(seq 450 499 | tr '\n' ' ') \
  --batch-size 16 --epochs 40 --lr 3e-4 --seed 0
```

## Expected outputs

- checkpoints: `/workspace/wise_idm/checkpoints/best.pt`, `history.json`
- logs: `/workspace/wise_idm/tb_logs/`

## Execution result

- start time: 2026-08-12T09:05Z
- end time: 2026-08-12T10:03Z
- exit status: 0
- warnings/errors: one crash during the run (Bus error / SIGBUS) caused by a race with the concurrently-running 5000-episode `preprocess_videos.py` background download overwriting a video cache file this run's DataLoader workers had `mmap`'d open. Root-caused and fixed with an atomic write-then-rename in `preprocess_videos.py` (write to `path+".tmp"` via explicit file handle, then `os.replace()`); both the training job and the preprocessing job were killed and restarted to pick up the fix. This run record covers the successful retry after that fix.

## Observed evidence

- IDM: best checkpoint at epoch 30/40 -- `val_mean_joint_mae=0.06857`, `val_gripper_accuracy=0.98685`, `gripper_mae=0.01963`. Per-joint MAE: `[0.0359, 0.0695, 0.0373, 0.0974, 0.0746, 0.0760, 0.0892]` rad (joint A4, index 3, is the highest at 0.097 rad -- plausible given A4's narrow, non-centered official range `[-3.0718,-0.0698]`). Training improved from `val_mean_joint_mae=0.197`/`gripper_acc=0.825` at epoch 0, converging by ~epoch 30 with epochs 30-39 all within `[0.0686, 0.0791]` -- no further improvement in the final 10 epochs, i.e. converged for this recipe at this data scale.
- Checkpoint reload verification (training ladder stage 3, `verify_checkpoint.py`): loaded `checkpoints_500ep/best.pt` fresh into a new model instance and re-ran evaluation on the val split (episodes 450-499) -- **exact match** to the recorded metrics (`mean_joint_mae` diff=0.000000, `gripper_accuracy` diff=0.000000). Save/reload round-trip is lossless.
- Compared to RUN_0008 (27-episode debug subset, same recipe): `val_mean_joint_mae` improved from 0.516 to 0.0686 (~7.5x better); `val_gripper_accuracy` from 0.976 to 0.987 (already near-ceiling at debug scale, marginal further gain) -- scaling to 500 episodes substantially improved joint-position accuracy; gripper classification was already strong at debug scale.
- artifact paths: `/workspace/wise_idm/checkpoints_500ep/best.pt`, `/workspace/wise_idm/checkpoints_500ep/history.json`

## Outcome

- pass/fail: **PASS**
- what was proven: the corrected training recipe (BCE gripper + pos_weight + grad clip + OneCycleLR + full 33-frame density) scales cleanly from 27 to 500 episodes with no new instabilities once the unrelated concurrent-decode race was fixed, continues improving substantially with more data, and the checkpoint save/reload path is exact. This is a genuinely useful IDM checkpoint, not just a debug-subset proof of concept.
- what was **not** proven: whether more data (the parallel 5000-episode download) improves further, or whether 500 episodes already captures most of the achievable gain -- the last 10 epochs plateaued, consistent with either "converged for this architecture" or "data-limited." A future 5000-episode retrain will help distinguish these, per the user's own framing ("might even give a hint whether we need more than 5k").
- next action: use this checkpoint to proceed to M5 (IDM validation, incl. on Cosmos-generated dreams); compare against RUN_0010's wide-model variant once it finishes, and against a future 5000-episode retrain once the parallel download completes.

## Reproducibility checklist

- [x] exact commits/revisions recorded (dataset revision; code still not in git)
- [x] exact environment/interpreters recorded
- [x] setup steps recorded
- [x] exact commands recorded
- [x] task/data budget recorded
- [x] seeds/randomness recorded
- [x] configs/model revisions recorded
- [x] outputs/artifacts recorded
- [x] no secrets recorded
- [x] failed run preserved if applicable (the pre-fix SIGBUS crash documented above rather than as a separate run file)
