# Frozen DROID IDM Design

This document is the production contract for the first WISE IDM. Changes require a recorded experiment or an explicit replacement decision; they must not be introduced silently in training or inference code.

## Purpose and boundary

The IDM is a direct inverse-dynamics model:

`three-view RGB video -> 32 x 8 commanded actions`.

It is trained only on DROID data. Cosmos is not a training dependency and no Cosmos-generated dream is used as an IDM target. Cosmos enters later, during WISE candidate scoring, when the frozen IDM checks whether a generated dream implies the action paired with that dream.

The production IDM has no learned video-action verifier, auxiliary action encoder, proprioceptive input, initial robot-state input, language input, task input, success/failure input, or lab identity input.

## Pinned dataset and split

- source: `nvidia/Cosmos3-DROID`;
- source revision: `5c11a20accb11497270a5247a7f1e66ad04c956c`;
- eligibility: episode length at least 33 frames;
- eligible population at the pinned revision: 71,253 episodes, comprising 57,584 successes and 13,669 failures;
- production training set: 21,000 episodes;
- production validation set: 1,000 episodes;
- no test split is created for this IDM run.

The lab x outcome allocation preserves the natural eligible-population proportions. Quotas are recomputed only after the unavoidable 33-frame eligibility rule. A lab is not oversampled merely because RoboLab is the downstream target.

| Lab | Train success | Train failure | Train total | Validation success | Validation failure | Validation total |
|---|---:|---:|---:|---:|---:|---:|
| AUTOLab | 2,067 | 965 | 3,032 | 98 | 46 | 144 |
| CLVR | 1,385 | 110 | 1,495 | 66 | 5 | 71 |
| GuptaLab | 328 | 47 | 375 | 16 | 2 | 18 |
| ILIAD | 610 | 335 | 945 | 29 | 16 | 45 |
| IPRL | 1,302 | 364 | 1,666 | 62 | 17 | 79 |
| IRIS | 934 | 50 | 984 | 45 | 2 | 47 |
| PennPAL | 823 | 26 | 849 | 39 | 1 | 40 |
| RAD | 294 | 136 | 430 | 14 | 7 | 21 |
| RAIL | 1,592 | 736 | 2,328 | 76 | 35 | 111 |
| REAL | 1,031 | 433 | 1,464 | 49 | 21 | 70 |
| RPL | 574 | 157 | 731 | 27 | 8 | 35 |
| TRI | 5,332 | 493 | 5,825 | 254 | 24 | 278 |
| WEIRD | 699 | 177 | 876 | 33 | 8 | 41 |
| **Total** | **16,971** | **4,029** | **21,000** | **808** | **192** | **1,000** |

Selection is deterministic and auditable:

1. join pinned Cosmos3-DROID episode metadata with raw DROID scene identity;
2. apply only `length >= 33` eligibility;
3. reserve validation by stable, shard-aware ordering while satisfying the exact joint quotas;
4. exclude every validation scene from training, then select the exact training quotas with shard-aware ordering;
5. record episode, scene, outcome, lab, video-shard, source-revision, and manifest digests;
6. audit both episode shares and the resulting window/shard shares.

Do not delete frames, remove idle periods, relabel episodes, or treat idle and active segments as different datasets. All selected episode frames remain eligible for window construction. Shard-aware selection reduces scattered I/O; scene disjointness, exact quotas, and source fidelity take priority over minimizing shard overlap.

## Window and label contract

- three synchronized views: wrist, exterior 1, exterior 2;
- 33 consecutive RGB frames per view at 15 Hz;
- 32 labels, each containing 7 absolute commanded joint positions and 1 gripper command;
- action row `t` labels the transition from frame `t` to frame `t+1`;
- a window starting at `s` therefore uses frames `s..s+32` and action rows `s..s+31`;
- training start stride: 16;
- validation start stride: 32;
- end-align the final window so the episode tail is represented.

The joint target comes from DROID commanded joint-position fields, not the convenience velocity-style `action` field. Raw DROID gripper commands are continuous in `[0, 1]`; threshold them at `> 0.5` for both training and execution-facing comparison, with `0 = open` and `1 = closed`. The Cosmos RoboLab response already restores this external convention, so the IDM/scorer must not apply another polarity flip.

## Visual preprocessing

Each camera image is resized with aspect-preserving letterboxing to `128 x 224` using the same canonical implementation in training, validation, checkpoint verification, and dream inference. Do not substitute a direct stretch at inference.

For each of the 32 intervals, concatenate its adjacent RGB frames along the channel axis to form a 6-channel motion input. The three camera streams remain distinct until cross-view fusion.

The decoded Cosmos dream contract is fixed:

- tensor shape: `33 x 528 x 640 x 3` RGB frames;
- split row: 360;
- wrist: rows `0:360`, columns `0:640` (`360 x 640`);
- exterior 1: rows `360:528`, columns `0:320` (`168 x 320`);
- exterior 2: rows `360:528`, columns `320:640` (`168 x 320`).

The request mosaic may be `540 x 640`, but the decoded dream consumed by the IDM is `528 x 640`. Inference must validate this exact geometry and use the fixed split instead of estimating a seam from image content.

## Frozen architecture

1. A shared ResNet-50 with torchvision `IMAGENET1K_V2` weights processes every 6-channel adjacent-frame pair. Initialize the widened first convolution by repeating the pretrained RGB weights and averaging the two copies.
2. Use the backbone through `layer3`, producing a `1024 x 8 x 14` feature map for each camera and interval.
3. Apply a full-channel spatial softmax. The expected `(x, y)` coordinate for each of 1,024 channels gives 2,048 spatial coordinates, projected to one width-512 token.
4. Add learned camera identities to the three tokens for an interval. A learned fusion token attends to them through a 2-layer cross-view Transformer.
5. Add learned time identities to the 32 fused interval tokens. Process them with a bidirectional 6-layer temporal Transformer: width 512, 8 attention heads, FFN width 2,048.
6. Apply aligned direct heads at every interval: `Linear(512, 7)` for joints and `Linear(512, 1)` for the binary gripper.

There is no action-query decoder. The output token at interval `t` directly predicts action `t`, which keeps the temporal alignment explicit.

## Objective and checkpoint contract

- compute joint mean and standard deviation from training windows only;
- train the seven standardized joint channels with SmoothL1 loss;
- train the thresholded gripper with weighted binary cross entropy;
- store normalization statistics, architecture/preprocessing identifiers, pinned source revision, selection digests, and selection audits in the checkpoint;
- report validation joint error and binary gripper accuracy, including per-joint diagnostics;
- reject a checkpoint whose architecture, preprocessing, manifests, normalization, or pinned data identity does not match the production contract.

Do not add a smoothness penalty or an idle penalty. Those objectives would change the meaning of preserved DROID behavior rather than merely reconstructing its commanded actions.

## WISE consistency use

For a Cosmos candidate pair `(dream, action)`, run the IDM on the complete 33-frame dream only. Let `ahat` be its 32-step prediction and `a` the paired Cosmos action. Using training joint standard deviations `sigma`:

`E_joint = mean_{t,j} |(ahat[t,j] - a[t,j]) / sigma[j]|`

`S_joint = exp(-E_joint)`

`S_gripper = mean_t 1[threshold(ahat[t,7]) = threshold(a[t,7])]`

`r_cons = 0.5 * S_joint + 0.5 * S_gripper`.

This is a deterministic comparison, not a learned verifier. It measures internal agreement between a generated future and its paired action; it does not claim that the future will occur in RoboLab.
