---
name: validate-droid-idm
description: Validate the trained DROID IDM on held-out real DROID trajectories and Cosmos-generated imagined rollouts, including temporal alignment, per-joint/gripper metrics, view/fusion ablations, domain shift, and consistency-score behavior before full WISE integration.
---

# Validate the DROID IDM

## Validation budget and mandatory run record

When this skill is being used for setup, smoke, debugging, or milestone validation, use the **smallest sufficient** task/data budget. For RoboLab, default to 1 task/1 episode for basic wiring and usually 1–3 representative tasks with only a few episodes each for integration validation. Expand only when the current question cannot be answered reliably on the small panel. Small validation panels prove engineering correctness; they do not support performance claims.

Before every non-trivial execution launched by this skill, create `research/runs/RUN_XXXX_<slug>.md` from `research/runs/RUN_TEMPLATE.md`, fill the known setup/config/commands before launch, and finalize it with outputs/results/failures afterward. Keep failed-run records. Update `research/RUNBOOK.md` as well when the run verifies a reusable setup or canonical command.

## Phase 1 — held-out real DROID

Evaluate on held-out trajectories not used for training.

Report:

- normalized and physical/action-space error;
- per-joint metrics;
- gripper accuracy/calibration as appropriate;
- error versus time in chunk;
- simple temporal diagnostics.

Inspect qualitative failure cases, not only mean loss.

## Alignment stress tests

Test deliberate temporal offsets where practical. Correct alignment should outperform nearby wrong offsets. If not, question whether the model is reading action-relevant motion or merely regressing priors.

## View/fusion evidence

Primary model is three-view. When compute allows, compare:

- 3 views;
- wrist + ext1;
- wrist + ext2;
- early vs late fusion.

Use these as evidence, not mandatory exhaustive grid search.

## Phase 2 — Cosmos imagined futures

Run the IDM on decoded Cosmos dreams from the same format that full WISE will use.

For each candidate compare reconstructed action to Cosmos's co-generated action and log a normalized discrepancy. Characterize:

- consistency score distribution;
- relation to candidate diversity;
- obvious low-consistency examples;
- dream artifacts/flicker sensitivity;
- difference between real-video and dream-video input distributions.

Remember: high internal consistency does not prove the dream is physically correct.

## Calibration readiness

Estimate useful per-channel scales/statistics for `r_cons`. Do not choose fusion weights yet solely from one tiny sample.

## Exit

M5 passes only when the IDM has credible held-out real-data performance and produces non-degenerate, interpretable dream consistency scores.

Then hand off to `/integrate-wise-selector`.
