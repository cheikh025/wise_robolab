---
name: investigate-wise-problem
description: Diagnose unclear, surprising, or repeated failures across RoboLab, Cosmos, Robometer, DROID IDM, or WISE integration. Use when evidence spans layers, normal fixes fail, or the next experiment is not credible.
---

# Investigate a WISE/RoboLab Problem

## Validation budget and mandatory run record

When this skill is being used for setup, smoke, debugging, or milestone validation, use the **smallest sufficient** task/data budget. For RoboLab, default to 1 task/1 episode for basic wiring and usually 1–3 representative tasks with only a few episodes each for integration validation. Expand only when the current question cannot be answered reliably on the small panel. Small validation panels prove engineering correctness; they do not support performance claims.

Before every non-trivial execution launched by this skill, create `research/runs/RUN_XXXX_<slug>.md` from `research/runs/RUN_TEMPLATE.md`, fill the known setup/config/commands before launch, and finalize it with outputs/results/failures afterward. Keep failed-run records. Update `research/RUNBOOK.md` as well when the run verifies a reusable setup or canonical command.

## Localize the layer

Start from the smallest boundary that can reproduce the issue:

1. RoboLab/Isaac environment;
2. Cosmos server startup;
3. RoboLab-Cosmos protocol;
4. action execution semantics;
5. decoded dream/video path;
6. same-context K candidate diversity;
7. Robometer offline inference;
8. Robometer online selector;
9. DROID data/temporal alignment;
10. IDM training/reload;
11. IDM dream inference;
12. score calibration/fusion;
13. full closed-loop WISE.

Do not debug all layers at once.

## Reconcile evidence sources

If a bootstrap note, current source, current docs, and runtime disagree, explicitly record the disagreement and determine which revision each refers to. Prefer measured current behavior.

Search current official repositories/issues/papers when the failure may be version-specific or undocumented.

## Use discriminating tests

Prefer tests that distinguish hypotheses:

- fixed observation with repeated Cosmos requests for seed collapse;
- deliberate frame/action offsets for IDM alignment;
- real vs dream video through the same Robometer/IDM path for domain shift;
- constant score arrays for calibration stability;
- saved candidate replay for action/video pairing bugs;
- B=1 through the WISE wrapper to test whether integration itself changes behavior.

## Record

Put the diagnosis, evidence, minimal reproduction, and proposed fix in the active progress report or a dedicated diagnostic report. Do not paste enormous logs; preserve them as artifacts and quote the relevant tail/metrics.

Return to the appropriate milestone skill when the problem is localized.
