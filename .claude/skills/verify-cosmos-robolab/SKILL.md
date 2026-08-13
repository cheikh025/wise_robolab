---
name: verify-cosmos-robolab
description: Verify Cosmos3-Edge-Policy-DROID end-to-end through RoboLab, including exact checkpoint/defaults, client/server formats, native rollout-video retention, stochastic candidate diversity, and a measured B=1 baseline. Use after RoboLab setup and whenever Cosmos integration changes.
---

# Verify Cosmos3-Edge with RoboLab

## Validation budget and mandatory run record

When this skill is being used for setup, smoke, debugging, or milestone validation, use the **smallest sufficient** task/data budget. For RoboLab, default to 1 task/1 episode for basic wiring and usually 1–3 representative tasks with only a few episodes each for integration validation. Expand only when the current question cannot be answered reliably on the small panel. Small validation panels prove engineering correctness; they do not support performance claims.

Before every non-trivial execution launched by this skill, create `research/runs/RUN_XXXX_<slug>.md` from `research/runs/RUN_TEMPLATE.md`, fill the known setup/config/commands before launch, and finalize it with outputs/results/failures afterward. Keep failed-run records. Update `research/RUNBOOK.md` as well when the run verifies a reusable setup or canonical command.

## Goal

Prove the frozen Cosmos path is correct before adding Robometer or WISE.

Do not assume prior successful manual work is still valid; rediscover the active implementation and record it.

## Inspect current sources

Inspect:

- RoboLab `policies/cosmos3/` client/run code;
- current NVIDIA cosmos-framework RoboLab server;
- current `nvidia/Cosmos3-Edge-Policy-DROID` model card/revision;
- relevant current official cookbook/server docs.

Watch for drift between Nano defaults and Edge-specific requirements. Verify the **actual loaded checkpoint at runtime**, not only the command string.

## Verify environments are isolated

Record exact RoboLab and Cosmos interpreters. Do not merge incompatible Python/Torch environments merely for convenience.

## Verify protocol and semantics

From source + runtime confirm:

- input camera composition/keys;
- current robot state fields;
- prompt/instruction formatting;
- action space and dimension;
- chunk length;
- conditioning/control rate;
- gripper post-processing;
- server randomness/seed behavior;
- response fields;
- whether video decoding is available and how it is enabled.

Compare the server's ready/config line to the client/environment expectations.

## B=1 end-to-end smoke

Run one small RoboLab task with Cosmos through the unmodified selection semantics. Verify request -> server inference -> returned action -> RoboLab execution -> episode output.

If it fails, diagnose at this layer before proceeding.

## Retain native imagined rollout video

If the server already produces native generated video but the client discards it, make the minimum clean patch to preserve it with candidate metadata. Do not regenerate an action-conditioned future separately.

Save/inspect at least one decoded rollout. Verify frame count/layout empirically instead of assuming model-card geometry.

Ensure enabling video return does not alter the action chunk or baseline control behavior except for expected runtime/memory overhead.

## Verify same-context candidate diversity

Before Best-of-K, take one fixed pre-execution context and request multiple candidates without changing observation/state/instruction. Measure:

- action pairwise distances;
- video differences or lightweight perceptual statistics;
- seed metadata if available.

Reject a Best-of-K setup that silently returns duplicates.

## Measure B=1 baseline

Choose a small initial task panel from RoboLab that is reproducible and useful for bring-up. Record exact tasks/episodes/seeds/simulator stack. This is the Cosmos baseline for later selector comparisons.

Do not claim the public RoboLab leaderboard score unless you actually run the matching full protocol.

## Record

Create a progress report, commit the exact integration patch, update `research/RUNBOOK.md`, append the experiment, and update `research/STATE.md`.

M1 passes only when normal Cosmos inference, video retention, diversity, and B=1 evidence are all verified.

Then hand off to `/validate-robometer-on-cosmos`.
