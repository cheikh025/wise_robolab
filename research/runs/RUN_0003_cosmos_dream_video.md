# RUN_0003 — Cosmos3-Edge native dream-video retention

## Identity

- status: `COMPLETED`
- run class: `validation`
- milestone: M1_COSMOS
- associated progress report: research/progress/PROGRESS_0001_COSMOS.md
- date/time: 2026-08-12 (~07:42Z)
- operator/agent: Claude Code (autonomous /goal run)

## Purpose

- exact question this run answers: with the server started with `--decode-video`, does the stock (now minimally patched) client correctly retain the server's native imagined-rollout video without altering the action path or baseline control behavior?
- pass/fail criterion: dream `.mp4` file(s) are written, non-empty, playable, with a sane frame count/shape (per-call, not per-step); the same episode's action-execution behavior (success/score) is not changed by enabling video decode (beyond expected latency/memory overhead).
- why this task/data budget is sufficient for this validation: 1 task, 1 env, 1 episode — same wiring-validation budget as RUN_0001. This is an infra/plumbing check (does the byte pipe work), not a policy-quality measurement.

## Code state

- RoboLab repo: `/workspace/RoboLab`, branch `wise/m0-setup`
- branch: `wise/m0-setup`
- commit: uncommitted at time of run — new diff in `policies/cosmos3/client.py` (see below), to be committed after this run passes
- relevant uncommitted diff: `policies/cosmos3/client.py` — added `_save_dream()`, `_cur_env_id` tracking (set in `_extract_observation`, which already receives `env_id`), `_dream_call_counters` dict, and a `video = response.get("video")` check in `_unpack_response()` that writes the video via RoboLab's own `VideoWriter` (reused, not reinvented) to `<output_dir>/dreams/dream_env{env_id}_call{NNN}.mp4` before returning the action array unchanged. Imports added: `os`, `robolab.constants.get_output_dir`, `robolab.core.utils.video_utils.VideoWriter`.
- upstream revision if relevant: unchanged
- Cosmos/cosmos-framework revision: unchanged (`a98dec05aa93ff6e2ebab2f38b590b86fe84f757`)
- Robometer revision: n/a
- IDM/WISE code revision: n/a

## Machine and environments

- host/GPU: same box, unchanged
- driver/CUDA: unchanged
- Isaac Sim / Isaac Lab: unchanged (5.0.0 / 2.2.0)
- RoboLab interpreter: `/workspace/RoboLab/.venv/bin/python`
- Cosmos interpreter: `/workspace/cosmos-framework/.venv/bin/python`
- Robometer interpreter: n/a
- IDM interpreter: n/a
- key package versions: unchanged from RUN_0001

## Setup from a clean state

Same as RUN_0001, plus:

```bash
# server, this time with --decode-video (checkpoints already cached from RUN_0001, so boot is fast)
cd /workspace/cosmos-framework
export LD_LIBRARY_PATH= HF_HOME=/workspace/.hf_home HF_HUB_DISABLE_XET=1
/workspace/cosmos-framework/.venv/bin/python -m cosmos_framework.scripts.action_policy_server_robolab \
  --checkpoint-path nvidia/Cosmos3-Edge-Policy-DROID --port 8000 --format-prompt-as-json True --decode-video

# client: same command as RUN_0001, now with the video-retention patch active
cd /workspace/RoboLab && source .venv/bin/activate && export OMNI_KIT_ACCEPT_EULA=Y
uv run python policies/cosmos3/run.py --task BananaInBowlTask --num-envs 1 --headless
```

Required environment variables: same as RUN_0001.

## Models and data

- Cosmos checkpoint + exact revision: `nvidia/Cosmos3-Edge-Policy-DROID` (already cached locally from RUN_0001, no re-download expected)
- Robometer checkpoint + exact revision: n/a
- IDM checkpoint + exact revision: n/a
- DROID dataset release/split: n/a
- other inputs/assets: n/a

## RoboLab / experiment configuration

- task(s): `BananaInBowlTask`
- exact instruction(s): "Pick up the banana and place it in the bowl" (same as RUN_0001)
- num envs: 1
- num runs / episodes: 1
- seeds/randomness: same defaults as RUN_0001 (env seed=0; server seed=0, deterministic_seed=False — so this specific episode's exact trajectory need not reproduce RUN_0001's bit-for-bit, stochastic sampling is expected)
- simulator/physics stack: unchanged
- episode timeout semantics: unchanged (episode_length_s=50 -> 750 steps @ 15Hz)
- candidate budget K: 1 (still B=1; decode-video does not change K)
- action horizon/prefix: chunk=32, unchanged
- Cosmos generation settings: unchanged (guidance=3.0, num_steps=4, unipc, shift=5.0) plus `decode_video=True`
- Robometer view/scalarization: n/a
- IDM preprocessing/config: n/a
- `r_exec` config: n/a
- calibration/fusion config: n/a

## Exact commands

```bash
# terminal 1
cd /workspace/cosmos-framework
export LD_LIBRARY_PATH= HF_HOME=/workspace/.hf_home HF_HUB_DISABLE_XET=1
/workspace/cosmos-framework/.venv/bin/python -m cosmos_framework.scripts.action_policy_server_robolab \
  --checkpoint-path nvidia/Cosmos3-Edge-Policy-DROID --port 8000 --format-prompt-as-json True --decode-video

# terminal 2
cd /workspace/RoboLab && source .venv/bin/activate && export OMNI_KIT_ACCEPT_EULA=Y
uv run python policies/cosmos3/run.py --task BananaInBowlTask --num-envs 1 --headless
```

