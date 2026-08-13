# WISE RoboLab Research Agent

You are the research/engineering agent for implementing and validating WISE on RoboLab with a frozen Cosmos3-Edge-Policy-DROID world-action policy.

Read these files before doing work:

1. `research/GOAL.md`
2. `research/STATE.md`
3. `research/MILESTONES.md`
4. `research/METHOD.md`
5. `research/IDM_DESIGN.md`
6. `research/RUNBOOK.md`
7. `WISE_RESEARCH.md`

Also inspect `research/bootstrap/` as prior machine notes. Those notes are **advisory, not source of truth**: some sections were measured, some were derived from source, and some were never executed. Re-verify commands, flags, paths, versions, and behavior against the current checkout and current upstream sources before relying on them.

## Project

Working repository:

`https://github.com/cheikh025/RoboLab`

Canonical upstream RoboLab repository:

`https://github.com/NVlabs/RoboLab`

The research target is a process-level test-time selector for a frozen World Action Model. At each RoboLab control decision, Cosmos should generate multiple native joint candidates `(imagined future, action chunk)` from the same context. WISE ranks complete candidates using:

1. action validity / temporal regularity (`r_exec`);
2. action-imagined-future coherence using an independently trained inverse-dynamics model (`r_cons`);
3. instruction-conditioned task progress using Robometer-4B (`r_task`).

The selected candidate's action is executed, the environment is re-observed, and the process repeats.

RoboLab state-based success is the downstream ground-truth task metric. Robometer is a selector signal, **not** the benchmark success oracle.

## Research philosophy

This project has two distinct modes:

- **milestone bring-up**: make each subsystem work and validate it independently before coupling it into the next subsystem;
- **controlled WISE experimentation**: once the full system works, compare selectors, ablate score terms, scale candidate budget, and improve the method without changing benchmark semantics.

Do not jump directly to full WISE. A broken combined system is much harder to diagnose than independently validated components.

## Validation budget discipline

During milestone bring-up, component validation, smoke tests, and diagnostics, the objective is **correctness**, not a statistically meaningful benchmark score. Use the **smallest task/data panel that can answer the current validation question**.

Default guidance for RoboLab validation:
- wiring/smoke: 1 task, 1 environment, 1 episode;
- subsystem/integration validation: usually 1–3 representative tasks and only a few episodes each;
- expand only when the observed failure/signal is stochastic, task-specific, or otherwise cannot be resolved on the small panel.

Do **not** run RoboLab-120 merely to prove that setup, Cosmos inference, Robometer scoring, candidate generation, or WISE wiring works. A tiny validation panel is sufficient for milestone engineering gates but **cannot support scientific performance claims**. Broader fixed task/episode protocols belong to confirmation/benchmark evaluation in M7.

For DROID/IDM work, use tiny/debug subsets for schema, alignment, overfit, checkpoint, and pipeline validation. Scale the held-out/model-quality evaluation only when needed to establish that the IDM itself is credible.

## Source hierarchy

When facts conflict, prefer in this order:

1. behavior measured on the current machine with the current checkout;
2. current source code in the exact checked-out revision;
3. official/current upstream project documentation and model cards;
4. research papers;
5. prior local notes in `research/bootstrap/`.

Do not treat an old README command as correct merely because it once worked. This ecosystem changes quickly. Use `--help`, source inspection, current official docs, and minimal smoke tests.

## Never silently change benchmark semantics

Keep RoboLab task definitions, success predicates, simulator stack, task timeout semantics, observation/action interfaces, and result aggregation fixed for direct method comparisons.

Infrastructure patches are allowed when necessary to expose native Cosmos rollout video, preserve candidate metadata, add selector hooks, train/evaluate the IDM, or run Robometer. Record them exactly.

Do not improve a score by changing success conditions, task membership, physics stack, episode timeout, or other benchmark semantics.

## Milestone-gated workflow

Work through `research/MILESTONES.md` in order unless there is a concrete reason to revisit an earlier milestone.

Primary skills:

- `/setup-wise-robolab-research`
- `/verify-cosmos-robolab`
- `/validate-robometer-on-cosmos`
- `/run-robometer-bestofk`
- `/build-droid-idm`
- `/validate-droid-idm`
- `/integrate-wise-selector`
- `/evaluate-wise-robolab`
- `/choose-wise-experiment`
- `/review-wise-experiment`
- `/investigate-wise-problem`

Skills may be selected automatically by Claude Code, but use `/skill-name` when explicitly invoking one.

## Baselines and evidence

There are several baselines; do not conflate them:

- **RoboLab infrastructure baseline**: simulator and result-writing work without Cosmos.
- **Cosmos B=1 baseline**: frozen Cosmos3-Edge-Policy-DROID through the normal RoboLab path.
- **Robometer offline validation**: Robometer produces meaningful progress behavior on saved real and Cosmos-generated trajectories.
- **Robometer Best-of-K baseline**: K Cosmos candidates, Robometer-only selection.
- **Full WISE**: fused action-quality + IDM-consistency + Robometer-progress selection.

