# Current Research State

Status: `IN_PROGRESS`

Current milestone: `M4_IDM_TRAIN` (M0, M1, M2, and M3 passed)

Working RoboLab repo: `https://github.com/cheikh025/RoboLab`, branch `wise/m0-setup`. Upstream is `https://github.com/NVlabs/RoboLab`.

## Accepted production IDM

The production IDM contract is frozen in `research/IDM_DESIGN.md` and implemented in the separate `wise_idm` repository. It is a vision-only, three-view, direct action regressor: 33 consecutive RGB frames at 15 Hz produce the 32 aligned 7-joint plus binary-gripper commands. It has no proprioception, language, task metadata, action encoder, or learned video-action verifier. The implementation, manifest builder/selector, preprocessing, DDP training, checkpoint-resume, inference, server, and focused CPU tests exist. The production manifests, cache, GPU training run, and production checkpoint do not yet exist.

Training is fixed to `nvidia/Cosmos3-DROID@5c11a20accb11497270a5247a7f1e66ad04c956c`: 21,000 train episodes and one 1,000-episode validation set, selected from the 71,253 episodes with at least 33 frames. Both outcomes and all 13 labs follow the eligible population's joint lab x outcome proportions. Validation is raw-scene-disjoint from training. There is no test split and no frame, idle, success, or failure filtering beyond the unavoidable 33-frame eligibility rule.

## Historical IDM evidence

RUN_0007 through RUN_0019 record useful pilot and legacy evidence, but their SmallCNN/flattened-token architectures, episode-number splits, square stretching, optional proprioception, and pilot checkpoints are superseded for production. RUN_0009 remains the best measured legacy checkpoint (`val_mean_joint_mae=0.06857`, `val_gripper_accuracy=0.98685`) and RUN_0016 proved that legacy dream inference could run. Those values are not production metrics and the checkpoint must not be used to validate or resume the new architecture.

## Other components

Cosmos3-Edge through RoboLab is verified end to end. The decoded candidate transport observed in M1 is `(33, 528, 640, 3)`; its fixed layout splits at row 360 into wrist, exterior 1, and exterior 2 views. Cosmos training/internals are not part of IDM training; Cosmos is used only later to produce candidate video/action pairs for WISE.

Robometer is validated offline, and Robometer-only Best-of-K passed its engineering gate. `r_exec` is implemented standalone. The existing legacy `r_cons` server experiment is historical; production `r_cons` awaits the new checkpoint and uses direct IDM reconstruction against the paired Cosmos action. Full WISE fusion remains M6.

Measured RoboLab baselines remain small-n validation evidence, not benchmark claims. See `research/EXPERIMENTS.jsonl` and the individual run receipts for details.

## Immediate next action

1. Join official episode metadata to raw DROID scene identity and generate the deterministic `train_21k.csv` and `val_1k.csv` manifests plus audit.
2. Preprocess only their touched video shards and inspect episode, scene, shard, and stride-window distributions.
3. Train the production IDM on the two A100s, reproduce its fixed 1K validation metrics after reload, then check the saved Cosmos dream path.
4. Integrate the resulting production `r_cons` into WISE before broader evaluation.
