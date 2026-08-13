# RUN_0015 — DROID IDM: 5000-episode training, both GPUs (DDP), matched epoch budget (decisive run)

## Identity

- status: `COMPLETED`
- run class: `validation`
- milestone: M4_IDM_TRAIN
- associated progress report: research/progress/PROGRESS_0004_IDM.md (to be created)
- date/time: 2026-08-12 (~16:25Z)
- operator/agent: Claude Code (autonomous /goal run, user-directed: use both GPUs together for one correct/decisive run rather than further split single-GPU ablations)

## Purpose

- exact question this run answers: with the diagnosed root cause of RUN_0012/RUN_0013's plateau being epoch budget (15 epochs gives each of 4500 train examples only 15 passes, vs RUN_0009's 40 passes over 500 examples, despite ~3x more total gradient steps -- an underfitting signature, not a generalization gap and not clearly a capacity issue per RUN_0013 ruling out batch/lr and RUN_0014 being aborted before it could test capacity), does the baseline architecture trained for a properly matched epoch budget (30, matching where RUN_0009 actually converged) on the full 5000-episode set beat RUN_0009's 500-episode result (val_mean_joint_mae=0.06857)?
- pass/fail criterion: val_mean_joint_mae at convergence meaningfully below 0.06857 (5000 episodes helps once given adequate epochs) or plateaus at/above it (500 episodes was already sufficient and this IDM doesn't benefit from more DROID data at this recipe).
- why this task/data budget is sufficient for this validation: same 5000-episode data as RUN_0012/RUN_0013 (already downloaded, cached, verified), same baseline architecture already proven best at 500-episode scale (RUN_0010) and not yet falsified at 5000-episode scale -- this is a single, decisive run rather than continuing to split GPU time across parallel single-variable ablations, per explicit user direction to combine both GPUs into one correct run now that there is enough evidence to commit.

## Code state

- repo: `/workspace/wise_idm`, git commit `fea5f54`
- relevant diff since RUN_0012/RUN_0013 (commit `fea5f54`): added multi-GPU DDP support to `train.py` (`DistributedDataParallel` + `DistributedSampler`, falls back to single-process when launched without `torchrun`); replaced `compute_joint_stats`/`compute_gripper_pos_weight` (which wastefully decoded all 3 cameras' video per window just to read the 8-dim action column) with `compute_stats_fast`, which reads directly from the already-loaded parquet action columns -- no behavior change, removes a needless full-dataset video-decode pass before training starts. Verified via a 1-epoch DDP smoke test on the 500-episode set (43.8s for epoch 0 across 2 GPUs vs RUN_0009's ~85-134s single-GPU) before committing to this run.

## Machine and environments

- host/GPU: both A100s (`torchrun --standalone --nproc_per_node=2`), DDP with NCCL backend
- IDM interpreter: `/workspace/wise_idm/.venv/bin/python`

## Setup from a clean state

Reuses the already-populated 5000-episode video cache (episodes 0-4999, ~259GB, from `preprocess_videos.py --num-episodes 5000`, verified complete).

## Models and data

- DROID dataset: identical to RUN_0012/RUN_0013 -- `nvidia/Cosmos3-DROID` success split, episodes 0-4499 train / 4500-4999 val

## RoboLab / experiment configuration

n/a (no RoboLab/Cosmos/Robometer execution)

- IDM config: baseline architecture (RUN_0010-confirmed at 500-episode scale) -- cnn_width=64, d_model=256, n_heads=8, n_encoder_layers=4, n_decoder_layers=4, ~9.0M params
- training config (revised pre-epoch-0, see note below): batch_size=48 per GPU (effective global batch 96 across 2 GPUs), lr=5e-4 (sqrt-scaled from RUN_0012's 16/3e-4 baseline, ~1.73x for 3x batch, rounded to match RUN_0013's already-validated 5e-4 value), AdamW, OneCycleLR, grad clip 1.0, BCE gripper + pos_weight, epochs=30, num_workers=8/rank, seed=0
- note: originally launched at batch_size=16/lr=3e-4 (matching RUN_0012); killed and relaunched at batch_size=48/lr=5e-4 within ~2 minutes, before any epoch completed (near-zero sunk cost), after observing GPU memory was only ~19% utilized (15.7GB/80GB) at the original batch size -- user asked to use a bigger batch for faster training given the headroom.

## Exact commands

```bash
cd /workspace/wise_idm && source .venv/bin/activate
export HF_HOME=/workspace/.hf_home
torchrun --standalone --nproc_per_node=2 train.py --mode train \
  --train-episodes $(seq 0 4499 | tr '\n' ' ') \
  --val-episodes $(seq 4500 4999 | tr '\n' ' ') \
  --batch-size 48 --epochs 30 --lr 5e-4 --num-workers 8 --seed 0 \
  --out-dir /workspace/wise_idm/checkpoints_5000ep_ddp \
  --log-dir /workspace/wise_idm/tb_logs_5000ep_ddp
```

## Expected outputs

- checkpoints: `/workspace/wise_idm/checkpoints_5000ep_ddp/best.pt`, `history.json`

## Execution result

- start time: 2026-08-12T~16:26Z (relaunched at batch=48/lr=5e-4 after an initial batch=16/lr=3e-4 launch was killed pre-epoch-0 to better utilize GPU memory headroom)
- end time: 2026-08-12T~21:04Z (30 epochs, ~470-490s/epoch, ~4hr wall time across both GPUs via DDP)
- exit status: 0

## Observed evidence

- IDM: best checkpoint at epoch 21/30, `val_mean_joint_mae=0.11701`, `val_gripper_accuracy=0.99253`, `gripper_mae=0.01617`. Per-joint MAE: `[0.0773, 0.1453, 0.0740, 0.1438, 0.1034, 0.1285, 0.1467]` -- notably wider spread than RUN_0009's 500ep result (`[0.036, 0.070, 0.037, 0.097, 0.075, 0.076, 0.089]`), with joints A2/A4/A7 (indices 1,3,6) particularly worse (0.145/0.144/0.147 vs RUN_0009's 0.070/0.097/0.089).
- Training curve: fast initial drop through epoch 6 (0.315->0.137 LR still >90% of peak), flat noisy plateau epochs 7-19 (0.122-0.135, LR decaying 91%->33% of peak), then a real break to a new floor around epoch 20-21 (0.120->0.117) as LR dropped below ~30% of peak -- matches the OneCycleLR-driven analysis discussed mid-run. Epochs 22-29 oscillated in a tight `[0.1170, 0.1199]` band with no further net improvement despite LR continuing to anneal toward zero -- this time genuinely converged, not merely under-scheduled (unlike RUN_0012/RUN_0013's 15-epoch runs).
- Checkpoint reload verification (`verify_checkpoint.py`): exact match (`joint_mae` diff=0.000000, `gripper_acc` diff=0.000000).
- Comparison across all 5000-episode attempts: RUN_0012 (15ep, bs16) 0.1256; RUN_0013 (15ep, bs32) 0.1238; **RUN_0015 (30ep, bs48, DDP) 0.1170** -- the properly-matched epoch budget did help (best result among the 5000ep attempts), confirming epoch budget was a real factor in RUN_0012/13's underperformance, but even with adequate epochs the 5000-episode run does **not** beat RUN_0009's 500-episode result (0.06857).
- artifact paths: `/workspace/wise_idm/checkpoints_5000ep_ddp/best.pt`, `/workspace/wise_idm/checkpoints_5000ep_ddp/history.json`

## Outcome

- pass/fail: **FAIL** against this run's own pass criterion (did not beat RUN_0009's 0.06857)
- what was proven: (1) epoch budget was a real, fixable factor -- 30 epochs clearly beat 15 epochs at this data scale (0.117 vs ~0.124-0.126); (2) even with a properly matched epoch budget and genuine convergence (flat for the last 8 epochs despite LR still annealing), the current architecture does not benefit from 10x more DROID data -- it does *worse* than the 500-episode checkpoint. This is a genuine capacity/token-efficiency finding, not an artifact of insufficient training time, and directly motivates the architecture redesign discussed afterward (replacing the 1537-token flatten-to-grid encoding with spatial-softmax token compression to ~96 tokens, dropping the proprioception token, keeping the joint-decode transformer skeleton).
- what was **not** proven: whether the redesigned (spatial-softmax, vision-only) architecture would do better at 5000-episode scale -- that is the next experiment.
- next action: (1) RUN_0009's 500-episode checkpoint (`checkpoints_500ep/best.pt`, val_mean_joint_mae=0.06857) remains the best available IDM checkpoint and the leading candidate for the M5 quick task test and eventual HF push; (2) implement the redesigned architecture (spatial-softmax token compression, no proprio token) and train it at 5000-episode scale to test whether it resolves the capacity gap this run exposed; (3) push both the current-architecture (RUN_0009) and new-architecture checkpoints to HF for comparison, per explicit user direction.

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
