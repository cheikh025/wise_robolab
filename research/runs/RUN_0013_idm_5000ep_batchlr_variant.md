# RUN_0013 — DROID IDM: 5000-episode training, larger-batch/higher-lr variant (parallel to RUN_0012)

## Identity

- status: `COMPLETED`
- run class: `validation`
- milestone: M4_IDM_TRAIN
- associated progress report: research/progress/PROGRESS_0004_IDM.md (to be created)
- date/time: 2026-08-12 (~11:10Z)
- operator/agent: Claude Code (autonomous /goal run, user-directed GPU utilization + training-setting experimentation freedom)

## Purpose

- exact question this run answers: at 10x more data than RUN_0009, does a larger batch size (32 vs 16) with a correspondingly higher peak LR (5e-4 vs 3e-4) train faster/better than RUN_0012's direct baseline scale-up, now that there's enough data to support larger batches without starving the model of gradient-step diversity?
- pass/fail criterion: n/a (comparison run) -- informs whether batch/lr should be retuned at this data scale for any future larger run, run concurrently with RUN_0012 so it costs no extra wall time (GPU1 otherwise idle) per the standing "keep all GPUs busy" directive.
- why this task/data budget is sufficient for this validation: identical data/split to RUN_0012 (same 5000-episode set, same train/val split), only batch size and peak LR differ -- an apples-to-apples hyperparameter comparison.

## Code state

- repo: `/workspace/wise_idm`, git commit `8687125`

## Machine and environments

- host/GPU: GPU1 (`CUDA_VISIBLE_DEVICES=1`), running concurrently with RUN_0012 on GPU0
- IDM interpreter: `/workspace/wise_idm/.venv/bin/python`

## Setup from a clean state

Same as RUN_0012 -- reads the same already-populated video cache (read-only, no write race since preprocessing finished before this run started).

## Models and data

- DROID dataset: identical to RUN_0012 -- episodes 0-4499 train / 4500-4999 val

## RoboLab / experiment configuration

n/a (no RoboLab/Cosmos/Robometer execution)

- IDM config: identical to RUN_0012 (baseline architecture, cnn_width=64, d_model=256, 4+4 layers)
- training config: batch_size=32 (vs RUN_0012's 16), lr=5e-4 (vs 3e-4), AdamW, OneCycleLR, grad clip 1.0, BCE gripper + pos_weight, epochs=15, seed=0

## Exact commands

```bash
cd /workspace/wise_idm && source .venv/bin/activate
export HF_HOME=/workspace/.hf_home
CUDA_VISIBLE_DEVICES=1 python3 train.py --mode train \
  --train-episodes $(seq 0 4499 | tr '\n' ' ') \
  --val-episodes $(seq 4500 4999 | tr '\n' ' ') \
  --batch-size 32 --epochs 15 --lr 5e-4 --seed 0 \
  --out-dir /workspace/wise_idm/checkpoints_5000ep_bs32 \
  --log-dir /workspace/wise_idm/tb_logs_5000ep_bs32
```

## Expected outputs

- checkpoints: `/workspace/wise_idm/checkpoints_5000ep_bs32/best.pt`, `history.json`

## Execution result

- start time: 2026-08-12T~11:13Z
- end time: 2026-08-12T~15:37Z (15 epochs, ~1000-1060s/epoch)
- exit status: 0

## Observed evidence

- IDM: best checkpoint at epoch 8/15, `val_mean_joint_mae=0.12384`, `val_gripper_accuracy=0.99272`. Matches RUN_0012's independent run (same architecture/data, different batch/lr: 16/3e-4 vs this run's 32/5e-4) closely: 0.1256 vs 0.1238 -- confirms the plateau is not an artifact of one specific batch/lr choice.
- artifact paths: `/workspace/wise_idm/checkpoints_5000ep_bs32/best.pt`, `/workspace/wise_idm/checkpoints_5000ep_bs32/history.json`

## Outcome

- pass/fail: n/a (comparison) -- **result: batch/lr setting did not matter**, both plateaued in the same ~0.124-0.126 range.
- what was proven: this run (paired with RUN_0012) rules out batch size / peak LR as the explanation for the 5000-episode plateau -- ruling it out was necessary evidence to focus on epoch budget instead (see RUN_0012 and RUN_0014's updated outcomes: the real diagnosis is too few epochs -- 15 passes over 5000 episodes gives each example far less repeated exposure than RUN_0009's 40 passes over 500 episodes, even though total gradient steps here were ~3x higher than RUN_0009's entire run).
- next action: superseded by RUN_0015 -- a single combined-GPU (DDP) run at a properly matched epoch budget (30 epochs), using the baseline architecture and the RUN_0012-style batch=16 per-GPU setting (since batch size was shown here not to be the deciding factor).

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
- [x] failed run preserved if applicable (documented above rather than as a separate run file)
