# Machine-Specific Runbook

Status: `M0-M3_VERIFIED`; production M4 IDM code is implemented, while manifest generation, preprocessing, training, and checkpoint verification are pending.

This file must be filled by `/setup-wise-robolab-research` and updated whenever the machine, source revision, or execution path changes.

This file stores the **canonical currently verified setup**. It does not replace per-run reproduction records. Every non-trivial execution must also have `research/runs/RUN_XXXX_<slug>.md` with the exact setup/commands/configuration used for that specific run.

## Git

- working repo: `/workspace/RoboLab`, `https://github.com/cheikh025/RoboLab` (origin)
- origin: `origin` = `https://github.com/cheikh025/RoboLab.git`
- upstream: `upstream` = `https://github.com/NVlabs/RoboLab.git`
- starting commit: `0aef241fb088ca21bb4ebd24448940ed56620d17` (origin/main)
- research branch: `wise/m0-setup`
- upstream revision inspected: `97bc1e766300a8c95656067ecb81e267e7e11823` (upstream/main, 2026-08-12)

## Hardware / OS

- GPU(s): 2x NVIDIA A100-SXM4-80GB
- VRAM: 81920 MiB each
- driver: 580.95.05 (R580 branch — the branch validated for Isaac Sim 5.0 per bootstrap notes; R590/595.x is known-problematic)
- CUDA: 13.0 (partial toolkit preinstalled; torch wheels bring their own runtime — see per-env versions below)
- CPU/RAM: 128 vCPU, 503GB RAM
- OS/kernel: Linux 6.8.0-52-generic, unprivileged Vast.ai Docker container (not a VM)
- free disk: 738GB on `/` (overlay). **`/workspace` is NOT a persistent volume on this instance** (`workspace_is_volume=false`) — everything here is lost on recycle/destroy; nothing survives except what's pushed off-box (e.g. to HF).
- **No sudo**: `claudeuser` has no working/passwordless sudo on this box, contrary to the generic vast-agents guide. Root-level actions (apt installs) go through the local provisioner API instead: `POST http://localhost:11111/capabilities/provision` with `{"inline_yaml": "..."}` (apt_packages/pip/git_repos/downloads), unauthenticated on localhost. See RUN_0000 for a worked example.

## RoboLab / Isaac environment

- interpreter: `/workspace/RoboLab/.venv/bin/python` (Python 3.11.15)
- Python: 3.11.15
- PyTorch: 2.7.0+cu128
- Isaac Sim: 5.0.0
- Isaac Lab: 2.2.0
- install command:
  ```bash
  git lfs install
  cd /workspace && git clone https://github.com/cheikh025/RoboLab.git && cd RoboLab
  git remote add upstream https://github.com/NVlabs/RoboLab.git && git fetch upstream
  uv venv --python 3.11 && source .venv/bin/activate
  uv sync --extra isaac50   # NOT isaac51 — pick one, never mix (different PhysX build)
  export OMNI_KIT_ACCEPT_EULA=Y
  ```
  Bare-container prerequisite (this box needed it — see Known failures below):
  ```bash
  curl -s -X POST http://localhost:11111/capabilities/provision -H "Content-Type: application/json" -d '{"inline_yaml": "version: 1\napt_packages:\n  - libatomic1\n  - libegl1\n  - libgl1\n  - libglu1-mesa\n  - libglx0\n  - libgomp1\n  - libsm6\n  - libxi6\n  - libxrandr2\n  - libxt6\n  - libglib2.0-0\n  - libnghttp2-14\n  - ca-certificates\n  - curl\n  - unzip\n  - libx11-dev\n  - tree\n  - wget\n"}'
  ```
- test command: `uv run pytest tests/ -q` (from `/workspace/RoboLab`, venv active, `OMNI_KIT_ACCEPT_EULA=Y` set). Pass signal on this box: all progress-bar characters are `.` (no `F`/`E`/`s`), exit code 0. **No trailing "N passed" summary line is printed** — Isaac Sim hard-exits on `AppLauncher` close before pytest's normal teardown runs; this is expected, not a failure.
- smoke command:
  ```bash
  sed -i 's/save_videos=False)/save_videos=True)/' examples/run_empty.py   # 1-line patch, keep applied
  uv run python examples/run_empty.py --task BananaInBowlTask --headless --num-steps 100
  ```
