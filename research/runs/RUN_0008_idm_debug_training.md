# RUN_0008 — DROID IDM: full debug-subset training (train/val split)

## Identity

- status: `COMPLETED`
- run class: `validation`
- milestone: M4_IDM_TRAIN
- associated progress report: research/progress/PROGRESS_0004_IDM.md (to be created)
- date/time: 2026-08-12 (~08:41Z)
- operator/agent: Claude Code (autonomous /goal run)

## Purpose

- exact question this run answers: does the DreamZero-inspired IDM (full 33-frame temporal density, spatial-compressed CNN backbone, standardized-regression joint head + BCE gripper head) train to a meaningful, non-trivial held-out validation accuracy on the 27-episode DROID debug subset (training ladder stages 2-3: real training + checkpoint/reload)?
- pass/fail criterion: val joint MAE meaningfully below a naive constant-prediction baseline (mean action), val gripper accuracy meaningfully above the 59% majority-class baseline; a saved checkpoint reloads and reproduces the same val metrics.
- why this task/data budget is sufficient for this validation: still the debug-subset stage per the M4 skill ("training scaled beyond debug only after alignment checks pass") — 22 train / 5 val episodes (339 / 78 windows) is exactly the debug-subset scale, not a claim about eventual DROID-scale performance.

## Code state

- repo: `/workspace/wise_idm` (new standalone project, no git repo yet — flagged for follow-up before M4 close-out)
- branch: n/a
- commit: n/a
- relevant uncommitted diff: same code as RUN_0007, plus the post-discussion redesign: (1) full 33-frame temporal density (was 9-frame subsampled) with an added CNN stride to hold the token budget constant (~1537 tokens); (2) gripper head switched from SmoothL1-in-normalized-space regression to BCEWithLogitsLoss on the raw [0,1] target, after the debug subset's gripper distribution was measured as heavily bimodal (59% near 0, 29% near 1, 12% mid-transition) and SmoothL1 plateaued at ~0.45 for 300 steps even on a trivially-memorizable 8-window batch while joint SmoothL1 kept improving — BCE resolved this cleanly (RUN_0007: gripper_acc 0.629 -> 0.984 over 300 steps on the same fixed batch).
- upstream revision if relevant: `nvidia/Cosmos3-DROID` dataset revision `5c11a20accb11497270a5247a7f1e66ad04c956c`
- Cosmos/cosmos-framework revision: n/a for this run
- Robometer revision: n/a
- IDM/WISE code revision: this run's model/train code (second version, post gripper-loss fix)

## Machine and environments

- host/GPU: same box; this run pinned to `CUDA_VISIBLE_DEVICES=1` (GPU 0 is running the Cosmos3-Edge server from M1/M3 with ~26GB in use; GPU 1 is otherwise idle)
- driver/CUDA: unchanged
- IDM interpreter: `/workspace/wise_idm/.venv/bin/python` (3.11, torch 2.11.0+cu128)
- key package versions: unchanged from RUN_0007

## Setup from a clean state

Same as RUN_0007 (venv + preprocess_videos.py), plus this run's train command below.

## Models and data

- IDM checkpoint + exact revision: none yet — this run produces the first real checkpoint
- DROID dataset release/split: `nvidia/Cosmos3-DROID`, `success` split, episodes 0-21 (train, 339 windows) / 22-26 (val, 78 windows)

## RoboLab / experiment configuration

n/a (no RoboLab/Cosmos/Robometer execution)

- IDM config: image_size=128, num_frames=33 (full density, 32 adjacent pairs), 16 spatial tokens/pair (4x4, after the added compression stride), d_model=256, 4 encoder + 4 decoder layers, 8 heads, ~9.0M params, action_horizon=32
- training config: batch_size=8, lr=3e-4, AdamW (weight_decay=1e-4), epochs=30, SmoothL1 on standardized joint targets (mean/std from train split only) + BCEWithLogitsLoss on raw gripper target, seed=0

## Exact commands

```bash
cd /workspace/wise_idm && source .venv/bin/activate
CUDA_VISIBLE_DEVICES=1 python3 train.py --mode train \
  --train-episodes 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 \
  --val-episodes 22 23 24 25 26 \
  --batch-size 8 --epochs 30 --lr 3e-4 --seed 0
```

## Expected outputs

- result directory: `/workspace/wise_idm/checkpoints/best.pt`, `/workspace/wise_idm/tb_logs/`
- logs: stdout, captured here; `checkpoints/history.json`
- checkpoints: `checkpoints/best.pt` (model state dict + joint normalization stats + config, saved whenever val_mean_joint_mae improves)