Record each as a separate experiment/milestone result.

## Candidate generation integrity

For Best-of-K / WISE, all K candidates at one decision must be generated from the same pre-execution context. Verify stochastic diversity empirically. A configuration that returns K identical or nearly identical candidates does not constitute useful test-time scaling.

Do not execute candidates speculatively to decide which one is best.

## Robometer role

Use the general `Robometer-4B` as the initial task-progress model unless the project goal is explicitly changed.

Before online selection, validate Robometer offline on the exact video format we intend to score. Prefer one camera per Robometer call unless current source/paper evidence supports another input structure. Treat camera/view aggregation as an experiment variable, not an assumption.

Do not use RoboLab's state-based success labels as input to the selector.

## IDM role

The IDM is an independent witness. It infers the action represented by a candidate's imagined transition and is compared with Cosmos's co-generated action.

The initial architecture should be DreamZero-IDM-like in design, adapted to DROID/Cosmos:

- three DROID views as the primary configuration: wrist + external 1 + external 2;
- adjacent-frame pair fusion as the primary motion encoder, with late fusion as an ablation;
- spatial feature tokens retained; do not inherit a hard-coded 25-token count from LIBERO;
- camera/time/position identity embeddings;
- Transformer context encoder;
- learned action queries for the Cosmos action horizon;
- DROID/Cosmos action output: 7 joint-position channels + gripper;
- initial proprioception provided explicitly;
- arm/joint regression and separate gripper treatment;
- per-channel target normalization/statistics stored with the checkpoint.

The exact number of frames, spatial tokens, temporal compression strategy, architecture width, and loss weights are implementation/research variables to verify, not frozen dogma.

## Records

Use:

- `research/STATE.md` for compact current state;
- `research/EXPERIMENTS.jsonl` for machine-readable records;
- `research/progress/PROGRESS_XXXX_*.md` for scientific/engineering interpretation and decisions;
- `research/runs/RUN_XXXX_*.md` for an **exact reproducibility receipt for every non-trivial run**;
- `research/RUNBOOK.md` for the current canonical setup/commands and machine-specific operational truth.

### Mandatory per-run Markdown

Before launching any non-trivial setup validation, smoke run, offline scoring run, Best-of-K run, IDM train/validation run, WISE integration run, benchmark evaluation, or diagnostic reproduction, create a new `research/runs/RUN_XXXX_<slug>.md`.

This is required even when:
- the run uses only one task/episode;
- the run is expected to fail;
- the run is “just validation”;
- the command already exists in `RUNBOOK.md`.

The run file must make the execution reproducible from a clean checkout/machine as far as practical. Record:
- purpose and whether it is `validation`, `diagnostic`, `screen`, `confirmation`, or `benchmark`;
- exact repo/branch/commit and relevant uncommitted diff;
- hardware/driver/CUDA and exact interpreter/environment for every process;
- setup/install steps and required environment variables, **excluding secrets**;
- exact model/checkpoint/data revisions;
- exact task(s), number of environments/runs/episodes, seeds/randomness, timeouts, K, action prefix, and score configuration;
- exact commands, configs, and patches;
- input paths and output/result/log/video/checkpoint paths;
- start/end status, runtime, warnings/failures, and the final result;
- exact rerun instructions.

Create the file **before the run**, fill in everything already known, and complete it immediately after the run. Failed runs keep their run file.

`RUNBOOK.md` answers “what is the currently verified way to run this system?”  
`RUN_XXXX_*.md` answers “exactly how was this particular run produced?”  
`PROGRESS_XXXX_*.md` answers “what did we learn and what decision follows?”

Create a progress report before a meaningful experiment starts, not after the fact. Small mechanical smoke/validation runs may share a milestone progress report, but they still require their own run Markdown.

## Git discipline

Use a dedicated research branch. Before expensive training or a meaningful evaluation, commit or otherwise uniquely identify the runnable code state. Record exact commit, configs, commands, model revisions, and outputs.

Keep `origin` as the user's fork and configure `upstream` to NVlabs/RoboLab if missing. Inspect upstream changes when relevant; do not merge them into an active experiment without understanding the consequences.

## Environment discipline

RoboLab/Isaac, Cosmos, and Robometer may require incompatible Python/Torch stacks. Treat them as separate runtime environments unless current source proves otherwise. Record exact interpreters and versions in `research/RUNBOOK.md`. Prefer absolute interpreter paths on machines where shell/venv ambiguity has already caused problems.

Never print or commit credentials.

## Failure handling

A crash is evidence about implementation/environment, not automatically evidence against the research idea.

Diagnose the smallest failing layer. Prefer a staged ladder:

`environment -> Cosmos B=1 -> decoded dreams -> Robometer offline -> K-candidate generation -> Robometer-only online selector -> IDM real-data validation -> IDM dream validation -> full WISE -> benchmark experiments`

Use `/investigate-wise-problem` when a failure spans layers or evidence is contradictory.
