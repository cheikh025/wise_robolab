# Initial DROID IDM Design

This is the starting design, not an immutable architecture.

## Purpose

Infer the DROID/Cosmos action chunk represented by a short multi-view transition so WISE can compare:

`Cosmos native action` vs `IDM(imagined future)`.

## Primary input

- DROID-style **three views**: wrist + exterior 1 + exterior 2;
- current/initial robot proprioception: seven joint positions + gripper state at minimum;
- video sequence aligned to the target action chunk;
- language is optional for the IDM and should not be included by default unless experiments show it is needed.

Two-view variants (wrist + one exterior) are efficiency/ablation candidates, not the primary starting point.

## Architecture family

Follow the DreamZero IDM design principles:

1. adjacent-frame pairwise early fusion as primary motion encoding;
2. shared CNN visual backbone;
3. preserve a spatial feature grid instead of global average pooling;
4. project spatial features into Transformer tokens;
5. add camera, time/interval, and spatial-position identities;
6. Transformer encoder for multi-view/multi-time context;
7. learned action queries in a Transformer decoder;
8. output one action per target action step in parallel;
9. separate continuous joint regression from gripper prediction.

Keep a late-fusion mode as an ablation/robustness option for generated-video flicker.

## Do not hard-code LIBERO's 25 spatial tokens

The old 25 arose from a particular 160x160 input and stride-32 backbone. For DROID/Cosmos, choose crop/resize/backbone/token grid from the actual input geometry and compute budget.

Preserve spatial localization; the exact grid size is a design variable.

## Output target

Primary target for Cosmos compatibility:

- 7 commanded joint-position channels;
- 1 commanded gripper channel;
- target horizon matched to the verified Cosmos action chunk used in RoboLab (expected to be 32 in the current path, but verify at runtime).

Use DROID's `action_dict/joint_position` and `action_dict/gripper_position` (or exact equivalent in the chosen loader). Do **not** accidentally train against DROID's convenience `action` field if it represents joint velocity + gripper.

## Normalization/loss

- store per-joint mean/std in the checkpoint;
- regress standardized joint targets with robust regression (SmoothL1 is the starting point);
- use a gripper loss appropriate to the executed representation;
- log per-joint validation error, aggregate normalized error, gripper accuracy, and temporal diagnostics.

## Compute scaling

A literal 3-view x 32-interval x dense spatial-grid full-attention model can become expensive. Preserve the core motion/spatial principles while allowing:

- spatial pooling/compression after the CNN;
- temporal subsampling or learned compression;
- factorized attention;
- fewer visual tokens;
- lower transformer width/layers.

Do not solve compute by silently dropping a camera before measuring the trade-off.
