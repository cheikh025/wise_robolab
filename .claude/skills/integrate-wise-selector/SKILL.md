---
name: integrate-wise-selector
description: Integrate full WISE selection into RoboLab/Cosmos using separable action-quality, IDM-consistency, and Robometer-progress scores with explicit candidate-relative calibration, logging, configurable ablations, and no speculative environment execution.
---

# Integrate Full WISE

## Validation budget and mandatory run record

When this skill is being used for setup, smoke, debugging, or milestone validation, use the **smallest sufficient** task/data budget. For RoboLab, default to 1 task/1 episode for basic wiring and usually 1–3 representative tasks with only a few episodes each for integration validation. Expand only when the current question cannot be answered reliably on the small panel. Small validation panels prove engineering correctness; they do not support performance claims.

Before every non-trivial execution launched by this skill, create `research/runs/RUN_XXXX_<slug>.md` from `research/runs/RUN_TEMPLATE.md`, fill the known setup/config/commands before launch, and finalize it with outputs/results/failures afterward. Keep failed-run records. Update `research/RUNBOOK.md` as well when the run verifies a reusable setup or canonical command.

## Preserve the candidate abstraction

Define one candidate object/record containing at minimum:

- candidate ID / generation seed if available;
- action chunk;
- imagined future/video reference;
- raw `r_exec`;
- raw `r_cons`;
- raw/per-frame `r_task`;
- calibrated component scores;
- fused WISE score;
- admissibility/hard-failure reason;
- generation/scoring latency.

Do not pass loose arrays that can accidentally mismatch actions and videos.

## r_exec

Implement action bounds/non-finite checks and temporal regularity for the **verified absolute joint-position control representation**. Incorporate previous executed action/chunk boundary where methodologically appropriate.

Treat gripper separately from continuous joint commands.

Keep raw penalty subterms for diagnostics.

## r_cons

Run the validated IDM on each candidate's imagined transition using the same preprocessing as M5, including initial proprioception. Compare IDM reconstruction to that candidate's Cosmos action in normalized action space, with separate gripper treatment.

## r_task

Use exactly the Robometer path validated in M2/M3. Do not silently change view or scalarization while adding WISE.

## Calibration

Implement candidate-relative calibration as an explicit strategy/config. Start with one defensible method, but keep raw scores and make alternatives easy to test.

Handle zero-variance candidate sets safely. Calibration must not produce NaNs or artificial preference when a component is uninformative.

## Fusion

Expose nonnegative weights and selectors for:

- each single component;
- every useful two-component combination;
- full three-component WISE.

Hard-invalid candidates may receive `-inf` before fusion.

## Correctness tests

Add unit/integration tests for:

- candidate/action/video pairing;
- calibration with constant/outlier inputs;
- gripper handling;
- deterministic selection ties;
- invalid candidate rejection;
- all K generated before action execution;
- scorer failure behavior.

## Smoke test

Run one task/episode with verbose candidate logs. Manually inspect at least several decisions to ensure selected action belongs to the candidate with the expected fused score.

M6 passes before large benchmark experiments begin.

Then hand off to `/evaluate-wise-robolab`.
