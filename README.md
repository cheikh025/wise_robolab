# WISE RoboLab Claude Research Agent

A Claude Code research/engineering scaffold for implementing and validating WISE on the user's RoboLab fork with Cosmos3-Edge-Policy-DROID, Robometer-4B, and a DROID inverse-dynamics model.

## Install into the RoboLab checkout

Copy the **contents** of this package into the root of `cheikh025/RoboLab` so `.claude/skills/...`, `CLAUDE.md`, `WISE_RESEARCH.md`, and `research/...` sit at repository root.

This package intentionally does not overwrite RoboLab source files. The agent should inspect the current checkout and make explicit, recorded patches as each milestone requires.

## Start

In Claude Code, from the RoboLab repository root:

`/setup-wise-robolab-research`

Then follow the milestone hand-offs. Claude Code can also auto-select skills from their descriptions.

## Design principle

Prior notes in `research/bootstrap/` are useful context but are not authoritative. The agent must rediscover and verify the actual commands/interfaces on the current machine and current source revisions.

The current production IDM contract is frozen in `research/IDM_DESIGN.md`. In brief, it is a direct three-view RGB-to-action model trained only on a pinned DROID source: 21,000 training episodes, 1,000 scene-disjoint validation episodes, no test split, and no proprioception, language, learned verifier, or Cosmos training data. `research/METHOD.md` defines how its output becomes WISE's deterministic `r_cons` signal.

## Two global rules

1. **Validation stays small.** During setup and milestone validation, use the smallest sufficient RoboLab panel (typically 1 task/episode for smoke and 1–3 tasks with a few episodes for integration checks). Do not run the full benchmark just to prove wiring. Broader protocols are for scientific evaluation after the pipeline works.

2. **Every run is reproducible in Markdown.** Before every non-trivial execution, create `research/runs/RUN_XXXX_<slug>.md` from the template, record exact setup/commit/commands/config/tasks/seeds/model revisions, then finalize it with outputs/results/failures. Failed runs are kept too.
