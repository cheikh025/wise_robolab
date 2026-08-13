---
name: validate-robometer-on-cosmos
description: Install and validate general Robometer-4B offline on saved RoboLab real trajectories and Cosmos-generated dreams before any online Best-of-K coupling. Use after Cosmos rollout video is available.
---

# Validate Robometer on Cosmos/RoboLab Data

## Validation budget and mandatory run record

When this skill is being used for setup, smoke, debugging, or milestone validation, use the **smallest sufficient** task/data budget. For RoboLab, default to 1 task/1 episode for basic wiring and usually 1–3 representative tasks with only a few episodes each for integration validation. Expand only when the current question cannot be answered reliably on the small panel. Small validation panels prove engineering correctness; they do not support performance claims.

Before every non-trivial execution launched by this skill, create `research/runs/RUN_XXXX_<slug>.md` from `research/runs/RUN_TEMPLATE.md`, fill the known setup/config/commands before launch, and finalize it with outputs/results/failures afterward. Keep failed-run records. Update `research/RUNBOOK.md` as well when the run verifies a reusable setup or canonical command.

## Scope

This milestone is deliberately offline. Do not couple Robometer into the control loop yet.

Prove:

1. Robometer is installed/running correctly;
2. its progress signal is meaningful enough on the exact DROID-style data we intend to score.

## Inspect current Robometer source

Use the current official Robometer repository/model/paper, not only bootstrap notes. Determine exact Python/Torch requirements, checkpoint loading, video preprocessing/subsampling, per-frame progress output, and any success/preference outputs.

Create/use a separate Robometer environment if required by dependencies.

## Build a clean offline dataset

Use saved RoboLab sensor trajectories and saved Cosmos dreams from M1. Preserve the exact environment instruction string.

Prefer examples where the RoboLab event/state log makes progress interpretable, including successful and failed/partial trajectories when available.

## View handling

Robometer is initially treated as a single-video scorer. Score DROID views separately unless current primary-source evidence justifies a multi-camera input representation.

Measure at least:

- wrist;
- exterior 1;
- exterior 2.

Do not send a tiled composite merely because Cosmos uses one internally unless Robometer's training/inference distribution supports it.

If dream and real views have different resolution, record the confound and test resize/upscale only as an explicit ablation.

## Validate progress behavior

For each view, inspect the per-frame progress curve relative to RoboLab's task/event timeline. Useful evidence includes:

- successful trajectory progress generally increasing toward completion;
- lower progress on clear failures/non-progress;
- generated dream signal that is not universally flat/NaN;
- consistency across repeated scoring;
- sensitivity to the exact task instruction.

A model that loads successfully but emits an uninformative constant is not milestone success.

## Define the scalar score

Choose and record the initial `r_task` scalarization. Candidate options include final progress or final-minus-initial progress. Keep raw per-frame outputs so the choice can be revisited.

Do not hide this design choice.

## Measure cost

Measure Robometer latency, peak VRAM, and batching opportunities on the actual GPU. This constrains affordable K.

## Record

Create a progress report, store scripts/configs in the repo when they are reusable, update the Robometer section of `research/RUNBOOK.md`, append the experiment, and update `research/STATE.md`.

M2 passes only when at least one documented input/view path gives meaningful progress behavior.

Then hand off to `/run-robometer-bestofk`.
