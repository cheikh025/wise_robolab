# RUN_0020 - Production three-view vision-only IDM

## Identity

- status: `PLANNED_TRAINING`; implementation preflight completed, data/training not started
- run class: production M4 training
- milestone: M4_IDM_TRAIN
- date: 2026-08-13

## Question

Train and verify the one accepted production IDM on the frozen DROID selection. This is not an architecture, view, or data-size pilot.

## Frozen contract

- source: `nvidia/Cosmos3-DROID@5c11a20accb11497270a5247a7f1e66ad04c956c`
- selection: 21,000 train and 1,000 raw-scene-disjoint validation episodes using the exact eligible lab x outcome quotas in `research/IDM_DESIGN.md`; no test split
- samples: three views, 33 consecutive frames at 15 Hz, actions at rows 0-31 for visual gaps 0->1 through 31->32; train stride 16 and validation stride 32 with an end-aligned tail
- model: `wise_resnet50_transformer_v1`, vision only, 128x224 letterbox, direct 32x8 output; no proprioception, language, action encoder, verifier, or Cosmos training input
- loss: standardized SmoothL1 for seven joints plus weighted binary gripper BCE

## Code preflight

The separate `wise_idm` repository contains catalog construction, deterministic manifest selection/audit, canonical video preprocessing, the model, DDP training/resume, reload verification, dream inference, and the HTTP score server. Focused CPU tests cover selection, episode/scene overlap, window alignment, pair-stem initialization, spatial softmax, output shape, panel geometry, and short pipe reads. The production GPU path has not yet run.

## Commands

Use the canonical commands in `research/RUNBOOK.md`. Before launch, record the final `wise_idm` commit, manifest/audit SHA256 values, data/cache paths, environment/package versions, GPU state, and exact command here.

## Required outputs

- `catalog.parquet`, `train_21k.csv`, `val_1k.csv`, and `selection_audit.json`
- preprocessing shard audit and complete caches for both manifests
- `best.pt`, `last.pt`, TensorBoard/history output, and runtime/VRAM measurements
- reloaded metrics on the exact 1K validation manifest, including per-joint MAE and gripper accuracy
- at least one fixed-layout Cosmos dream inference result after real-data validation passes

## Result

Pending. Do not enter a metric or milestone decision until the complete training and fixed-manifest reload verification have finished.
