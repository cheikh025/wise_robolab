# RUN_XXXX — <short name>

## Identity

- status: `PLANNED` / `RUNNING` / `COMPLETED` / `FAILED` / `ABORTED`
- run class: `validation` / `diagnostic` / `screen` / `confirmation` / `benchmark`
- milestone:
- associated progress report:
- date/time:
- operator/agent:

## Purpose

- exact question this run answers:
- pass/fail criterion:
- why this task/data budget is sufficient for this validation:

## Code state

- RoboLab repo:
- branch:
- commit:
- relevant uncommitted diff:
- upstream revision if relevant:
- Cosmos/cosmos-framework revision:
- Robometer revision:
- IDM/WISE code revision:

## Machine and environments

- host/GPU:
- driver/CUDA:
- Isaac Sim / Isaac Lab:
- RoboLab interpreter:
- Cosmos interpreter:
- Robometer interpreter:
- IDM interpreter:
- key package versions:

## Setup from a clean state

Record the exact prerequisite/setup steps required to reproduce this run. Reuse verified `RUNBOOK.md` steps by reference, but include any run-specific setup here.

```bash
# install/setup commands
```

Required environment variables (names and non-secret values only):

```bash
# e.g. HF_HOME=...
# never paste tokens/passwords
```

## Models and data

- Cosmos checkpoint + exact revision:
- Robometer checkpoint + exact revision:
- IDM checkpoint + exact revision:
- DROID dataset release/split:
- other inputs/assets:

## RoboLab / experiment configuration

- task(s):
- exact instruction(s) when relevant:
- num envs:
- num runs / episodes:
- seeds/randomness:
- simulator/physics stack:
- episode timeout semantics:
- candidate budget K:
- action horizon/prefix:
- Cosmos generation settings:
- Robometer view/scalarization:
- IDM preprocessing/config:
- `r_exec` config:
- calibration/fusion config:

## Exact commands

```bash
# terminal/process 1
# ...

# terminal/process 2
# ...
```

## Expected outputs

- result directory:
- logs:
- videos/dreams:
- metrics JSON:
- checkpoints:
- other artifacts:

## Execution result

- start time:
- end time:
- wall time:
- peak VRAM / throughput if relevant:
- exit status:
- warnings/errors:

## Observed evidence

- validation/benchmark result:
- task-level result:
- candidate diversity:
- Robometer:
- IDM:
- WISE:
- artifact paths:

## Outcome

- pass/fail:
- what was proven:
- what was **not** proven:
- next action:

## Exact rerun recipe

From a clean checkout/machine (or explicitly stated prepared base image), run:

```bash
# concise exact rerun sequence
```

## Reproducibility checklist

- [ ] exact commits/revisions recorded
- [ ] exact environment/interpreters recorded
- [ ] setup steps recorded
- [ ] exact commands recorded
- [ ] task/data budget recorded
- [ ] seeds/randomness recorded
- [ ] configs/model revisions recorded
- [ ] outputs/artifacts recorded
- [ ] no secrets recorded
- [ ] failed run preserved if applicable
