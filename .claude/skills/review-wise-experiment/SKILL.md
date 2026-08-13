---
name: review-wise-experiment
description: Review a completed WISE/RoboLab experiment and decide KEEP, REJECT, BRANCH, or RETEST using matched success evidence, component diagnostics, compute cost, and implementation complexity. Use after meaningful candidate evaluation.
---

# Review a WISE Experiment

## Validation budget and mandatory run record

When this skill is being used for setup, smoke, debugging, or milestone validation, use the **smallest sufficient** task/data budget. For RoboLab, default to 1 task/1 episode for basic wiring and usually 1–3 representative tasks with only a few episodes each for integration validation. Expand only when the current question cannot be answered reliably on the small panel. Small validation panels prove engineering correctness; they do not support performance claims.

Before every non-trivial execution launched by this skill, create `research/runs/RUN_XXXX_<slug>.md` from `research/runs/RUN_TEMPLATE.md`, fill the known setup/config/commands before launch, and finalize it with outputs/results/failures afterward. Keep failed-run records. Update `research/RUNBOOK.md` as well when the run verifies a reusable setup or canonical command.

Review the candidate against its actual parent/baseline under matched settings.

Consider:

- RoboLab task success and uncertainty;
- task-level gains/regressions;
- candidate diversity;
- whether the intended score term actually changed selections;
- Robometer/IDM/action-score failure patterns;
- latency/VRAM/throughput cost;
- implementation complexity and fragility;
- whether the result is confounded by changed simulator/evaluator semantics.

Decisions:

- `KEEP`: better main research state;
- `REJECT`: not worth using as parent;
- `BRANCH`: interesting trade-off/mechanism worth preserving;
- `RETEST`: evidence too noisy/incomplete;
- `MILESTONE_PASS` / `MILESTONE_BLOCKED` for bring-up stages.

Do not declare scientific improvement from a tiny smoke panel. A candidate can be technically correct yet scientifically inconclusive.

Finalize the progress report, append/update the ledger, update `research/STATE.md`, and identify the next action.
