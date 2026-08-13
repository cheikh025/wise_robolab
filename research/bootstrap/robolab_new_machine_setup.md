# RoboLab — new-machine setup and smoke test

Bring a fresh Linux GPU box from nothing to "a task ran and I have the video".
**No policy server, no model download.** Assets ship with the clone.

One path only. Do the steps in order.

Derived by reading this repo's source and docs, not by executing it (the fork was
inspected from a Windows workstation). File references are given so anything can be
re-checked.

---

## 1. What you are installing, in one picture

```
                    ┌─────────────────────────────────────────┐
   your model  ───► │  policy server  (separate process/host) │   ← NOT needed for this doc
   (later)          └─────────────────────────────────────────┘
                                    ▲ websocket / http
                                    │
   ┌────────────────────────────────┴──────────────────────────────────┐
   │  RoboLab  =  Isaac Sim + Isaac Lab  +  120 task definitions       │
   │  · robolab/tasks/benchmark/*.py     — 120 tasks, one file each    │
   │  · robolab/registrations/droid/     — turns a task into a gym env │
   │  · robolab/eval/                    — episode loop, results, video│
   │  · assets/                          — USD scenes/objects (~7 GB)  │
   └───────────────────────────────────────────────────────────────────┘
```

RoboLab is a **client**: the simulator and the benchmark live here, the policy lives
elsewhere. That is why you can install and fully verify this half on its own — which is
exactly what this document does.

Key facts, from source:

| thing | value | where |
|---|---|---|
| tasks | **120** files | `robolab/tasks/benchmark/` |
| task discovery | `auto_register_droid_envs(task_dirs=['benchmark'], ...)` | `robolab/registrations/droid/auto_env_registrations_jointpos.py:29` |
| default cameras | `WRIST_LEFT` = `OverShoulderLeftCameraCfg` + `WristCameraCfg` | `robolab/registrations/droid/camera_presets.py:28` |
| viewport camera | `EgocentricMirroredCameraCfg`, attached separately for video | same file, `:67` |
| control rate | `dt = 1/120`, `decimation = 8` → **15 Hz** | DROID env registration |
| success | state-based `DoneTerm` predicate, checked every step | e.g. `robolab/tasks/benchmark/rubiks_cube_task.py` |
| output root | `<repo>/output/` | `robolab/constants.py:14` |

---

## 2. Prerequisites

| requirement | value |
|---|---|
| OS | **Ubuntu 22.04+** (Linux GPU host, not Windows) |
| Python | **3.11** |
| GPU | NVIDIA RTX, **48 GB+ VRAM recommended**; smaller cards work at `--num_envs 1` |
| disk | **~8 GB** (assets ~7 GB) |
| `uv` | https://docs.astral.sh/uv/getting-started/installation/ |

---

## 3. Clone

All USD/mesh/texture assets are **git-lfs** objects (`.gitattributes` covers `*.usd`,
`*.usda`, `*.obj`, `*.stl`, `*.ply`, `*.png`, `*.hdr`, `*.exr`, `*.hdf5`, …). Without
`git-lfs` the clone still succeeds, but every asset is a small text pointer and the first
`create_env` dies deep inside USD loading. Install it **before** cloning.

```bash
sudo apt update && sudo apt install -y git-lfs ffmpeg
git lfs install

git clone https://github.com/cheikh025/RoboLab.git
cd RoboLab
```

A healthy clone reports LFS work, e.g.:

```
Filtering content: 100% (1635/1635), 5.75 GiB | 2.42 MiB/s, done.
```

Verify the assets are real files, not pointers:

```bash
du -sh assets/                          # expect several GB, not a few MB
file assets/objects/*/*.usd | head -3   # must NOT say "ASCII text"
git lfs ls-files | wc -l                # expect ~1635
```

If they are pointers: `git lfs install && git lfs pull`.

### If you are on a bare container

