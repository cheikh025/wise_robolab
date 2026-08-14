---
name: validate-droid-idm
description: Validate the frozen production vision-only IDM on the sole fixed 1K DROID validation manifest, then verify direct full-dream consistency scoring before WISE integration.
---

# Validate the DROID IDM

## Validation budget and mandatory run record

Use synthetic/tiny inputs only for wiring and failure reproduction. The sole model-quality evaluation is the complete frozen 1,000-episode validation manifest specified in `research/IDM_DESIGN.md`. Do not create a test split, second validation sample, pilot evaluation, or post-hoc subset. Do not tune the manifest or quotas after observing metrics.

Before every non-trivial execution launched by this skill, create `research/runs/RUN_XXXX_<slug>.md` from `research/runs/RUN_TEMPLATE.md`, fill the known setup/config/commands before launch, and finalize it with outputs/results/failures afterward. Keep failed-run records. Update `research/RUNBOOK.md` as well when the run verifies a reusable setup or canonical command.

## Phase 1 - fixed real-DROID validation

Before scoring, verify the checkpoint and data contract: pinned `nvidia/Cosmos3-DROID` revision, exact 21K/1K manifest digests and quotas, scene disjointness, train stride 16, validation stride 32 with end-aligned tails, preprocessing version, train-only joint statistics, and the frozen architecture identifier. Reject mismatches.

Evaluate every window in the fixed 1K manifest. No validation episode may occur in training and no validation scene may overlap a training scene.

Report:

- standardized and physical/action-space joint error;
- per-joint metrics and error versus the 32 transition positions;
- binary gripper accuracy and class-conditional behavior;
- error versus time in chunk;
- loss and window shares by lab, success/failure, and source shard so window overlap is visible rather than mistaken for episode balance.

Inspect qualitative failure cases, not only mean loss.

## Alignment stress tests

The data loader must enforce 33 consecutive synchronized RGB frames and 32 consecutive action rows, with row `t` labeling frame `t -> t+1`. Unit-level deliberate-offset checks are allowed for alignment debugging; they do not define extra evaluation datasets or replace the fixed 1K result.

## Frozen input and architecture

Validation uses all three views and the same 128 x 224 aspect-preserving letterbox as training. It must instantiate the ResNet-50-layer3 adjacent-pair encoder, full-channel spatial softmax, two-layer cross-view fusion Transformer, six-layer bidirectional temporal Transformer, and aligned direct action heads from the checkpoint contract.

There is no required view-count, early/late-fusion, query-decoder, backbone, proprioception, language, or learned-verifier ablation campaign. Any future architecture ablation is a separately approved experiment and must not delay or contaminate validation of this production run.

## Phase 2 - WISE scoring readiness

This is an integration check, not IDM training and not a second held-out model-quality split. Run the frozen IDM directly on complete decoded Cosmos candidate dreams using the exact production preprocessing. Do not provide initial state/proprioception, language, candidate action, task, success, or lab metadata to the IDM.

Require the verified 33 x 528 x 640 RGB dream transport. Split at row 360 into wrist 360 x 640, exterior 1 bottom-left 168 x 320, and exterior 2 bottom-right 168 x 320; letterbox each view to 128 x 224.

For each candidate, predict one 32 x 8 action directly from the full dream and compare it only afterward with that candidate's paired Cosmos 32 x 8 action. Log:

- standardized joint MAE, `exp(-joint_mae_std_units)`, binary gripper agreement, and final `r_cons`;
- consistency-score distribution;
- relation to candidate diversity;
- obvious low-consistency examples;
- dream artifacts/flicker sensitivity;
- difference between real-video and dream-video input distributions.

Remember: high internal consistency does not prove the dream is physically correct.

## Calibration readiness

Use the train-only seven-joint standard deviations stored in the checkpoint. The server score is fixed:

`joint_mae_std_units = mean(abs(idm_joints - cosmos_joints) / train_joint_std)`

`joint_cons = exp(-joint_mae_std_units)`

`gripper_cons = mean((sigmoid(idm_gripper_logit) > 0.5) == (cosmos_gripper > 0.5))`

`r_cons = 0.5 * joint_cons + 0.5 * gripper_cons`

The API action convention already matches raw DROID/RoboLab (`0=open`, `1=closed`); do not apply another polarity flip.

## Exit

M5 passes only when the complete fixed-1K validation result is credible, checkpoint verification reproduces it, and the exact direct dream/action score is finite, paired correctly, and non-degenerate on recorded candidate examples.

Then hand off to `/integrate-wise-selector`.
