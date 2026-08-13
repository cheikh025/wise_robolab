---
name: setup-wise-robolab-research
description: Initialize the WISE RoboLab research project. Verify the user's RoboLab fork/upstream, machine/Isaac environment, benchmark integrity, result-writing path, research branch, and machine-specific runbook before any Cosmos/Robometer/IDM work.
---

# Setup WISE RoboLab Research

## Validation budget and mandatory run record

When this skill is being used for setup, smoke, debugging, or milestone validation, use the **smallest sufficient** task/data budget. For RoboLab, default to 1 task/1 episode for basic wiring and usually 1–3 representative tasks with only a few episodes each for integration validation. Expand only when the current question cannot be answered reliably on the small panel. Small validation panels prove engineering correctness; they do not support performance claims.

Before every non-trivial execution launched by this skill, create `research/runs/RUN_XXXX_<slug>.md` from `research/runs/RUN_TEMPLATE.md`, fill the known setup/config/commands before launch, and finalize it with outputs/results/failures afterward. Keep failed-run records. Update `research/RUNBOOK.md` as well when the run verifies a reusable setup or canonical command.

## Read the contract

Read `CLAUDE.md`, `WISE_RESEARCH.md`, `research/GOAL.md`, `research/MILESTONES.md`, `research/METHOD.md`, `research/STATE.md`, and relevant prior notes in `research/bootstrap/`.

Treat bootstrap notes as hints. Re-verify them.

## Verify Git state

Working fork: `https://github.com/cheikh025/RoboLab`.

Canonical upstream: `https://github.com/NVlabs/RoboLab`.

Check current branch, commit, dirty state, `origin`, and `upstream`. Add/fetch `upstream` if missing. Do not overwrite local work.

Create a dedicated research branch such as `wise/<run-tag>` from the intended starting commit and record it in `research/RUNBOOK.md`.

## Inspect current RoboLab source

Read the current root README, requirements/pyproject, docs for environment execution/results, DROID registration/action-space code, evaluation runner, success predicates, and existing Cosmos policy client.

Use current official upstream docs/source online when it can resolve ambiguity. Pin the upstream revision actually inspected.

## Establish the machine stack

Identify how RoboLab/Isaac is actually installed on this machine. Do not assume the bootstrap path is still correct.

Record:

- exact interpreter;
- Python/PyTorch;
- Isaac Sim / Isaac Lab;
- driver/CUDA;
- GPU/VRAM;
- disk;
- relevant environment variables without printing secrets.

Use `research/tools/capture_system_info.py` with the RoboLab interpreter when practical.

## Verify benchmark infrastructure

Run the smallest reliable install/test sequence from the current checkout. Ensure CUDA-dependent tests really ran rather than being skipped.

Run one headless task without Cosmos if useful to isolate simulator health. Verify expected result/video/event artifacts are produced and identify exactly where state-based success is computed.

Confirm:

- control rate from the registered DROID environment;
- task timeout semantics;
- action space expected by the DROID registration;
- camera keys available in the Cosmos registration;
- output/result format.

## Build the runbook

Fill the RoboLab/Isaac and Git sections of `research/RUNBOOK.md` with commands that were **actually verified**.

A plausible command is not verified. Resolve flag/path questions with source, `--help`, and smoke execution.

## Record M0

Create `research/progress/PROGRESS_0000_SETUP.md` and record the environment, tests, exact commands, and results. Append an experiment record and update `research/STATE.md`.

M0 passes only when the simulator/result-writing path is reproducibly working.

Then hand off to `/verify-cosmos-robolab`.
