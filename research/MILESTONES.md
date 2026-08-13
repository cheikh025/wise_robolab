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

- DROID sample loading/alignment verified on a tiny/debug subset;
- commanded 7-D joint-position + gripper targets are taken from the correct DROID fields, not accidentally from the convenience velocity `action` field;
- three-view primary data path works;
- initial proprioception is included;
- training, checkpointing, normalization stats, and reload work;
- training scaled beyond debug only after alignment checks pass.

## M5 — IDM validation

Exit criteria:

- held-out real DROID action reconstruction metrics are meaningful;
- gripper accuracy and per-joint errors reported;
- temporal/alignment tests exclude obvious label offset mistakes;
- early/late fusion and view ablations are available when useful;
- Cosmos-dream inference works;
- consistency-score distributions and real-vs-dream domain shift are characterized.

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
