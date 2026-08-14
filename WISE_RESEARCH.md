# WISE RoboLab Research Workflow

This is the operating workflow for the project.

## Universal validation rule

Stages A–G are primarily **engineering validation** until the pipeline is ready for controlled experiments. Outside the frozen 21,000/1,000-episode production IDM contract, deliberately use a small task/data budget:
- one task/episode for basic smoke and wiring;
- one to three representative RoboLab tasks with only a few episodes each for most subsystem/integration checks;
- larger panels only when the current question genuinely requires more evidence.

The production IDM allocation is not a pilot panel: do not shrink it into another test run or add a separate test split.

Passing a milestone means the subsystem is reproducibly correct on the chosen validation evidence; it does **not** mean its RoboLab performance has been established. Do not spend the 120-task benchmark budget on setup validation.

## Universal reproduction rule

Every non-trivial run gets a dedicated `research/runs/RUN_XXXX_<slug>.md`, created before execution and finalized after it. This includes setup/smoke, Cosmos, Robometer, Best-of-K, IDM training/validation, full WISE, evaluations, and failed diagnostics.

The run Markdown must contain enough setup, code state, commands, task/data selection, model revisions, environment details, and output paths to reproduce that exact run. Reusable verified commands are also propagated into `research/RUNBOOK.md`.

## Stage A — establish the machine and benchmark

Run `/setup-wise-robolab-research`.

Finish with:

- verified fork/upstream and research branch;
- exact Isaac Sim / Isaac Lab / Python / CUDA stack recorded;
- RoboLab tests/smoke episode passing;
- task success/result-writing path understood;
- machine-specific commands in `research/RUNBOOK.md`;
- baseline report created.

## Stage B — verify frozen Cosmos through RoboLab

Run `/verify-cosmos-robolab`.

Do not merely check that the server starts. Verify end to end:

- the intended **Edge DROID** checkpoint is actually loaded;
- server/client observation and action formats agree;
- action space is joint-position + gripper as expected;
- control rate and action horizon match the environment;
- one task runs through the normal client;
- decoded native imagined rollout video can be retained without changing action semantics;
- repeated calls on the same context produce genuinely different candidates when stochastic sampling is enabled;
- a reproducible B=1 Cosmos baseline can be measured.

## Stage C — validate Robometer offline

Run `/validate-robometer-on-cosmos`.

First prove Robometer works independently of the policy loop. Score saved real trajectories and saved Cosmos dreams with the exact language instruction. Determine which DROID view(s) provide useful progress signal and measure latency.

Do not start Best-of-K until offline behavior is credible.

## Stage D — Robometer-only Best-of-K

Run `/run-robometer-bestofk`.

This is the strongest pre-IDM selector baseline:

`same RoboLab state -> K Cosmos candidates -> Robometer score -> select candidate -> execute its paired action`

Compare against B=1 / first-sample and random-candidate selection under matched settings. Start on a small task panel before expanding.

## Stage E — build the DROID IDM

Run `/build-droid-idm`.

Build the deterministic production manifests from `nvidia/Cosmos3-DROID` revision `5c11a20accb11497270a5247a7f1e66ad04c956c`: 21,000 training episodes and 1,000 scene-disjoint validation episodes using the exact joint lab x outcome quotas in `research/IDM_DESIGN.md`. Use shard-aware selection, retain every selected frame, and audit the induced window distribution. Do not create a pilot or test split.

Train the frozen direct vision-to-action architecture: three synchronized RGB views, 33 consecutive frames, adjacent-frame motion pairs, shared ResNet-50 spatial features, cross-view fusion, a bidirectional temporal Transformer, and aligned 32-step joint/gripper heads. Inputs are vision only. Do not add initial state, proprioception, language, metadata, a learned verifier, or an auxiliary action encoder. Cosmos is not used in IDM training.

## Stage F — validate the IDM

Run `/validate-droid-idm`.

Validation ladder:

1. evaluate commanded-action reconstruction over the frozen 1,000-episode DROID validation manifest;
2. verify checkpoint identity, training-only normalization, temporal alignment, per-joint errors, and binary gripper accuracy;
3. decode complete Cosmos dreams as fixed `33 x 528 x 640 x 3` RGB tensors split at row 360;
4. infer 32 x 8 actions from each dream and compare them with the paired Cosmos action using the frozen direct `r_cons` formula;
5. characterize real-validation and generated-dream consistency distributions before selector integration.

Do not change views, filter idle frames, add a test set, or start an architecture-ablation campaign as a substitute for validating the production contract. Do not plug the IDM into WISE merely because training loss decreases.

## Stage G — integrate full WISE

Run `/integrate-wise-selector`.

Implement the three signals independently, preserve raw values, calibrate candidate-relative scores, fuse them, and select a complete candidate. Keep hooks to run each component alone or in combinations.

## Stage H — controlled RoboLab evaluation

Run `/evaluate-wise-robolab` and then iterate with `/choose-wise-experiment` + `/review-wise-experiment`.

Minimum comparison set should eventually include:

- Cosmos B=1 / first sample;
- random candidate among K;
- Robometer-only;
- action-quality only;
- IDM-consistency only;
- task + exec;
- task + consistency;
- exec + consistency;
- full WISE;
- candidate-budget scaling for useful K values.

Use matched tasks, seeds/initialization protocol, simulator versions, timeouts, and episode counts for direct comparisons.

## Continuous research after full bring-up

```text
accepted implementation + experiment history
                  |
                  v
        /choose-wise-experiment
                  |
                  v
       implement coherent candidate
                  |
                  v
        /evaluate-wise-robolab
                  |
                  v
        /review-wise-experiment
                  |
       keep / reject / branch /
              retest
                  |
                  v
       update records and repeat
```

Use `/investigate-wise-problem` whenever the next move is unclear or a subsystem behaves inconsistently.
