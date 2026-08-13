# RUN_0012 — DROID IDM: 5000-episode training (baseline architecture, final scale)

## Identity

- status: `COMPLETED`
- run class: `validation`
- milestone: M4_IDM_TRAIN
- associated progress report: research/progress/PROGRESS_0004_IDM.md (to be created)
- date/time: 2026-08-12 (~11:10Z)
- operator/agent: Claude Code (autonomous /goal run)

## Purpose

- exact question this run answers: does the baseline architecture (confirmed the winner over the wide/deep variant in RUN_0010, at ~9.0M params: cnn_width=64, d_model=256, 4+4 transformer layers), trained on 10x more data (5000 vs 500 episodes), improve materially beyond RUN_0009's 500-episode checkpoint (val_mean_joint_mae=0.06857)? This directly answers the user's explicit question ("might even give a hint whether we need more than 5k").
- pass/fail criterion: val_mean_joint_mae improves meaningfully below RUN_0009's 0.06857 (data helped) or plateaus at/above it (500 episodes had already captured most of the achievable gain for this architecture/recipe).
- why this task/data budget is sufficient for this validation: this is the full parallel-downloaded 5000-episode set the user explicitly asked for as the next scale step beyond 500; a fresh disjoint 500-episode val split (4500-4999) keeps the same train/val ratio as RUN_0009 for a fair comparison.

## Code state

- repo: `/workspace/wise_idm`, git commit `8687125` (checkpoint-config fix, includes all architecture hyperparameters now)
- IDM/WISE code revision: unchanged from RUN_0010's fixed recipe

## Machine and environments

- host/GPU: GPU0 (`CUDA_VISIBLE_DEVICES=0`), free at launch (both A100s idle after RUN_0009/RUN_0010 completed)
- IDM interpreter: `/workspace/wise_idm/.venv/bin/python` (3.11, torch 2.11.0+cu128)
- system: 128 vCPU, 503GiB RAM (86GiB free / 401GiB page cache at launch), 322GB disk free after the 5000-episode video cache (259GB) was written

## Setup from a clean state

`preprocess_videos.py --num-episodes 5000` (completed prior to this run, background task `bwj3fgs78`, exit 0): downloaded and pre-decoded video caches for all 3 cameras across episodes 0-4999 (150/137/61 files respectively for exterior_1/exterior_2/wrist, ~259GB total in `/workspace/wise_idm/cache`). Verified with a smoke-test dataset load on episodes 4990-4999 (280 windows constructed successfully, confirming both video cache and on-demand data-parquet download work for the tail of the range) before committing to the full training run.

## Models and data

- DROID dataset release/split: `nvidia/Cosmos3-DROID`, `success` split, episodes 0-4499 (train) / 4500-4999 (val)
- IDM checkpoint + exact revision: fresh training run, baseline architecture (RUN_0010-confirmed winner)

## RoboLab / experiment configuration

n/a (no RoboLab/Cosmos/Robometer execution)

- IDM config: image_size=128, num_frames=33 (full density), cnn_width=64, d_model=256, n_heads=8, n_encoder_layers=4, n_decoder_layers=4 (RUN_0010-confirmed baseline, ~9.0M params)
- training config: batch_size=16, lr=3e-4, AdamW, OneCycleLR, grad clip 1.0, BCE gripper loss with pos_weight computed from the 4500-episode train split, epochs=15 (reduced from RUN_0009's 40 -- 10x more data means roughly comparable total gradient steps at ~1/3 the epoch count; will extend if still improving at epoch 15), seed=0

## Exact commands

```bash
cd /workspace/wise_idm && source .venv/bin/activate
export HF_HOME=/workspace/.hf_home
CUDA_VISIBLE_DEVICES=0 python3 train.py --mode train \
  --train-episodes $(seq 0 4499 | tr '\n' ' ') \
  --val-episodes $(seq 4500 4999 | tr '\n' ' ') \
  --batch-size 16 --epochs 15 --lr 3e-4 --seed 0 \
  --out-dir /workspace/wise_idm/checkpoints_5000ep \
  --log-dir /workspace/wise_idm/tb_logs_5000ep
```

## Expected outputs

- checkpoints: `/workspace/wise_idm/checkpoints_5000ep/best.pt`, `history.json`
- logs: `/workspace/wise_idm/tb_logs_5000ep/`

## Execution result

- start time: 2026-08-12T~11:12Z
- end time: 2026-08-12T~15:12Z (15 epochs, ~1105-1180s/epoch, ~4hr wall time; slower than RUN_0009 per-epoch since each epoch now covers ~10x more windows)
- exit status: 0

## Observed evidence

- IDM: best checkpoint at epoch 5/15, `val_mean_joint_mae=0.12558`, `val_gripper_accuracy=0.99228`. Val metric plateaued/oscillated in the `[0.125, 0.135]` band for the remaining 10 epochs with no further improvement -- **worse** than RUN_0009's 500-episode result (`val_mean_joint_mae=0.06857`), despite far more total training data and gradient steps. `train_loss` at epoch 12 (0.2516) was still higher than RUN_0009 had already reached by *its* epoch 4 (0.2840) -- more telling, RUN_0009 reached a lower train_loss (0.2215) by its own epoch 12 than this run ever reached in all 15 epochs (best ~0.250), even though this run did ~3x more total gradient-descent steps overall. This is an underfitting signature (train loss itself insufficiently low), not a generalization gap.
- Matches RUN_0013's independent run (different batch/lr) on the same data: 0.1256 vs 0.1238 -- consistent, ruling out this being a one-off/noisy result specific to one hyperparameter setting.
- artifact paths: `/workspace/wise_idm/checkpoints_5000ep/best.pt`, `/workspace/wise_idm/checkpoints_5000ep/history.json`

## Outcome

- pass/fail: **FAIL** against this run's own pass criterion (did not improve on RUN_0009; in fact regressed)
- what was proven: at 15 epochs, scaling from 500 to 5000 episodes with the *same* architecture and epoch budget does not help and in fact underperforms -- the model appears capacity-limited at this larger, more diverse data scale (unlike at 500 episodes, where RUN_0010 found the opposite -- more capacity didn't help because data was the bottleneck there). RUN_0014 (wide architecture on the same 5000-episode data, running concurrently on GPU1) directly tests whether more capacity resolves this.
- next action: await RUN_0014's result. If the wide model clearly beats this plateau, capacity was the bottleneck at 5000-episode scale and the wide architecture becomes the leading final-checkpoint candidate. If not, the 500-episode checkpoint (RUN_0009, still the best result so far at 0.06857) likely remains the best available candidate and 5000 episodes should be deprioritized rather than sunk further time into per user's explicit efficiency directive.

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
- [x] failed run preserved if applicable (documented above rather than as a separate run file -- this run itself is the "failed to improve" result)
