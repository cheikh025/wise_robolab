---
name: evaluate-wise-robolab
description: Run controlled RoboLab evaluations of B=1, random-K, Robometer-only, WISE ablations, and full WISE under matched benchmark semantics, with adaptive panels for development and fixed broader protocols for claims.
---

# Evaluate WISE on RoboLab

## Validation budget and mandatory run record

When this skill is being used for setup, smoke, debugging, or milestone validation, use the **smallest sufficient** task/data budget. For RoboLab, default to 1 task/1 episode for basic wiring and usually 1–3 representative tasks with only a few episodes each for integration validation. Expand only when the current question cannot be answered reliably on the small panel. Small validation panels prove engineering correctness; they do not support performance claims.

Before every non-trivial execution launched by this skill, create `research/runs/RUN_XXXX_<slug>.md` from `research/runs/RUN_TEMPLATE.md`, fill the known setup/config/commands before launch, and finalize it with outputs/results/failures afterward. Keep failed-run records. Update `research/RUNBOOK.md` as well when the run verifies a reusable setup or canonical command.

## First ask what decision the evaluation informs

Choose one purpose:

- `smoke`: correctness only;
- `diagnostic`: answer a specific failure question;
- `screen`: cheap matched comparison to decide what deserves more runs;
- `confirmation`: broader task/episode evidence;
- `benchmark`: fixed protocol intended for a reported result.

Do not spend full-benchmark compute to diagnose basic wiring.

## Preserve matching conditions

For direct selector comparisons keep fixed:

- RoboLab/Isaac stack and commit;
- Cosmos checkpoint/revision and generation settings;
- tasks and instructions;
- task timeouts/success predicates;
- environment initialization/seeds protocol;
- action prefix/chunk behavior unless it is the experimental variable;
- episode count.

Record any unavoidable differences.

## Minimum selector baselines

Eventually compare:

1. B=1 / first sample;
2. random candidate among K;
3. Robometer-only;
4. exec-only;
5. consistency-only;
6. task + exec;
7. task + consistency;
8. exec + consistency;
9. full WISE.

Do not require all nine for every early screen. Choose the smallest panel that answers the current question.

## Test-time scaling curve

For promising selectors, measure useful K values. Report success together with:

- WAM generation latency;
- Robometer latency;
- IDM latency;
- total decision latency;
- VRAM;
- throughput/parallelization;
- candidate diversity.

A larger K that adds no diversity is not meaningful scaling.

## Task-level analysis

RoboLab has heterogeneous task difficulty/competency structure. Record task-level outcomes and investigate where selection helps or hurts instead of relying only on one overall average.

## Evidence discipline

Do not promote a method based on a tiny smoke panel. Use matching repeated episodes and uncertainty-aware interpretation before making scientific claims.

Store result directories and a concise summary in the progress report. Raw logs/videos stay on disk.