## Expected outputs

- result directory: `/workspace/RoboLab/output/<timestamp>_cosmos3/`
- logs: `log_0_env0.json`
- videos/dreams: `BananaInBowlTask/dreams/dream_env0_call000.mp4`, `..._call001.mp4`, ... (one per policy chunk, ~155/32 ≈ 5 calls expected based on RUN_0001's early-success episode length)
- metrics JSON: `episode_results.jsonl`
- checkpoints: n/a
- other artifacts: sensor + viewport videos (as RUN_0001)

## Execution result

- start time: 2026-08-12T07:36:51Z (server ready) / 2026-08-12T07:37:11Z (episode start)
- end time: 2026-08-12T07:37:~57Z (episode complete, 141 steps @ dt=0.0667 -> 9.4s sim time, wall time similar order to RUN_0001's ~67s)
- wall time: server restart to ready: ~4 min (fast — checkpoints cached from RUN_0001); episode: same order as RUN_0001
- peak VRAM / throughput if relevant: not sampled; decode-video adds a VAE-decode pass per policy call but did not visibly change per-call latency order of magnitude
- exit status: 0
- warnings/errors: none new; same benign Warp/CUDA-driver-entry-point warning as prior runs
- disk: `df -h /` still 10% used after this run (dream videos are small — 5 files x ~2.2s each)

## Observed evidence

- validation/benchmark result: **PASS**. `_save_dream()` fired on every policy chunk and wrote a real, playable h264 `.mp4` for each.
- task-level result: `BananaInBowlTask_0`, success=true, episode_step=141 (vs. RUN_0001's 155 — different because `deterministic_seed=False` samples a new trajectory each run, expected and consistent with RUN_0002's diversity finding). Confirms enabling `--decode-video` + the client patch did not break or otherwise visibly alter the action-execution path — same instruction, same policy, still succeeds.
- candidate diversity: n/a (B=1, covered separately in RUN_0002)
- Robometer: n/a
- IDM: n/a
- WISE: n/a
- artifact paths:
  - `/workspace/RoboLab/output/2026-08-12_07-37-11_cosmos3/BananaInBowlTask/dreams/dream_env0_call{000..004}.mp4` — 5 files, one per policy chunk (episode needed 5 replans: ceil(141/32)=5, matches)
  - each dream: h264, **640x528**, **33 frames**, 2.2s duration (33 frames @ 15fps) — empirically measured via `ffprobe`, matching the robometer bootstrap notes' previously-recorded geometry `(33, 528, 640, 3)` (VAE decode rounds 540 input height down to 528, a multiple of 16 — consistent with `spatial_compression_factor=16` seen in the server's model config log in RUN_0001)
  - normal sensor/viewport videos and `episode_results.jsonl` also present, unaffected

## Outcome

- pass/fail: **PASS**
- what was proven: the server's native imagined-rollout video (returned only when `--decode-video` is set) can be retained end-to-end with a minimal, clean client patch (~25 lines: track `env_id`, reuse RoboLab's own `VideoWriter`, write to `<output_dir>/dreams/`) without touching the action path — `_unpack_response` still returns `np.asarray(response["action"])` unchanged, just with a side-effecting save first. Frame count/geometry (33 frames, 640x528) verified empirically, not assumed from documentation, per M1 skill guidance.
- what was **not** proven: whether the dream content is *useful* for anything downstream (Robometer scoring, IDM consistency) — that's M2/M5. Also not proven: behavior under `--num-envs > 1` (dream saving keyed by `env_id`, but only tested with 1 env here — multi-env dream attribution is a follow-up check before M3's Best-of-K, since Best-of-K needs K candidates per single env, not multiple envs, so this is likely fine but worth a quick sanity check when M3 is implemented).
- next action: commit the `policies/cosmos3/client.py` diff on `wise/m0-setup`, then write `PROGRESS_0001_COSMOS.md`, update `RUNBOOK.md`/`STATE.md`/`EXPERIMENTS.jsonl`, mark M1 `MILESTONE_PASS`, hand off to M2 (`/validate-robometer-on-cosmos`).

## Exact rerun recipe

```bash
cd /workspace/cosmos-framework
export LD_LIBRARY_PATH= HF_HOME=/workspace/.hf_home HF_HUB_DISABLE_XET=1
/workspace/cosmos-framework/.venv/bin/python -m cosmos_framework.scripts.action_policy_server_robolab \
  --checkpoint-path nvidia/Cosmos3-Edge-Policy-DROID --port 8000 --format-prompt-as-json True --decode-video &
cd /workspace/RoboLab && source .venv/bin/activate && export OMNI_KIT_ACCEPT_EULA=Y
uv run python policies/cosmos3/run.py --task BananaInBowlTask --num-envs 1 --headless
```

## Reproducibility checklist

- [x] exact commits/revisions recorded
- [x] exact environment/interpreters recorded
- [x] setup steps recorded
- [x] exact commands recorded
- [x] task/data budget recorded
- [x] seeds/randomness recorded
- [x] configs/model revisions recorded
- [ ] outputs/artifacts recorded
- [x] no secrets recorded
- [ ] failed run preserved if applicable
