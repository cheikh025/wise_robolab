# RUN_0010 — DROID IDM: wide/deep model capacity comparison (parallel to RUN_0009)

## Identity

- status: `COMPLETED`
- run class: `validation`
- milestone: M4_IDM_TRAIN
- associated progress report: research/progress/PROGRESS_0004_IDM.md (to be created)
- date/time: 2026-08-12 (~09:11Z)
- operator/agent: Claude Code (autonomous /goal run, user-directed GPU utilization)

## Purpose

- exact question this run answers: is the baseline 9M-param IDM (RUN_0009: cnn_width=64, d_model=256, 4+4 transformer layers) capacity-limited on 500 episodes, or does a ~3x larger model (cnn_width=96, d_model=384, 6+6 layers) reach meaningfully better validation metrics on the identical data/split/recipe?
- pass/fail criterion: n/a (comparison run, not a pass/fail gate) -- informs which architecture scale to carry into the eventual 5000-episode "final" training run
- why this task/data budget is sufficient for this validation: same 500-episode train/val split as RUN_0009, run concurrently on GPU1 (idle otherwise) so the comparison is apples-to-apples and doesn't cost additional wall time -- directly addresses "keep all GPUs doing useful work" per user direction, framed as a real architecture-decision experiment rather than idle compute.

## Code state

- repo: `/workspace/wise_idm` (now a git repo, commit `58b3160`, initialized after this run started -- only pre-existing code files committed, checkpoints/cache gitignored)
- relevant uncommitted diff: `train.py` gained `--cnn-width/--d-model/--n-heads/--n-encoder-layers/--n-decoder-layers` CLI flags threaded into `DroidIDM`'s constructor (previously hard-coded to the defaults); `model.py` unchanged (already accepted these as constructor args)

## Machine and environments

- host/GPU: GPU1 (`CUDA_VISIBLE_DEVICES=1`), running concurrently with RUN_0009 on GPU0 and the 5000-episode `preprocess_videos.py` download (CPU/network-bound) -- three concurrent jobs on one box
- IDM interpreter: `/workspace/wise_idm/.venv/bin/python`

## Models and data

- DROID dataset: identical to RUN_0009 -- `nvidia/Cosmos3-DROID` success split, episodes 0-449 train / 450-499 val, same windows (reads the same on-disk cache, read-only at this point since both training jobs only read, only the download job writes -- and it writes different, not-yet-training-relevant files for episodes 500+, so no read/write race with these two training jobs)

## RoboLab / experiment configuration

n/a (no RoboLab/Cosmos/Robometer execution)

- IDM config (wide variant): image_size=128, num_frames=33, cnn_width=96 (vs baseline 64), d_model=384 (vs 256), n_heads=8, n_encoder_layers=6 (vs 4), n_decoder_layers=6 (vs 4)
- training config: identical to RUN_0009 -- batch_size=16, lr=3e-4, AdamW, OneCycleLR, grad clip 1.0, BCE gripper + pos_weight, epochs=40, seed=0

## Exact commands

```bash
cd /workspace/wise_idm && source .venv/bin/activate
CUDA_VISIBLE_DEVICES=1 python3 train.py --mode train \
  --train-episodes $(seq 0 449 | tr '\n' ' ') \
  --val-episodes $(seq 450 499 | tr '\n' ' ') \
  --batch-size 16 --epochs 40 --lr 3e-4 --seed 0 \
  --cnn-width 96 --d-model 384 --n-heads 8 --n-encoder-layers 6 --n-decoder-layers 6 \
  --out-dir /workspace/wise_idm/checkpoints_500ep_wide \
  --log-dir /workspace/wise_idm/tb_logs_500ep_wide
```

## Expected outputs

- checkpoints: `/workspace/wise_idm/checkpoints_500ep_wide/best.pt`, `history.json`
- logs: `/workspace/wise_idm/tb_logs_500ep_wide/`

## Execution result

