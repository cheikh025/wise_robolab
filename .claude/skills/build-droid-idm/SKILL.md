---
name: build-droid-idm
description: Build and train the frozen production vision-only IDM on the pinned Cosmos3-DROID 21K/1K manifests, with three views, exact 33-frame-to-32-action alignment, and reproducible checkpoints. Use after the Robometer-only baseline is working.
---

# Build the DROID IDM

## Validation budget and mandatory run record

Synthetic tensors or tiny debug inputs may be used for implementation checks, but they are not an alternative data split and produce no model-quality claim. Production training uses exactly 21,000 selected episodes and the only model-quality evaluation uses the fixed 1,000-episode validation manifest. Do not create a test split or a pilot evaluation split.

Before every non-trivial execution launched by this skill, create `research/runs/RUN_XXXX_<slug>.md` from `research/runs/RUN_TEMPLATE.md`, fill the known setup/config/commands before launch, and finalize it with outputs/results/failures afterward. Keep failed-run records. Update `research/RUNBOOK.md` as well when the run verifies a reusable setup or canonical command.

## Read design and sources

Read `research/IDM_DESIGN.md` first. It is the source of truth for the frozen data, alignment, preprocessing, architecture, loss, and validation contract. Also verify the current pinned dataset schema and Cosmos/RoboLab action convention from exact source revisions. Do not substitute an older DreamZero-like implementation when it conflicts with the frozen contract.

IDM training is independent of Cosmos inference. Train only on `nvidia/Cosmos3-DROID` at revision `5c11a20accb11497270a5247a7f1e66ad04c956c`; Cosmos-generated dreams and Cosmos actions enter only later when WISE computes `r_cons`.

## Verify DROID labels before modeling

The production split is determined by the exact selection procedure and quotas in `research/IDM_DESIGN.md`:

- filter only unavoidable `length >= 33` eligibility;
- select exactly 21,000 train episodes and 1,000 validation episodes at the natural eligible lab x success/failure proportions;
- keep train and validation scene-disjoint, prefer shard-local blocks, record all quota/scene/shard audits, and never oversample a lab;
- preserve all frames and all behavior, including idle/repeated frames; do not remove or relabel examples based on motion;
- use train stride 16 and validation stride 32, adding one end-aligned tail window when the regular grid does not end at the episode boundary.

Inspect the pinned schema and enforce these target invariants:

- seven commanded **absolute joint positions** plus gripper from the explicit action fields, never a convenience velocity-action field;
- 33 consecutive synchronized frames at 15 Hz produce 32 targets;
- for a window starting at `s`, load frames `s..s+32` and action rows `s..s+31`; action row `t` labels the transition from frame `t` to frame `t+1`;
- threshold raw gripper position with `> 0.5`; production convention is `0=open`, `1=closed` and no additional polarity flip is applied for the Cosmos/RoboLab API response.

Fail closed on missing cameras, bad timestamps, malformed ranges, non-consecutive rows, split leakage, scene leakage, quota mismatch, or a data revision mismatch.

## Primary input design

Use all three synchronized views in fixed, recorded order:

- wrist;
- exterior 1;
- exterior 2.

Inputs are RGB only. Do not provide initial robot state/proprioception, language/instruction, task identity, success/failure, lab identity, scene identity, or any other metadata to the model. Metadata is allowed only for deterministic data selection and audits.

Aspect-preserving letterbox each view to 128 x 224 using the canonical preprocessing recorded in the checkpoint. Never distort the aspect ratio or crop away view content.

## Architecture

Implement the frozen production architecture:

- concatenate each adjacent RGB pair channel-wise to form a six-channel image;
- use one shared ImageNet-v2 ResNet-50 through `layer3`; initialize the six-channel `conv1` by repeating and averaging pretrained RGB weights;
- require the resulting 1024 x 8 x 14 feature geometry;
- apply full-channel spatial softmax to obtain x/y coordinates for all 1,024 channels, then project the 2,048-coordinate descriptor to width 512;
- add learned camera embeddings to the three per-transition camera tokens and fuse them with a fusion token plus a two-layer cross-view Transformer;
- add learned time embeddings to the 32 fused transition tokens and process them with a six-layer, eight-head, width-512, FFN-2048 bidirectional temporal Transformer;
- use time-aligned direct `Linear(512, 7)` and `Linear(512, 1)` heads for standardized joints and binary gripper logits.

Do not add an action-query decoder, learned video-action verifier, auxiliary action encoder, proprioception/state branch, language branch, smoothness penalty, idle-window weighting/filtering, or mandatory alternate-view/fusion architecture.

## Control compute

Keep the frozen 33-frame, three-view input and 32-transition output. Compute or memory optimizations must preserve numerical behavior and the checkpoint contract; an architecture change requires a separately approved experiment.

## Training ladder

1. run unit-level tensor, alignment, selection, preprocessing, and checkpoint round-trip checks;
2. compute per-joint mean/std and gripper class weight from train windows only;
3. train once on the complete frozen 21K manifest using SmoothL1 on standardized joints plus weighted BCE on binary gripper;
4. evaluate checkpoints only on the complete frozen 1K validation manifest and select the checkpoint by the declared validation metric.

Log standardized aggregate and per-joint error, physical-space joint error, gripper accuracy, losses, window/episode/lab/outcome/shard shares, and the exact train/validation manifest digests. Do not report a debug subset as held-out evidence.

## Record

Commit model/data/training code, create a progress report, capture system info, and record the pinned data revision, manifest hashes and audits, exact config/command/checkpoint, preprocessing version, train-only statistics, and validation results. Update runbook/state without rewriting historical receipts.

Then hand off to `/validate-droid-idm`.
