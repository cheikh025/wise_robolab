# WISE RoboLab Research Workflow

This is the operating workflow for the project.

## Universal validation rule

Stages A–G are primarily **engineering validation** until the pipeline is ready for controlled experiments. For validation, deliberately use a small task/data budget:
- one task/episode for basic smoke and wiring;
- one to three representative RoboLab tasks with only a few episodes each for most subsystem/integration checks;
- larger panels only when the current question genuinely requires more evidence.

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

Begin with the DROID debug subset for data/alignment validation, then scale training only after labels, frame/action timing, camera mapping, and normalization are proven.

Primary design: DreamZero-like motion IDM adapted to 3-view DROID, 32-step 8-D Cosmos joint-position action chunks, and initial proprioception.

## Stage F — validate the IDM

Run `/validate-droid-idm`.

Validation ladder:

1. held-out real DROID clips -> reconstruct DROID commanded actions;
2. camera/view and fusion ablations;
3. temporal alignment sanity tests;
4. Cosmos-generated dreams -> infer actions and compare with Cosmos co-generated actions;
5. analyze real-vs-generated domain shift and consistency-score distributions.

Do not plug an unvalidated IDM into WISE merely because training loss decreases.

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