- start time: 2026-08-12T09:08Z
- end time: 2026-08-12T~10:35Z (40 epochs, ~134s/epoch, GPU1, batch_size=16 -- essentially matched RUN_0009's per-epoch wall time despite ~2.6x more parameters, since RUN_0009 and this run shared the same disk-cache read path and both were GPU-bound, not IO-bound)
- exit status: 0
- warnings/errors: one bug found and fixed *after* this run's training finished (not during): `train.py`'s checkpoint `config` dict only recorded `image_size`/`num_frames`/`chunk_len`/`cameras`, omitting the architecture hyperparameters (`cnn_width`, `d_model`, `n_heads`, `n_encoder_layers`, `n_decoder_layers`) entirely -- `verify_checkpoint.py` silently reconstructed the model with hard-coded defaults instead of this run's actual wide config, which happened to raise a clear `size mismatch` error on reload (rather than silently loading wrong weights) since this run's shapes differ from the defaults. Fixed both `train.py` (now saves all architecture fields) and `verify_checkpoint.py` (now reconstructs from the full saved config, falling back to defaults only for older checkpoints missing the new fields); patched the already-saved `checkpoints_500ep/best.pt` and `checkpoints_500ep_wide/best.pt` config dicts in place (metadata-only edit, model weights untouched) so both reload correctly going forward. This is a real reproducibility bug relevant to the goal's requirement to push the final checkpoint "with its config" -- would have silently produced an unusable/wrong-shape checkpoint description for any non-default architecture, including a future final run if its hyperparameters ever differ from the hardcoded defaults.

## Observed evidence

- IDM (wide variant, 6+6 layers, d_model=384, cnn_width=96, ~23.8M params vs baseline's ~9.0M): best checkpoint at epoch 38/40, `val_mean_joint_mae=0.08027`, `val_gripper_accuracy=0.98599`, `gripper_mae=0.02232`. Per-joint MAE: `[0.0475, 0.0725, 0.0445, 0.0822, 0.0812, 0.1220, 0.1120]` -- notably worse than baseline on joints A6/A7 (indices 5,6: 0.122/0.112 vs baseline's 0.076/0.089) despite the larger model.
- Training curve: loss decreased steadily (train_loss 0.194 by epoch 39) but val_mean_joint_mae plateaued/oscillated in the `[0.080, 0.086]` band from epoch ~26 onward with no further real improvement -- classic overfitting-relative-to-baseline signature: more capacity fit the 500-episode train set as well or better than baseline, but generalized worse to the held-out 50-episode val split.
- Checkpoint reload verification (fixed `verify_checkpoint.py`): exact match after the config fix (`joint_mae` diff=0.000000, `gripper_acc` diff=0.000000) -- confirms the bug above was purely a metadata/reload-script gap, not a weight-corruption issue.
- Direct comparison at the same 40-epoch budget, same data, same recipe: baseline (RUN_0009) `val_mean_joint_mae=0.06857` vs wide (this run) `val_mean_joint_mae=0.08027` -- **baseline wins by ~17% relative**, despite using ~2.6x fewer parameters.
- artifact paths: `/workspace/wise_idm/checkpoints_500ep_wide/best.pt`, `/workspace/wise_idm/checkpoints_500ep_wide/history.json`

## Outcome

- pass/fail: n/a (comparison) -- **result: baseline architecture (9.0M params) wins**, wide/deep variant (23.8M params) does not help and measurably hurts at 500-episode scale.
- what was proven: at 500 episodes, this IDM is data-limited, not capacity-limited -- the smaller model already has enough capacity to fit the available signal, and the extra capacity in the wide variant translated to worse generalization (higher val error despite comparable/lower train loss), not better. This directly supports the priority of evaluating the parallel 5000-episode download (more data) over further scaling model size.
- next action: carry the **baseline architecture** (cnn_width=64, d_model=256, 4+4 layers, ~9.0M params) forward as the reference config for M5 and for any eventual 5000-episode retrain, rather than the wide variant. Do not scale model capacity further until/unless a larger dataset shows the smaller model saturating.

## Reproducibility checklist

- [x] exact commits/revisions recorded (dataset revision; code now in `wise_idm` git repo, commit `58b3160`)
- [x] exact environment/interpreters recorded
- [x] setup steps recorded
- [x] exact commands recorded
- [x] task/data budget recorded
- [x] seeds/randomness recorded
- [x] configs/model revisions recorded
- [x] outputs/artifacts recorded
- [x] no secrets recorded
- [x] failed run preserved if applicable (the post-hoc checkpoint-config bug documented above rather than as a separate run file)