Skip this if you are on a workstation or a container built `FROM nvcr.io/nvidia/isaac-lab`
(RoboLab's own `docker/Dockerfile` does) — those already carry Isaac Sim's system libraries.

On a plain Ubuntu image (rented GPU box, minimal container) they are missing, and Isaac Sim
segfaults on the **first `create_env`**, not at import — so the install looks fine right up
until you run something. NVIDIA's own Isaac Sim Dockerfile installs:

```bash
apt-get update && apt-get install -y --no-install-recommends \
  libatomic1 libegl1 libgl1 libglu1-mesa libglx0 libgomp1 \
  libsm6 libxi6 libxrandr2 libxt6 libglib2.0-0 libnghttp2-14 \
  ca-certificates curl unzip
```

On Ubuntu 24.04 `libxt6` and `libglib2.0-0` are virtual names satisfied by `libxt6t64` /
`libglib2.0-0t64` via `Provides:`; if apt refuses either, add the `t64` suffix.

The crash signature when they are absent — see §9.4 for the full read.

---

## 4. Install

```bash
cd RoboLab
uv venv --python 3.11
source .venv/bin/activate
uv sync --extra isaac50
export OMNI_KIT_ACCEPT_EULA=Y     # put in ~/.bashrc; cached after first acceptance
```

`isaac50` = Isaac Sim 5.0 / Isaac Lab 2.2.0. **Use this and only this.** The repo also
declares an `isaac51` extra; it ships a different PhysX build, so grasping and settling
dynamics differ and results are not comparable across the two. Pick one, record it, never
mix.

If you skip `source .venv/bin/activate`, prefix every command below with `uv run`.

---

## 5. Verify the install

```bash
uv run pytest tests/
```

This is a real end-to-end check, not a lint. `tests/conftest.py` boots Isaac Sim once for
the session (and sets `OMNI_KIT_ACCEPT_EULA=Y` itself, so no prompts); the suite asserts
isaaclab is importable, all 120 task definitions are valid, the env factory is populated,
and one full episode runs (`tests/test_run_empty.py` creates `BananaInBowlTask`, resets,
steps 5 times, calls `end_episode`, closes).

`test_run_empty` **skips itself when CUDA is unavailable** — a "passed" on a CPU box proves
less than it looks. Check the output says `passed`, not `skipped`.

---

## 6. Smoke test — random episode, with video

`examples/run_empty.py` drives the env with random actions
(`sample_space(env.single_action_space, ...)`), but it calls the episode helper with video
**hardcoded off** at `examples/run_empty.py:118-119`:

```python
save_image=False,
save_videos=False)
```

The helper itself fully supports writing video (`examples/episodes.py:228-264`:
`VideoWriter` at `1/(render_interval*dt)` = 15 fps, frames from `over_shoulder_left_camera`,
written to `empty_{episode}_numsteps{steps}.mp4`). Flip the flag — this is why you forked:

```bash
sed -i 's/save_videos=False)/save_videos=True)/' examples/run_empty.py
git diff --stat examples/run_empty.py     # expect exactly 1 changed line
```

Then run it:

```bash
uv run python examples/run_empty.py --task BananaInBowlTask --headless --num-steps 100
```

Expected: the env registers, the instruction prints, a 100-step tqdm bar runs, and output
lands under `output/run_empty_env/`. The video is at:

```
output/run_empty_env/<ENV_NAME>/empty_0_numsteps100.mp4
```

`<ENV_NAME>` is the registered env, which appends the scene to the task class name
(e.g. `BananaInBowlTaskHomeOffice`). Set `save_image=True` in the same call to also drop
`empty_0.png`.

### Done when

- [ ] `uv run pytest tests/` passes with CUDA present (not skipped)
- [ ] `run_empty.py` completes without a traceback
- [ ] the `.mp4` exists and plays, showing the scene from the over-shoulder-left camera
- [ ] `output/run_empty_env/` contains `results.json` / `episode_results.jsonl` and
      `log_0_env0.json`

Nothing above touches a policy server, so a pass means **the simulator half is fully
working**.

---

## 7. Picking a task

`--task` takes the **task class name** (e.g. `BananaInBowlTask`), and `get_envs(task=...)`
expands it to every registered variant.

```bash
ls robolab/tasks/benchmark/ | wc -l                          # 120
grep -rn '"default":' robolab/tasks/benchmark/ | head -40    # instructions
```

For smoke tests use what the repo itself uses: **`BananaInBowlTask`** (the default in
`tests/conftest.py` and every example) or `RubiksCubeAndBananaTask` — the README calls
these two "good for sanity checking".

**There is no ice-cream / pink-plate task in RoboLab-120.** Grepped the whole repo for
`ice cream`, `icecream`, and `pink plate` — zero hits in tasks or assets. Nearest existing:
`pink_spoon_in_pot.py` ("Put the pink spaghetti spoon in the pot"),
`cooking_pick_pasta_tool.py` (pink tool), and the plate tasks
(`bagel_on_plate_task.py`, `banana_on_plate_task.py`, `fruits_to_plate.py`, …).

---

## 8. Where output goes

```
output/
└── <output_folder>/                       # run_empty_env, or <timestamp>_<policy>
    ├── episode_results.jsonl              # one self-contained JSON per episode
    ├── <ENV_NAME>/
    │   ├── run_0.hdf5                     # demo_0..demo_{N-1}, one per env
    │   ├── log_0_env0.json                # subtask/event log
    │   ├── empty_0_numsteps100.mp4        # observation camera
    │   └── env_cfg.json                   # full env config incl. renderer — provenance
```

`output/` is already gitignored (`**/output/`). Full field reference: `docs/data.md`.

---

## 9. Gotchas

1. **Always `--headless` for anything multi-task.** In GUI mode Kit's viewport leaks GPU
   VRAM across `create_env`/`env.close()` cycles until OOM — an IsaacLab 2.2.0 / Kit issue,
   documented in `docs/known_issues.md`. Headless never creates the viewport, so no leak.
2. **`cv2` must be imported before `isaaclab`.** Every entry script does
   `import cv2  # noqa` first, with a "do not remove" comment. Keep that ordering in
   anything you write.
3. **git-lfs pointers** — §3. The failure surfaces as a USD load error, not a clear message.
4. **Segfault at `createHydraEngine`** = missing system libs (§3, bare container). Read the
   Kit log bottom-up; the fatal frames are `librtx.mdltranslator.plugin.so` →
   `libcarb.scenerenderer-rtx.plugin.so` → `libomni.hydra.rtx.plugin.so` →
   `UsdManager::createHydraEngine`, and further up sits the real cause:

   ```
   Could not load .../libneuray.so. Error: libGLU.so.1: cannot open shared object file
   Could not load .../libMaterialXRenderGlsl.so. Error: libXt.so.6: cannot open ...
   ```

   `libGLU.so.1` absent → iray's `libneuray.so` fails → the MDL translator dies when the
   RTX renderer initializes. The `GLFW initialization failed` and
   `failed to open the default display` lines are **normal headless noise**, not the fault.
5. **Rendering artefacts** from the previous scene linger briefly after a scene swap —
   known IsaacLab/RTX behaviour, rare on recommended GPUs.
6. **If the driver is on the R590 branch (595.x)**, expect trouble with the Omniverse RTX
   renderer — the validated branch is R580 (`580.65.06`). A tell that shows up early, even
   when the run still proceeds:

   ```
   Warp CUDA error: Failed to get driver entry point 'cuDeviceGetUuid'
   Warp CUDA error 36: API call is not supported in the installed CUDA driver
   ```

   Isaac Sim 5.0's bundled Warp predates CUDA 13.x drivers. The reported R590 failure mode
   is `ERROR_DEVICE_LOST` during renderer init — distinct from the missing-lib segfault in
   §9.4, so check the libs first. No known workaround beyond downgrading, which a rented
   box may not allow.
7. **`--num-runs` vs `--num_envs`**: total episodes = `num_runs × num_envs`. Prefer more
   envs; only add runs when VRAM says no. Per-task ceilings measured on a 48 GB L40 are in
   `docs/env_vram_size_guide.md`.

---

## 10. What comes next (not in this doc)

Once the above passes, the policy half is a separate, independent bring-up:

- `policies/README.md` — the client interface
- `policies/dreamzero/README.md` — DreamZero server + `--remote-host/--remote-port 5000`
- `policies/cosmos3/README.md` — Cosmos3 server on port 8000
- `docs/policy.md` — writing a client for a new model

Neither requires anything in this document to change.

---

## 11. Source map — where to look when something is wrong

| question | file |
|---|---|
| how is a task defined? | `robolab/tasks/benchmark/<task>.py` |
| how does a task become an env? | `robolab/registrations/droid/auto_env_registrations_jointpos.py` |
| how is an episode run? | `robolab/eval/episode.py`, `robolab/eval/runner.py` |
| how is success decided? | the task's `DoneTerm` + `robolab/core/task/conditionals.py` |
| where do results/videos get written? | `robolab/core/logging/results.py`, `robolab/core/utils/video_utils.py` |
| CLI flag reference | `docs/environment_run.md` |
| output/HDF5 layout | `docs/data.md` |
| debugging flags (`VERBOSE`, `DEBUG`, `VISUALIZE`) | `docs/debug.md` |
| known breakage | `docs/known_issues.md` |
