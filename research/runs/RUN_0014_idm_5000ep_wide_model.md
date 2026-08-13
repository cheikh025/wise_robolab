# RUN_0014 — DROID IDM: wide/deep architecture at 5000-episode scale (re-testing RUN_0010's conclusion at larger data scale)

## Identity

- status: `ABORTED`
- run class: `diagnostic`
- milestone: M4_IDM_TRAIN
- associated progress report: research/progress/PROGRESS_0004_IDM.md (to be created)
- date/time: 2026-08-12 (~13:15Z)
- operator/agent: Claude Code (autonomous /goal run)

## Purpose

- exact question this run answers: RUN_0010 found that a wide/deep variant (23.8M params) underperforms the baseline (9.0M params) at 500-episode scale (data-limited regime, more capacity just overfit). RUN_0012/RUN_0013 (5000-episode baseline, 15 epochs) then plateaued at val_mean_joint_mae~0.124-0.134, clearly worse than RUN_0009's 500-episode result (0.0686) despite ~3x more total gradient steps and train_loss also failing to drop as far as RUN_0009's -- an underfitting signature, not a generalization-gap signature. This suggests the regime flipped: at 5000 episodes (far more scene/task diversity), the 9.0M-param baseline may now be capacity-limited rather than data-limited. This run directly tests that by training the same wide/deep architecture from RUN_0010 on the same 5000-episode data RUN_0012 used.
- pass/fail criterion: n/a (diagnostic) -- if the wide model clearly beats RUN_0012/RUN_0013's ~0.124-0.134 plateau, capacity was the bottleneck at this data scale (reversing RUN_0010's conclusion, which only held at 500 episodes). If it plateaus at a similar or worse level, the bottleneck is more likely epoch budget/schedule, not raw parameter count -- next step would be a longer training run instead.
- why this task/data budget is sufficient for this validation: identical 5000-episode data/split to RUN_0012/RUN_0013, same epoch budget (15) for a fair architecture-only comparison.

## Code state

- repo: `/workspace/wise_idm`, git commit `8687125`

## Machine and environments

- host/GPU: GPU1 (`CUDA_VISIBLE_DEVICES=1`), free after RUN_0013 completed
- IDM interpreter: `/workspace/wise_idm/.venv/bin/python`

## Setup from a clean state

Reuses the already-populated 5000-episode video cache and joint-stats computation path (no new setup).

## Models and data

- DROID dataset: identical to RUN_0012/RUN_0013 -- episodes 0-4499 train / 4500-4999 val

## RoboLab / experiment configuration

n/a (no RoboLab/Cosmos/Robometer execution)

- IDM config: wide variant from RUN_0010 -- cnn_width=96, d_model=384, n_heads=8, n_encoder_layers=6, n_decoder_layers=6 (~23.8M params)
- training config: batch_size=16, lr=3e-4 (matches RUN_0012, not RUN_0013's bs32/lr5e-4, to isolate the architecture variable), OneCycleLR, grad clip 1.0, BCE gripper + pos_weight, epochs=15, seed=0

## Exact commands

```bash
cd /workspace/wise_idm && source .venv/bin/activate
export HF_HOME=/workspace/.hf_home
CUDA_VISIBLE_DEVICES=1 python3 train.py --mode train \
  --train-episodes $(seq 0 4499 | tr '\n' ' ') \
  --val-episodes $(seq 4500 4999 | tr '\n' ' ') \
  --batch-size 16 --epochs 15 --lr 3e-4 --seed 0 \
  --cnn-width 96 --d-model 384 --n-heads 8 --n-encoder-layers 6 --n-decoder-layers 6 \
  --out-dir /workspace/wise_idm/checkpoints_5000ep_wide \
  --log-dir /workspace/wise_idm/tb_logs_5000ep_wide
```

## Expected outputs

- checkpoints: `/workspace/wise_idm/checkpoints_5000ep_wide/best.pt`, `history.json`

## Execution result

- start time: 2026-08-12T~13:16Z
- end time: 2026-08-12T~15:49Z (killed before any epoch completed -- only setup/joint-stats/pos_weight had run)
- exit status: aborted (SIGTERM via pkill), not a failure

## Observed evidence

- IDM: none -- killed before epoch 0 finished, essentially zero sunk training cost.

## Outcome

- pass/fail: n/a (aborted by design change, not a result)
- what was proven: nothing directly -- this run was redesigned before producing a result.
- why aborted: user feedback mid-run (after RUN_0012/RUN_0013 both plateaued at ~0.124-0.126, well above RUN_0009's 0.06857) identified a design flaw in this run's plan: testing capacity (wide vs baseline) at the *same* 15-epoch budget that had already looked insufficient for the baseline is a weak test -- if 15 epochs isn't enough for the small model, it likely isn't enough for the big model either, so this run was likely to come back "still bad" regardless of whether capacity actually matters, which would have wasted the ~3hr run and required a second, longer follow-up anyway. Root cause of the 5000ep plateau was later diagnosed as **epoch budget** (see RUN_0012/RUN_0013 updated outcomes): total gradient steps at 15 epochs actually exceeded RUN_0009's full 40-epoch run by ~3x (10x more data / ~3x fewer epochs), but each individual training example was seen far fewer times (15 passes vs RUN_0009's 40) -- an underfitting signature from insufficient per-example exposure, not insufficient total steps and not (necessarily) insufficient capacity.
- next action: superseded by RUN_0015 -- a single combined-GPU (DDP, both A100s) run using the baseline architecture (not wide, per the evidence at 500-episode scale in RUN_0010 and no evidence yet that capacity is the 5000-episode bottleneck) with an epoch budget matched to RUN_0009's actual convergence point (30 epochs, not 15), using both GPUs together for wall-clock efficiency rather than splitting into further single-GPU ablations.

## Reproducibility checklist

- [x] exact commits/revisions recorded
- [x] exact environment/interpreters recorded
- [x] setup steps recorded
- [x] exact commands recorded
- [x] task/data budget recorded
- [x] seeds/randomness recorded
- [x] configs/model revisions recorded
- [x] outputs/artifacts recorded (none produced -- aborted pre-epoch-0)
- [x] no secrets recorded
- [x] failed run preserved if applicable (this record itself documents the abort and reasoning)
