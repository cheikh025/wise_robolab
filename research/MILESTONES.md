# Milestones

## Milestone validation policy

M0–M6 are validation gates, not full benchmark studies. Use a deliberately small representative task/data panel unless a specific validation question requires expansion. A milestone can pass on small evidence when the evidence proves the intended engineering property reproducibly. Do not interpret that as a performance claim.

Every executable milestone check must have a corresponding `research/runs/RUN_XXXX_*.md` reproduction record.

## M0 — RoboLab setup and benchmark integrity

Exit criteria:

- fork/upstream/research branch recorded;
- exact simulator/software stack captured;
- test suite or equivalent install verification passes with CUDA actually exercised;
- one headless RoboLab episode completes and writes expected result artifacts;
- state-based success path and task timeout behavior understood;
- runbook filled with verified commands.

## M1 — Cosmos3-Edge + RoboLab baseline

Exit criteria:

- intended Edge DROID checkpoint proven loaded;
- observation, state, action-space, control-rate, chunk-size, and gripper post-processing verified from current code and runtime;
- one normal Cosmos episode works end to end;
- decoded native rollout video is retained without changing the action path;
- repeated same-context requests demonstrate useful candidate diversity;
- B=1 baseline is measured on a documented initial panel.

## M2 — Robometer offline validation

Exit criteria:

- isolated Robometer environment works;
- general Robometer-4B loads and scores saved video + exact task instruction;
- real successful/failure examples show interpretable progress behavior relative to RoboLab event/state logs;
- Cosmos dream scoring works;
- per-view behavior is measured; input/view strategy chosen and recorded;
- latency and VRAM are measured.

## M3 — Robometer-only Best-of-K

Exit criteria:

- K candidates are generated before any action from that decision is executed;
- each candidate keeps its paired action and imagined future together;
- Robometer scores candidates online/offline in a way identical to the validated scoring path;
- first-sample, random-K, and Robometer-selected-K are compared under matched settings;
- selector overhead is measured.

## M4 — DROID IDM data + training pipeline

Exit criteria:

- `nvidia/Cosmos3-DROID` is pinned to revision `5c11a20accb11497270a5247a7f1e66ad04c956c`;
- deterministic, scene-disjoint, shard-aware manifests contain exactly 21,000 training and 1,000 validation episodes with the frozen lab x outcome quotas;
- selection applies only the unavoidable `length >= 33` eligibility rule, preserves every selected frame, and reports episode plus window/shard audits;
- 33 synchronized frames align to 32 action rows using the verified frame `t` -> frame `t+1` convention, with train stride 16, validation stride 32, and an end-aligned tail;
- commanded 7-D absolute joint-position targets come from the correct DROID fields rather than the convenience velocity-style `action` field;
- continuous raw gripper targets are thresholded at `> 0.5` into `0 = open`, `1 = closed` without an extra Cosmos polarity flip;
- the three-view RGB-only data path works with no initial state, proprioception, language, outcome, task, or lab model input;
- the frozen ResNet-50 spatial-softmax/cross-view/temporal-Transformer model trains, checkpoints, resumes, reloads, and preserves training-only normalization statistics;
- there is no separate test split, learned verifier, auxiliary action encoder, smoothness loss, or idle loss.

## M5 — IDM validation

Exit criteria:

- the full frozen 1,000-episode validation manifest is evaluated without training-scene leakage;
- standardized and physical-unit joint errors, per-joint diagnostics, and binary gripper accuracy are reported;
- checkpoint verification reproduces validation metrics and rejects architecture, preprocessing, source-revision, manifest, or normalization mismatches;
- temporal/alignment checks exclude frame/action offsets without changing or filtering the production data;
- inference accepts only the fixed three-view `33 x 528 x 640 x 3` decoded dream layout split at row 360 and uses the same aspect-preserving letterbox as training;
- direct `r_cons` computation compares the IDM's 32 x 8 prediction with the paired Cosmos action using the frozen joint-error/gripper-agreement formula;
- real-validation and generated-dream consistency distributions are recorded as diagnostics before WISE integration.

## M6 — Full WISE integration

Exit criteria:

- raw `r_exec`, `r_cons`, `r_task` stored for every candidate;
- candidate-relative calibration is explicit and reproducible;
- fusion weights/config are explicit;
- hard action-invalid behavior is explicit;
- all single-term/two-term/full selectors can be selected by config;
- selection preserves paired action/future identity;
- no candidate is physically executed before selection.

## M7 — Controlled WISE experiments

Exit criteria:

- matched comparisons against B=1, random-K, and Robometer-only;
- ablations isolate consistency contribution;
- useful K scaling curve measured;
- latency/VRAM/throughput reported;
- task-level failure analysis performed;
- results are reproducible from recorded commits/configs/commands.
