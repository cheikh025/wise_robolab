# RUN_0019 — DROID IDM: stratified-data pilot, 3-view vs 2-view (no proprio)

## Identity

- status: `RUNNING`
- run class: `screen`
- milestone: M4_IDM_TRAIN
- date/time: 2026-08-13 (~00:15Z)
- operator/agent: Claude Code (autonomous /goal run, user-directed IDM rethink)

## Purpose

- exact question this run answers: (1) does lab-stratified training data (13 labs, one contiguous block each, vs the AUTOLab-only data every prior run used) resolve the plateau seen in RUN_0012/13/15/17? Compare 3-view result against RUN_0009's 0.06857. (2) does dropping the right-exterior camera (2-view: wrist+left) cost meaningfully vs the full 3-view, holding data/architecture/everything else fixed?
- pass/fail criterion: n/a (screen/pilot -- directional signal, not a final decision). Short budget (15 epochs) per explicit user direction to keep pilots fast; a full-scale follow-up will use whichever config looks best here.
- why this task/data budget is sufficient: matched to RUN_0009's scale (4805 vs 4169 train windows) for direct comparability, spanning all 13 DROID labs (vs RUN_0009's AUTOLab-only) via one contiguous random block per lab (see RUN_0018-adjacent design notes / conversation record -- first attempt at scattered-individual-episode stratification needed ~217GB download for 696 episodes, redesigned to contiguous-block-per-lab: 20GB for 651 episodes, same window budget).

## Code state

- repo: `/workspace/wise_idm`, commit `2d0e08f` (proprio fully removed, camera count generalized, meta-file multi-part bug fixed)

## Models and data

- DROID dataset: lab-stratified sample, 566 train episodes / 85 val episodes (4805 / 550 windows), spanning all 13 labs (AUTOLab, CLVR, GuptaLab, ILIAD, IPRL, IRIS, PennPAL, RAD, RAIL, REAL, RPL, TRI, WEIRD), one contiguous random block per lab, no train/val overlap. Episode lists: `/tmp/pilot_train_episodes.csv`, `/tmp/pilot_val_episodes.csv`.

## RoboLab / experiment configuration

n/a (no RoboLab/Cosmos/Robometer execution)

- IDM config: v1 architecture (flatten-to-grid tokens), no proprioception (permanent rule), cnn_width=64, d_model=256, 4+4 layers, 8 heads
- Run A (GPU0): `--cameras wrist left right` (3-view)
- Run B (GPU1): `--cameras wrist left` (2-view)
- training config: batch_size=32, lr=3e-4, AdamW, OneCycleLR, grad clip 1.0, BCE gripper + pos_weight, epochs=15 (short pilot budget per explicit user direction), seed=0

## Exact commands

```bash
cd /workspace/wise_idm && source .venv/bin/activate && export HF_HOME=/workspace/.hf_home
CUDA_VISIBLE_DEVICES=0 python3 train.py --mode train --arch v1 --cameras wrist left right \
  --train-episodes $(cat /tmp/pilot_train_episodes.csv | tail -n +2 | tr '\n' ' ') \
  --val-episodes $(cat /tmp/pilot_val_episodes.csv | tail -n +2 | tr '\n' ' ') \
  --batch-size 32 --epochs 15 --lr 3e-4 --seed 0 \
  --out-dir /workspace/wise_idm/checkpoints_pilot_3view --log-dir /workspace/wise_idm/tb_logs_pilot_3view

CUDA_VISIBLE_DEVICES=1 python3 train.py --mode train --arch v1 --cameras wrist left \
  --train-episodes $(cat /tmp/pilot_train_episodes.csv | tail -n +2 | tr '\n' ' ') \
  --val-episodes $(cat /tmp/pilot_val_episodes.csv | tail -n +2 | tr '\n' ' ') \
  --batch-size 32 --epochs 15 --lr 3e-4 --seed 0 \
  --out-dir /workspace/wise_idm/checkpoints_pilot_2view --log-dir /workspace/wise_idm/tb_logs_pilot_2view
```

## Execution result

- start time: 2026-08-13T~00:15Z
- end time: TBD
- exit status: TBD

## Observed evidence

- IDM: TBD -- compare both against RUN_0009's 0.06857

## Outcome

- pass/fail: TBD
- next action: TBD -- winner scales up to the full stratified budget (~39k windows)

## Reproducibility checklist

- [x] exact commits/revisions recorded
- [x] exact environment/interpreters recorded
- [x] exact commands recorded
- [x] task/data budget recorded
- [x] seeds/randomness recorded
- [x] configs/model revisions recorded
- [ ] outputs/artifacts recorded
- [x] no secrets recorded