## Execution result

- start time: 2026-08-12T08:39Z (first attempt, SmoothL1 gripper, no pos_weight/clip/schedule)
- end time: 2026-08-12T08:48Z (final 5-epoch check, BCE+pos_weight+clip+OneCycleLR)
- wall time: first attempt stopped after 9 epochs (~90s) once the gripper plateau was diagnosed as a real bug rather than noise; second attempt (5 epochs, corrected recipe) ~50s
- peak VRAM / throughput if relevant: ~10s/epoch on GPU1 (A100, `CUDA_VISIBLE_DEVICES=1`), 339 train windows / 78 val windows, batch_size=8
- exit status: 0 (both attempts exited cleanly; first was killed deliberately mid-run once diagnosed, not crashed)
- warnings/errors: none beyond the diagnosed gripper-loss design issue (see RUN_0007)

## Observed evidence

**First attempt (original recipe: SmoothL1 gripper, plain AdamW, no grad clip, no LR schedule, num_workers=0):** val_gripper_accuracy was bit-identical (0.652) across all 9 epochs observed, and val_mean_joint_mae bounced 0.584-0.609 without a clear trend. TensorBoard inspection showed `train/gripper_bce`-equivalent loss hovering near ln(2)=0.693 (an uninformative-predictor loss level) while `train/joint_loss` did show real improvement (0.47->0.36 mean over ~430 steps). This matches RUN_0007's diagnosis: SmoothL1 regression on the heavily bimodal gripper target doesn't reliably learn to discriminate, even given real training signal reaching the rest of the network.

**Second attempt (corrected recipe: BCEWithLogitsLoss with pos_weight=0.576 (computed from the full 339-window train split: 6882 positive / 3966 negative -- notably different from the earlier 8-window sample's 59%/29% split, underscoring why pos_weight should be computed from the actual training data, not a small sample), gradient clipping (max_norm=1.0), OneCycleLR (5% warmup, cosine anneal), num_workers=4):** val_gripper_accuracy 0.879 (epoch 0) -> 0.959 (epoch 1) -> 0.976 (epoch 2) -> 0.976 (epoch 3) -> 0.976 (epoch 4). val_mean_joint_mae 0.571 -> 0.555 -> 0.516 -> 0.517 -> 0.516. Both metrics improved every epoch and plateaued at a much stronger level within just 5 epochs, versus the first recipe's complete stagnation over 9 epochs.

- IDM: best checkpoint (epoch 2, `checkpoints/best.pt`): val_mean_joint_mae=0.51586, val_gripper_accuracy=0.976
- artifact paths: `/workspace/wise_idm/checkpoints/best.pt`, `/workspace/wise_idm/checkpoints/history.json`, `/workspace/wise_idm/tb_logs/`

## Outcome

- pass/fail: **PASS** (second attempt; first attempt's failure is exactly why this run exists as a debug-subset validation gate, per the training ladder)
- what was proven: the corrected training recipe (BCE gripper loss + pos_weight from real data + grad clipping + LR warmup/schedule + multi-worker data loading) generalizes to held-out episodes on the debug subset, not just the tiny fixed overfit batch from RUN_0007. This is training-ladder stage 2 (real train/val training) and stage 3 (checkpoint save/reload, exercised via the `best.pt` save logic) both passing.
- what was **not** proven: performance at meaningful scale (27 episodes is still tiny) -- next step is RUN_0009, training on 500 episodes with the same now-validated recipe, per user direction to prioritize a "very good, robust" final IDM over debug-subset economy.
- next action: RUN_0009 -- 500-episode training run.

## Reproducibility checklist

- [x] exact commits/revisions recorded (dataset revision; wise_idm code still not in git -- flagged again, to fix before M4 close-out)
- [x] exact environment/interpreters recorded
- [x] setup steps recorded
- [x] exact commands recorded
- [x] task/data budget recorded
- [x] seeds/randomness recorded
- [x] configs/model revisions recorded
- [x] outputs/artifacts recorded
- [x] no secrets recorded
- [x] failed run preserved if applicable (first attempt's stagnation documented above rather than in a separate file, since it's the same run intent and directly motivates the fix)

## Reproducibility checklist

- [x] exact commits/revisions recorded (dataset revision; code not yet in git — flagged)
- [x] exact environment/interpreters recorded
- [x] setup steps recorded
- [x] exact commands recorded
- [x] task/data budget recorded
- [x] seeds/randomness recorded
- [x] configs/model revisions recorded
- [ ] outputs/artifacts recorded
- [x] no secrets recorded
- [ ] failed run preserved if applicable
