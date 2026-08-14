---
name: integrate-wise-selector
description: Integrate full WISE selection into RoboLab/Cosmos using separable action-quality, the frozen vision-only IDM's exact direct full-dream consistency score, and Robometer progress, with complete candidate pairing and no speculative execution.
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

For each candidate, send the complete decoded dream to the frozen IDM and compare its direct prediction with that same candidate's paired Cosmos action only after inference. The candidate action is a comparison target, never an IDM input. Do not provide initial robot state/proprioception, language/instruction, task identity, success/failure, lab/scene identity, Robometer features, or any learned verifier signal to the IDM.

Require the verified production shapes and preprocessing:

- dream: 33 x 528 x 640 x 3 RGB;
- fixed panel split at row 360: wrist 360 x 640, exterior 1 bottom-left 168 x 320, exterior 2 bottom-right 168 x 320;
- aspect-preserving letterbox of each view to 128 x 224;
- IDM output and paired Cosmos action: 32 x 8, with seven absolute joint positions and binary gripper convention `0=open`, `1=closed`.

Reject non-finite or shape-mismatched inputs. Do not add a polarity flip: the Cosmos/RoboLab API response already matches the raw DROID convention.

Compute the raw server score exactly from checkpoint train statistics:

`joint_mae_std_units = mean(abs(idm_joints - cosmos_joints) / train_joint_std)`

`joint_cons = exp(-joint_mae_std_units)`

`gripper_cons = mean((sigmoid(idm_gripper_logit) > 0.5) == (cosmos_gripper > 0.5))`

`r_cons = 0.5 * joint_cons + 0.5 * gripper_cons`

Log all four quantities. Do not replace this direct score with a learned video-action verifier, auxiliary action encoder, action-query decoder, initial-state-conditioned model, or a Cosmos-trained IDM.

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
- exact dream panel split, view order, preprocessing version, and 33-frame/32-action shapes;
- proof that candidate action and proprioception are absent from IDM inputs;
- exact `r_cons` arithmetic against a hand-computed fixture;
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
