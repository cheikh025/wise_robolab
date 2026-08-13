---
name: build-droid-idm
description: Build and train the DreamZero-inspired inverse-dynamics model for DROID/Cosmos, using three views, correct joint-position+gripper targets, initial proprioception, staged data validation, and reproducible checkpoints. Use after the Robometer-only baseline is working.
---

# Build the DROID IDM

## Validation budget and mandatory run record

When this skill is being used for setup, smoke, debugging, or milestone validation, use the **smallest sufficient** task/data budget. For RoboLab, default to 1 task/1 episode for basic wiring and usually 1–3 representative tasks with only a few episodes each for integration validation. Expand only when the current question cannot be answered reliably on the small panel. Small validation panels prove engineering correctness; they do not support performance claims.

Before every non-trivial execution launched by this skill, create `research/runs/RUN_XXXX_<slug>.md` from `research/runs/RUN_TEMPLATE.md`, fill the known setup/config/commands before launch, and finalize it with outputs/results/failures afterward. Keep failed-run records. Update `research/RUNBOOK.md` as well when the run verifies a reusable setup or canonical command.

## Read design and sources

Read `research/IDM_DESIGN.md`, current DROID schema/docs, current Cosmos action representation, and any locally available DreamZero IDM reference/code.

The design is intentionally close to DreamZero's IDM principles but adapted to DROID/Cosmos. Do not blindly copy LIBERO shapes.

## Verify DROID labels before modeling

Start with the smallest DROID debug subset available.

Inspect actual sample tensors/fields and prove the target is:

- seven **commanded joint positions**;
- commanded gripper;
- correct temporal alignment to the video frames.

Do not accidentally use a convenience action field representing joint velocity + gripper.

Create explicit alignment tests/visualizations or numerical sanity checks. Off-by-one frame/action alignment can make the model look trainable while destroying the consistency signal.

## Primary input design

Use three views as the primary configuration:

- wrist;
- exterior 1;
- exterior 2.

Include initial 7-joint + gripper state explicitly.

Keep camera order/identity deterministic and recorded.

## Architecture

Implement a configurable DreamZero-like IDM:

- adjacent-frame early fusion primary path;
- shared ResNet-like visual trunk or another justified compact CNN;
- preserve spatial grid features;
- project to tokens;
- camera/time/position embeddings;
- small Transformer encoder;
- learned action queries + Transformer decoder;
- 7-D joint regression head;
- gripper head;
- per-channel action statistics stored in checkpoint.

Implement late fusion as an available ablation if practical.

Do not hard-code 25 spatial tokens. Derive feature geometry from current preprocessing/backbone and expose it in config.

## Control compute

For long 3-view clips, estimate token/attention cost before large training. If full attention is excessive, compress spatial/temporal tokens while preserving fine motion signal. Record the rationale.

## Training ladder

1. overfit a tiny batch/window to prove the model and labels can fit;
2. train on debug subset and verify validation metrics;
3. checkpoint/reload test;
4. scale to a meaningful DROID split only after alignment is proven.

Log joint error per dimension, normalized aggregate error, gripper accuracy, training/validation curves, and temporal smoothness/degeneracy indicators.

## Record

Commit model/data/training code, create a progress report, capture system info, record data revision/split, exact config/command/checkpoint, and update runbook/state.

Then hand off to `/validate-droid-idm`.