- output root: `/workspace/RoboLab/output/`
- task success/result files: `output/<run>/episode_results.jsonl` (one JSON line per episode: env_name/episode/success/instruction/score/reason), `output/<run>/<ENV_NAME>/log_0_env0.json` (subtask/event log), `output/<run>/<ENV_NAME>/env_cfg.json` (full config incl. renderer, provenance), `output/<run>/<ENV_NAME>/empty_0_numsteps100.mp4` (observation camera video, only when the `save_videos=True` patch above is applied)
- control rate: **15 Hz** — measured from `env_cfg.json`: `sim.dt=1/120s` (0.008333...), `decimation=8` -> `1/(dt*decimation)=15`
- task timeout semantics: `episode_length_s=50` in `env_cfg.json` -> ~750 control steps at 15Hz before timeout. Success is computed via a subtask state-machine of `DoneTerm` predicates (e.g. `object_grabbed(object=...)`, `object_in_container(object=..., container=..., ...)`), printed live during episode execution and logged to `log_0_env0.json`.

## Cosmos environment/server

- cosmos-framework path: `/workspace/cosmos-framework`
- revision: `a98dec05aa93ff6e2ebab2f38b590b86fe84f757`
- interpreter: `/workspace/cosmos-framework/.venv/bin/python`
- Python/PyTorch/CUDA: Python 3.13.13, torch 2.10.0+cu130 (isolated from RoboLab's env — never cross the two)
- checkpoint repo + revision: `nvidia/Cosmos3-Edge-Policy-DROID` @ `main` (**not** the script's Nano default — always pass `--checkpoint-path` explicitly). Auxiliary checkpoints pulled unconditionally at startup: `nvidia/Cosmos-Guardrail1` @ `d6d4bfa899a71454a700907664f3e88f503950cf`, `Qwen/Qwen3Guard-Gen-0.6B`, `Wan-AI/Wan2.2-TI2V-5B` (VAE only, `Wan2.2_VAE.pth`) @ `921dbaf3f1674a56f47e83fb80a34bac8a8f203e`. First cold start downloads all of these (~19 min on this box); cached afterward (~4 min restart).
- exact server command:
  ```bash
  cd /workspace/cosmos-framework
  export LD_LIBRARY_PATH=              # blank, deliberate — avoids Isaac Sim libs shadowing cosmos-framework's CUDA libs if both are sourced in the same shell (they shouldn't be, but belt-and-suspenders)
  export HF_HOME=/workspace/.hf_home
  export HF_HUB_DISABLE_XET=1          # works around a live hf-xet "Unable to parse string as hex hash value" bug
  /workspace/cosmos-framework/.venv/bin/python -m cosmos_framework.scripts.action_policy_server_robolab \
    --checkpoint-path nvidia/Cosmos3-Edge-Policy-DROID \
    --port 8000 \
    --format-prompt-as-json True \
    --decode-video               # omit if you don't need dream video; adds a VAE-decode pass per policy call
  ```
  Flag names verified via `--help` on this checkout: dashes, not underscores (e.g. `--checkpoint-path`, not `--checkpoint_path`).
- health/readiness check: `curl http://localhost:8000/healthz` -> `OK`. Ready log line (diff future runs against this):
  ```
  [robolab-policy-server] ready domain='droid_lerobot' resolution='480' action_space=joint_pos action_dim=8 chunk=32 history=1 use_state=True image=540x640 fps=15.0 guidance=3.0 num_steps=4 shift=5.0 seed=0 deterministic_seed=False
  ```
- action space: `joint_pos` — absolute joint-position commands, not end-effector deltas
- action dimension: 8 (7 arm joints + 1 gripper)
- action chunk size: 32 (one client `_needs_refresh` cycle = 32 executed env steps before the next policy call)
- conditioning fps: 15.0 (matches RoboLab's measured 15Hz control rate from M0 — verify this always matches when changing tasks/registrations)
- state input: `use_state=True`, `history_length=1`; joint position (7) + gripper position (1) sent as `observation/joint_position` / `observation/gripper_position`
- image layout: the client sends a **540x640x3** uint8 panel: wrist at the top (360x640), then exterior 1 and exterior 2 (180x320 each) side by side. The verified decoded dream is **528x640**. Its versioned transport contract is a fixed split at row 360: wrist `0:360, 0:640`, exterior 1 `360:528, 0:320`, exterior 2 `360:528, 320:640`. The earlier edge detector's row 359 is the final wrist row, so the corresponding Python split index is 360.
- decode-video mechanism: `--decode-video` (bare switch, no value) on the server adds a `"video"` key to the response: `uint8 numpy array, shape (T, H, W, 3)`, empirically measured as **(33, 528, 640, 3)** per policy call (33 = chunk 32 + 1 initial frame, 15fps -> 2.2s). The stock RoboLab client discards this field entirely — see the M1 client patch below to retain it.
- randomness/seed behavior: `seed=0` (base), `deterministic_seed=False` (default) -> **each call advances a NumPy RNG**, so repeated same-context requests return genuinely different candidates. Verified empirically (`research/tools/check_cosmos_diversity.py`, RUN_0002): K=5 identical requests -> pairwise action-chunk L2 distances mean=2.06 (min=1.26), zero duplicates. Do not assume this without checking — a fixed seed would silently collapse Best-of-K to K copies.
- exact client command:
  ```bash
  cd /workspace/RoboLab && source .venv/bin/activate && export OMNI_KIT_ACCEPT_EULA=Y
  uv run python policies/cosmos3/run.py --task BananaInBowlTask --num-envs 1 --headless
  ```
  Prerequisite (not in RoboLab's `pyproject.toml`, must install manually — and this uv venv has no `pip`, use `uv pip`):
  ```bash
  cd /workspace/RoboLab && uv pip install --no-cache-dir --no-deps \
    "openpi-client @ git+https://github.com/xuningy/openpi@aa6420561529593114160d05e5ad155792b272f3#subdirectory=packages/openpi-client"
  ```
- client response fields: `{"action": np.ndarray[32,8], "video": np.ndarray[33,528,640,3] | absent}`. Gripper channel is index 7 (last).
- gripper post-processing: the external DROID/RoboLab convention is 0=open, 1=closed. The official Cosmos server flips that value for its internal model convention and flips it back before returning the response. RoboLab then thresholds the returned float at 0.5. Do not add another polarity flip in the client, IDM server, or comparison path.
- dream-video retention patch: `policies/cosmos3/client.py` (commit `16513ca` on `wise/m0-setup`) — tracks `env_id` via `_extract_observation`, writes any `"video"` in the response to `<output_dir>/dreams/dream_env{id}_call{NNN}.mp4` using RoboLab's own `VideoWriter`, before returning the action array unchanged. Does not alter action semantics.

## Robometer environment

- repo path/revision: `/workspace/robometer` @ `5b815254bf31ee1bea3753c3a2da9f9033736d9a`
- interpreter: `/workspace/robometer/.venv/bin/python`
- Python/PyTorch/CUDA: 3.10.20, torch 2.8.0+cu128, CUDA available (verified)
- model repo/revision: `robometer/Robometer-4B`, default revision (~8.3GB on disk)
- install command:
  ```bash
  cd /workspace/robometer
  uv sync --extra robometer          # NOT plain `uv sync` — need transformers+trl
  uv pip install "torchao<0.10"      # REQUIRED FIX, see Known failures — re-apply after every fresh sync
  export HF_HOME=/workspace/.hf_home HF_HUB_DISABLE_XET=1
  hf download robometer/Robometer-4B   # or: /workspace/robometer/.venv/bin/hf download ...
  ```
- local inference command:
  ```bash
  cd /workspace/wise_robolab
  /workspace/robometer/.venv/bin/python research/tools/score_robometer.py \
    --run-dir <RoboLab task output dir, containing dreams/dream_env0_call*.mp4> \
    --sensor-video <path to the matching *_0.mp4 sensor video> \
    --task "<verbatim env instruction>"
  ```
- max frames/subsampling behavior: `max_frames=8` (from checkpoint config); `linspace_subsample_frames` keeps first+last frame always, discrete progress head with `num_bins=10`, `model_type=default`
- chosen view/input packaging: **one camera per call, three views scored independently, never composited** (RBM-1M has no tiled-frame examples; DROID deployment sends one exterior view). Split the decoded dream by the fixed 528x640 transport contract at row 360, not by content. Sensor panels (2560x360, head|left|right|wrist) use fixed column ranges; head is skipped.
- score scalarization: `last` (final-frame progress), full per-frame curves retained for later re-scalarization (e.g. `last - first`)
- measured latency/VRAM: approximate only — ~4-5s/call (model load amortized across 30 calls in ~2.5 min total); VRAM not sampled live. **Needs a dedicated micro-benchmark before fixing K in M3.**

## DROID data

- source: `nvidia/Cosmos3-DROID@5c11a20accb11497270a5247a7f1e66ad04c956c`, pinned in code and checkpoint configuration
- identity: success and failure roots have independent numeric episode namespaces; the canonical key is `(dataset_split, episode_index)`. Join the official `episode_id` to raw DROID `metadata_*.json` for `lab`, `building`, `scene_id`, `uuid`, and `robot_serial`. Use `lab|building|scene_id` as the reproducible raw-scene key.
- population: 71,907 published episodes; 71,253 are eligible for one 33-frame window (`length>=33`), comprising 57,584 successes and 13,669 failures. The 654 shorter episodes are excluded only because they cannot produce the required input/target pair.
- image fields: `observation.image.wrist_image_left`, `observation.image.exterior_image_1_left`, `observation.image.exterior_image_2_left`; native 640x360 RGB at 15 Hz
- target fields: `action.joint_position` (7 absolute commanded joint positions) and `action.gripper_position` (source float in [0,1], thresholded at `>0.5` for the executed/training binary target, 0=open and 1=closed)
- split: deterministic 21,000 train and 1,000 validation manifests using the exact eligible-population lab x outcome quotas in `research/IDM_DESIGN.md`; all labs and both outcomes are retained, and validation raw scenes are excluded entirely from train. There is no test split.
- windows: every selected frame is retained; no idle or content filtering. Train uses stride 16 plus an end-aligned tail, validation uses stride 32 plus an end-aligned tail.
- alignment: frames `s..s+32` label actions `s..s+31`; action row `t` is the command across visual transition `frame[t] -> frame[t+1]`
- preprocessing: aspect-preserving, no-crop letterbox to 128x224 with one canonical Torch bilinear-antialias implementation for training and inference
- provenance/audit: store source revision, manifest SHA256, joint quota counts, episode/scene overlap checks, window counts/shares, and all three cameras' shard episode/frame/window shares

## IDM

- implementation path: `/workspace/wise_idm/` (separate repository). Production entry points are `build_selection_catalog.py`, `select_manifests.py`, `preprocess_videos.py`, `train.py`, `verify_checkpoint.py`, `infer_on_dream.py`, and `idm_server.py`.
- architecture ID: `wise_resnet50_transformer_v1`, approximately 34.85M parameters. For each adjacent pair and camera, concatenate RGB into six channels; use shared torchvision ResNet50 `IMAGENET1K_V2` weights through layer3; apply full-channel spatial softmax to the 1024x8x14 map; project to width 512; fuse the three views with a two-layer Transformer; process all 32 transitions with a six-layer, eight-head, noncausal temporal Transformer; predict aligned 7-D joints and one binary gripper logit directly. There is no proprioception, action-query decoder, action encoder, verifier branch, language, or Cosmos feature path.
- loss/defaults: train-only per-joint mean/std, standardized SmoothL1 joints, class-balanced binary gripper BCE; AdamW, OneCycleLR, BF16, batch 1/GPU, gradient accumulation 8, learning rate `1e-4`, 20 epochs. Checkpoints include architecture/data/preprocessing/manifests/stats, optimizer/scheduler/scaler, and RNG state for guarded resume.
- production checkpoint: **pending**. RUN_0009 through RUN_0019 are immutable legacy/pilot history and are not compatible production checkpoints.
- canonical commands (create a run receipt and replace paths before execution):
  ```bash
  cd /workspace/wise_idm
  python3 build_selection_catalog.py --raw-metadata /data/droid_raw/1.0.1 --output manifests/catalog.parquet
  python3 select_manifests.py --catalog manifests/catalog.parquet --out-dir manifests --seed 0
  python3 preprocess_videos.py --manifest manifests/train_21k.csv
  python3 preprocess_videos.py --manifest manifests/val_1k.csv
  torchrun --standalone --nproc_per_node=2 train.py --mode train \
    --train-manifest manifests/train_21k.csv --val-manifest manifests/val_1k.csv \
    --batch-size 1 --gradient-accumulation 8 --epochs 20 --lr 1e-4 \
    --out-dir checkpoints_production --log-dir tb_logs_production
  python3 verify_checkpoint.py --checkpoint checkpoints_production/best.pt \
    --val-manifest manifests/val_1k.csv --batch-size 1
  ```

## WISE integration

- selector implementation path: `/workspace/RoboLab/policies/wise/bestofk_client.py` (`BestOfKClient`), `policies/wise/run_bestofk.py`. Robometer-only so far (M3); IDM `r_cons` and fused WISE selection are M6.
- candidate-generation hook: `BestOfKClient.infer()` overrides the base `InferenceClient.infer()` — builds one `_pack_request()` call and reuses it for K `_query_server()` calls before any execution (relies on the server's `deterministic_seed=False`, verified diverse in RUN_0002/RUN_0005)
- raw score logging path: `<output_dir>/wise_decisions.jsonl` (per decision: k, selector, per-candidate scores, selected index, generation/scoring latency, per-candidate action mean/std); every candidate's dream video also saved to `<output_dir>/dreams/dream_env{id}_call{NNN}_{cand{i}|selected{i}}.mp4`
- Robometer scoring server: `research/tools/robometer_server.py` (in the `wise_robolab` project) — minimal FastAPI wrapper around the exact `load_robometer()`/`score()` path verified in M2's RUN_0004, run with the robometer interpreter:
  ```bash
  export HF_HOME=/workspace/.hf_home
  /workspace/robometer/.venv/bin/python research/tools/robometer_server.py --port 8100
  ```
  `GET /health`, `POST /score` (multipart `.npy` upload of `(T,H,W,3)` uint8 wrist-view frames + `task` form field -> `{"per_frame": [...], "last": float}`). Chosen over robometer's own generic `/evaluate_batch_npy` (designed for the training/eval trajectory-dict shape, unverified for this single-clip use case).
- calibration config: none yet (single-term `r_task` only)
- fusion weights config: none yet (M6)
- action prefix: full 32-step chunk of the selected candidate (native Cosmos commitment, matching the B=1 baseline)
- K: 3 in validation runs (RUN_0005); not yet tuned/scaled (M7)

## Evaluation

- baseline task panel:
- full RoboLab protocol intended:
- episodes per task:
- seed/initialization handling:
- resume command:
- aggregation command:

## Known failures / machine-specific traps

- **No sudo on this box.** `sudo -n true` -> "a password is required"; `/etc/sudoers.d/user` exists but is password-gated and no password is available. Contradicts the generic vast-agents guide's "root or passwordless sudo" claim — verify per-instance, don't assume. Workaround: local provisioner API at `localhost:11111/capabilities/provision` runs as root (instance_portal service), unauthenticated on localhost. Confirmed working for apt package installs.
- **Bare-container missing system libs** (predicted by `research/bootstrap/robolab_new_machine_setup.md` §9.4, confirmed here): `libGLU.so.1`, `libSM.so.6`, `libXt.so.6` (and friends) are absent by default. Symptom on this box was **not** the documented segfault-at-`createHydraEngine` — instead `uv run pytest tests/` exited 0 almost immediately (after a `uv` dependency resync, before Isaac Sim booted or any test ran), which is easy to misread as a fast pass. Always sanity-check wall time and dot-count, not just exit code, on a fresh box. Fix: apt-install the lib list in the RoboLab/Isaac section above.
- **`uv`'s managed-Python install dir may not be writable.** System-level `UV_PYTHON_INSTALL_DIR=/.uv/python_install` on this image is `root:root`, mode `drwxrwxr-x` (group-writable, but `claudeuser` isn't in the `root` group) -> `uv sync` in a fresh project needing a not-yet-cached interpreter (e.g. cosmos-framework's managed CPython 3.13) fails with `Permission denied` creating a temp dir. Fix: `export UV_PYTHON_INSTALL_DIR=/workspace/.uv_python_install` (added to `~/.bashrc` on this box) before any `uv sync` that might need a new interpreter. RoboLab's own `uv venv --python 3.11` happened to work because 3.11 was apparently already cached.
- **`Warp CUDA error: Failed to get driver entry point 'cuDeviceGetUuid'` / `CUDA error 36`**: appeared during `run_empty.py` (not during `pytest`). Driver here (580.95.05) is on the validated R580 branch per bootstrap notes, and the run completed successfully end-to-end — treated as benign noise on this box, distinct from the R590/`ERROR_DEVICE_LOST` failure mode. Re-open this if a run actually fails with `ERROR_DEVICE_LOST`.
- **`omni.usd` "Unresolved reference prim path" warnings for unrelated scenes** (e.g. `assets/scenes/ladle_pot.usda`) appear during startup even when running a different task (`BananaInBowlTask`) — RoboLab evidently USD-validates multiple registered scenes at process boot. Benign; pre-existing asset-library warning, not caused by local changes.
- **Robometer: `ImportError: cannot import name 'ScalingType' from 'torch.nn.functional'`** on any import that touches `robometer.utils.save` (-> `peft` -> `transformers.quantizers.quantizer_torchao` -> `torchao`). Cause: `torchao` is pulled in transitively (not pinned in `robometer/pyproject.toml`, likely via `unsloth`/`trl`) and resolves to a version (`0.18.0` observed) that needs torch APIs newer than the pinned `torch==2.8.0`. Fix: `uv pip install "torchao<0.10"` (resolves to `0.9.0`) inside the robometer venv. This is **not** persisted in `pyproject.toml`, so **re-apply after every fresh `uv sync --extra robometer`** until upstream pins a compatible version.
- **Decoded dream geometry differs from the request panel.** The client sends 540x640 but the verified decoded video is 528x640. Use the versioned fixed split at row 360. The historical detected boundary row 359 is the last wrist pixel, not a competing split index. Content-based seam detection is not part of production IDM preprocessing.
