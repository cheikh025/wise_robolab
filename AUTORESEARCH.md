# WISE AutoResearch / Engineering Loop

The project is milestone-gated until the full WISE pipeline is validated, then becomes an iterative research loop.

Read `WISE_RESEARCH.md` for the detailed operating procedure.

## Bring-up sequence

```text
/setup-wise-robolab-research
        -> /verify-cosmos-robolab
        -> /validate-robometer-on-cosmos
        -> /run-robometer-bestofk
        -> /build-droid-idm
        -> /validate-droid-idm
        -> /integrate-wise-selector
        -> /evaluate-wise-robolab
```

Do not skip a blocked milestone by wiring more components around it.

During M0–M6 validation, use the smallest sufficient task/data panel. The purpose is to prove correctness, not to estimate final RoboLab performance. Full/broad evaluation is reserved for M7 confirmation/benchmark runs.

Every non-trivial execution must have a `research/runs/RUN_XXXX_*.md` created before launch and completed afterward, including failed validation runs.

## Research loop after M6

```text
current accepted WISE implementation + evidence
                  |
                  v
        /choose-wise-experiment
                  |
                  v
          implement candidate
                  |
                  v
        /evaluate-wise-robolab
                  |
                  v
        /review-wise-experiment
                  |
          keep/reject/branch/retest
                  |
                  v
       update state + progress ledger
                  |
                  +--------------------> repeat
```

Use `/investigate-wise-problem` whenever the evidence is contradictory or the failure crosses subsystem boundaries.
