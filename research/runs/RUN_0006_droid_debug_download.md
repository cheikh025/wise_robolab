# RUN_0006 — DROID debug subset download + schema/alignment verification

## Identity

- status: `SUPERSEDED` (the receipt was never finalized; later RUN_0007-RUN_0019 records contain the actual debug/training evidence)
- run class: `validation`
- milestone: M4_IDM_TRAIN
- associated progress report: research/progress/PROGRESS_0004_IDM_DATA.md (to be created)
- date/time: 2026-08-12 (~08:20Z)
- operator/agent: Claude Code (autonomous /goal run)

## Purpose

- exact question this run answers: does `nvidia/Cosmos3-DROID` (LeRobotDataset v3.0 format, the exact dataset cosmos-framework itself trains Cosmos3's DROID policy on) load correctly on a tiny debug subset (one data/video chunk-file), with commanded joint-position + gripper targets coming from the correct fields (`action.joint_position` [7], `action.gripper_position` [1]) and not the convenience velocity/cartesian fields, and with correct temporal alignment between frames/state/action?
- pass/fail criterion: parquet loads, episode boundaries are identifiable, video frame count matches parquet row count per episode (or a documented, understood relationship), `action.joint_position`/`action.gripper_position` are present and have sane ranges (not accidentally equal to `action.joint_velocity`/`action.cartesian_position`), fps=15 confirmed matching RoboLab/Cosmos control rate.
- why this task/data budget is sufficient for this validation: M4's own guidance — "Start with the smallest DROID debug subset available." One data/video chunk-file (~680MB, likely dozens of episodes packed) is far smaller than the full 57,639-episode/18.7M-frame dataset, sufficient for schema/alignment verification before any training.

## Code state

- repo: n/a (data download + a new standalone `wise_robolab` IDM package, not part of RoboLab or cosmos-framework)
- branch: n/a yet — will create a dedicated branch/location for IDM code under `wise_robolab` or a new repo location, TBD in the next run
- commit: n/a
- relevant uncommitted diff: n/a
- upstream revision if relevant: `nvidia/Cosmos3-DROID` dataset revision = default (main), schema confirmed via `success/meta/info.json`: `codebase_version: v3.0`, `chunks_size: 1000`, `total_episodes: 57639`, `total_frames: 18691281`, `fps: 15`
- Cosmos/cosmos-framework revision: `a98dec05aa93ff6e2ebab2f38b590b86fe84f757` (source-of-truth for schema field names, cross-checked in `droid_lerobot_dataset_config.py`/`droid_lerobot_dataset.py`, not executed in this run)
- Robometer revision: n/a
- IDM/WISE code revision: n/a (not yet written)

## Machine and environments

- host/GPU: same box, unchanged
- driver/CUDA: unchanged
- Isaac Sim / Isaac Lab: not used
- interpreter for this download/inspection: `/venv/main/bin/python` (system default env, has `huggingface_hub`; IDM training env TBD — likely needs its own venv given pandas/pyarrow/decord/av1-video-decode requirements not yet verified against RoboLab/Cosmos/Robometer's existing envs)
- key package versions: TBD (need `pyarrow`/`pandas` for parquet, a video decoder with AV1 support for the DROID videos — note: **AV1 codec**, different from the h264 RoboLab/Cosmos videos, must verify decode path works)

## Setup from a clean state

```bash
source /venv/main/bin/activate
export HF_HOME=/workspace/.hf_home
python3 -c "
from huggingface_hub import hf_hub_download
for f in [
    'success/meta/info.json', 'success/meta/stats.json', 'success/meta/tasks.parquet',
    'success/meta/episodes/chunk-000/file-000.parquet',
    'success/data/chunk-000/file-000.parquet',
    'success/videos/observation.image.wrist_image_left/chunk-000/file-000.mp4',
    'success/videos/observation.image.exterior_image_1_left/chunk-000/file-000.mp4',
    'success/videos/observation.image.exterior_image_2_left/chunk-000/file-000.mp4',
]:
    p = hf_hub_download('nvidia/Cosmos3-DROID', f, repo_type='dataset')
    print(f, '->', p)
"
```

## Models and data

- Cosmos checkpoint + exact revision: n/a
- Robometer checkpoint + exact revision: n/a
- IDM checkpoint + exact revision: n/a (not yet trained)
- DROID dataset release/split: `nvidia/Cosmos3-DROID`, `success` split, `chunk-000/file-000` only (data + all 3 camera videos + full meta)
- other inputs/assets: n/a

## RoboLab / experiment configuration

n/a for this run (pure data download/inspection, no RoboLab/Cosmos/Robometer execution)

## Exact commands

See Setup section above, plus a follow-up inspection script (to be written) that:
1. loads the parquet with pandas/pyarrow
2. groups rows by `episode_index`, reports episode count and frame-count-per-episode in this file
3. spot-checks `action.joint_position`/`action.gripper_position` ranges vs `action.joint_velocity`/`action.cartesian_position` to confirm they are numerically distinct (not accidentally aliased)
4. opens one episode's wrist video, confirms frame count matches the parquet row count for that episode
5. confirms `timestamp`/`frame_index` are monotonic and evenly spaced at 1/15s within an episode

## Expected outputs

- result directory: `/workspace/.hf_home/hub/datasets--nvidia--Cosmos3-DROID/` (HF cache)
- logs: inspection script stdout, captured in this run file
- videos/dreams: n/a
- metrics JSON: n/a
- checkpoints: n/a
- other artifacts: n/a

## Execution result

- start time: TBD
- end time: TBD
- wall time: TBD
- peak VRAM / throughput if relevant: n/a
- exit status: TBD
- warnings/errors: TBD

## Observed evidence

- validation/benchmark result: TBD
- task-level result: n/a
- candidate diversity: n/a
- Robometer: n/a
- IDM: TBD (schema/alignment findings)
- WISE: n/a
- artifact paths: TBD

## Outcome

- pass/fail: `SUPERSEDED_WITHOUT_FINAL_RESULT`
- what was proven: nothing independently claimable from this incomplete receipt; later runs proved DROID loading and legacy training paths
- what was **not** proven: the frozen production schema, selection, preprocessing, or architecture
- next action: use RUN_0020 and the current runbook; do not resume this obsolete download recipe

## Exact rerun recipe

See Setup section above.

## Reproducibility checklist

- [x] exact commits/revisions recorded
- [ ] exact environment/interpreters recorded
- [x] setup steps recorded
- [x] exact commands recorded
- [x] task/data budget recorded
- [x] seeds/randomness recorded (n/a — deterministic download/inspection)
- [x] configs/model revisions recorded
- [ ] outputs/artifacts recorded
- [x] no secrets recorded
- [ ] failed run preserved if applicable
