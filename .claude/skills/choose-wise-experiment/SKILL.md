---
name: choose-wise-experiment
description: Choose the next coherent WISE/RoboLab experiment after the full pipeline works, using current task-level evidence, component diagnostics, latency, candidate diversity, and prior experiments. Use before each new research candidate in milestone M7.
---

# Choose the Next WISE Experiment

## Validation budget and mandatory run record

When this skill is being used for setup, smoke, debugging, or milestone validation, use the **smallest sufficient** task/data budget. For RoboLab, default to 1 task/1 episode for basic wiring and usually 1–3 representative tasks with only a few episodes each for integration validation. Expand only when the current question cannot be answered reliably on the small panel. Small validation panels prove engineering correctness; they do not support performance claims.

Before every non-trivial execution launched by this skill, create `research/runs/RUN_XXXX_<slug>.md` from `research/runs/RUN_TEMPLATE.md`, fill the known setup/config/commands before launch, and finalize it with outputs/results/failures afterward. Keep failed-run records. Update `research/RUNBOOK.md` as well when the run verifies a reusable setup or canonical command.

Read the smallest sufficient context from `research/STATE.md`, recent `EXPERIMENTS.jsonl`, relevant progress reports, current code/config, and primary literature/source when useful.

Ask:

> What experiment is most likely to clarify or improve WISE per unit of compute without confounding benchmark semantics?

Candidate directions may include:

- K / candidate diversity / diffusion sampling settings;
- Robometer view choice or score scalarization;
- candidate-relative calibration;
- fusion weights;
- action-quality terms/thresholds;
- IDM architecture, views, temporal/spatial compression, losses, or calibration;
- action-prefix/replanning horizon;
- batching/parallelization that changes cost but not semantics;
- failure-targeted variants suggested by task-level evidence.

Do not mechanically grid-search everything.

A candidate can contain several related changes when they form one coherent design. Avoid unrelated bundles.

Before implementation, create the next progress report and record:

- exact modifications;
- why they are worth testing now;
- primary metric/evidence to watch;
- expected cost;
- which baselines/settings must remain matched.

Commit/identify the runnable state before expensive evaluation and hand off to `/evaluate-wise-robolab`.
