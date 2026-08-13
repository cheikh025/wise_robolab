---
name: run-robometer-bestofk
description: Implement and evaluate the Robometer-only Best-of-K selector over native Cosmos world-action candidates in RoboLab. This is the strong pre-IDM test-time-scaling baseline and must preserve same-context candidate generation and paired action/future identity.
---

# Robometer-only Best-of-K

## Validation budget and mandatory run record

When this skill is being used for setup, smoke, debugging, or milestone validation, use the **smallest sufficient** task/data budget. For RoboLab, default to 1 task/1 episode for basic wiring and usually 1–3 representative tasks with only a few episodes each for integration validation. Expand only when the current question cannot be answered reliably on the small panel. Small validation panels prove engineering correctness; they do not support performance claims.

Before every non-trivial execution launched by this skill, create `research/runs/RUN_XXXX_<slug>.md` from `research/runs/RUN_TEMPLATE.md`, fill the known setup/config/commands before launch, and finalize it with outputs/results/failures afterward. Keep failed-run records. Update `research/RUNBOOK.md` as well when the run verifies a reusable setup or canonical command.

## Goal

Implement the simplest serious test-time selector before the IDM:

`same state -> K Cosmos candidates -> Robometer score each future -> execute paired action from highest-scoring candidate`.

## Candidate integrity

At one control decision:

1. freeze the current observation/state/instruction;
2. generate all K candidates before executing any of them;
3. preserve candidate ID, seed if available, action chunk, imagined future, raw Robometer output;
4. select one candidate;
5. execute only the selected candidate's action prefix/chunk;
6. re-observe before the next candidate set.

Never mix the action from one candidate with the video from another.

## Baselines

Under matched settings compare at minimum:

- B=1 / first sample;
- random candidate from K;
- Robometer-selected candidate from K.

Use the same K candidate set when practical for random-vs-Robometer analysis, so differences come from selection rather than generation.

## Start small

Begin on one or a few tasks with enough episodes to catch implementation bugs. Verify selector logs before scaling.

Log for every decision:

- candidate IDs/seeds;
- Robometer raw per-frame predictions and scalar score;
- selected index;
- action chunk summary;
- latency for generation and scoring.

## Receding horizon

Initially preserve the native Cosmos/RoboLab action commitment if that is required for apples-to-apples baseline comparison. Make shorter action prefixes a later explicit experiment rather than silently changing behavior.

## Decision

M3 passes when the selector is correct, stable, and compared against first-sample/random baselines. It does not need to outperform on every small smoke panel to pass engineering validation, but scientific claims require adequate episode counts later.

Then hand off to `/build-droid-idm`.
