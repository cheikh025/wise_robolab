# Cosmos3-Edge-Policy-DROID on RoboLab — the verified runbook

Bringing up the **Cosmos3-Edge-Policy-DROID** policy server and evaluating a single RoboLab
task against it, on one Vast.ai box.

Assumes [`vast_isaaclab_template.md`](./vast_isaaclab_template.md) is done: the
`nvcr.io/nvidia/isaac-lab:2.2.0` template, RoboLab cloned at
`/workspace/isaaclab/RoboLab`, `run_empty.py` producing video.

**Verified through §5** — the server is up and reporting ready. **§6 (the client run) has not
been executed yet**; it is transcribed from source, not from a successful run. Everything
before it was performed and its output recorded.

Dead ends are in §9 so they aren't repeated — **do not deviate into them.**

---

## 0. The one rule that matters on this box

**Always call interpreters by absolute path. Never rely on `source .venv/bin/activate`.**

Two Pythons coexist here and one is Isaac Sim's non-standard embedded build. Worse, bash
caches resolved command paths, so `which python` and the `python` that actually runs can
disagree — which is exactly what happened, and it cost an hour (§9.1).

| purpose | interpreter |
|---|---|
| RoboLab / Isaac Sim | `/workspace/isaaclab/_isaac_sim/python.sh` |
| Cosmos policy server | `/workspace/cosmos-framework/.venv/bin/python` |

Never cross them. Never install one's packages with the other.

---

## 1. Client side — `openpi-client`

`policies/cosmos3/client.py:9` imports `openpi_client`, which is **not** in RoboLab's
`pyproject.toml`. It only exists in RoboLab's Dockerfile, which this install path bypasses.
Same pinned commit, same `--no-deps`:

```bash
/workspace/isaaclab/_isaac_sim/python.sh -m pip install --no-cache-dir --no-deps \
  "openpi-client @ git+https://github.com/xuningy/openpi@aa6420561529593114160d05e5ad155792b272f3#subdirectory=packages/openpi-client"

/workspace/isaaclab/_isaac_sim/python.sh -c "import openpi_client; print('ok')"
```

`--no-deps` is deliberate — numpy, websockets and msgpack-numpy are already satisfied, and
letting pip resolve them risks replacing Isaac Sim's torch.

---

## 2. System deps and uv

```bash
apt-get update && apt-get install -y --no-install-recommends \
  curl ffmpeg git-lfs libx11-dev tree wget

curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv --version        # cosmos-framework requires >= 0.11.3
```

That apt list is cosmos-framework's own prerequisite set, verbatim from its README.

---

## 3. Install cosmos-framework

```bash
cd /workspace
git clone https://github.com/NVIDIA/cosmos-framework.git
cd cosmos-framework

uv sync --all-extras --group=cu130-train --group=policy-server
```

**Do not pre-create the venv** and do not pass `--python`. `uv sync` deletes any existing
`.venv` and rebuilds it with its own managed CPython (3.13.14 here). Let it.

`--group=policy-server` is required — it provides `openpi-server`. The repo README's native
install only shows `cu130-train`; the `policy-server` group comes from the Edge model card's
docker command. **This is a deliberate merge of two documents**, and it is necessary.

427 packages, ~25 GB. A correct install ends with, among others:

```
+ torch==2.10.0+cu130
+ transformer-engine==2.12+cu130.torch210
+ flash-attn==2.7.4.post1+cu130.torch210
+ loguru==0.7.3
+ openpi-server==0.1.0
+ cosmos-framework==1.2.2 (from file:///workspace/cosmos-framework)
```

### Verify — do not skip

```bash
hash -r
/workspace/cosmos-framework/.venv/bin/python -c \
  "import sys, torch, loguru; print(sys.prefix, sys.version.split()[0], torch.__version__)"
```

Must print exactly:

```
/workspace/cosmos-framework/.venv 3.13.14 2.10.0+cu130
```

If `sys.prefix` says `/workspace/isaaclab/_isaac_sim/kit/python` or torch says `2.7.0+cu128`,
you are running Isaac Sim's interpreter — see §9.1. **The install is not the problem.**

---

## 4. Hugging Face auth

```bash
/workspace/cosmos-framework/.venv/bin/hf auth login
```

Use the interactive login, not `export HF_TOKEN=hf_...` — an inline export lands in shell
history and in any log you paste.

Two separate repos, two separate approvals, both needed:

| repo | why |
|---|---|
| `nvidia/Cosmos3-Edge-Policy-DROID` | the policy |
| `nvidia/Cosmos-Guardrail1` | pulled unconditionally at startup (§9.3) |

---

## 5. Start the server — terminal 1

```bash
cd /workspace/cosmos-framework
export LD_LIBRARY_PATH=
export HF_HOME=/workspace/.cache/huggingface
export HF_HUB_DISABLE_XET=1

/workspace/cosmos-framework/.venv/bin/python \
  -m cosmos_framework.scripts.action_policy_server_robolab \
  --checkpoint_path nvidia/Cosmos3-Edge-Policy-DROID \
  --port 8000 \
  --format-prompt-as-json True
```

Three non-obvious pieces:

- **`export LD_LIBRARY_PATH=`** — blank, not a typo. cosmos-framework's install docs require
  it, and it matters doubly here: the isaac-lab image points `LD_LIBRARY_PATH` at Isaac Sim's
  bundled libraries, which would shadow the CUDA libs this torch expects.
- **`HF_HUB_DISABLE_XET=1`** — works around a live hf-xet bug (§9.4). Without it the
  guardrail download dies on `Unable to parse string as hex hash value`.
- **`--checkpoint_path` and `--format-prompt-as-json True`** — the script's default is
  **Nano** (`_DEFAULT_DROID_POLICY_CHECKPOINT` at `action_policy_server_robolab.py:65`), and
  the JSON prompt flag is Edge-specific. `policies/cosmos3/README.md` documents Nano and
  omits it — don't copy from there.

First launch downloads ~8 GB. **Leave this terminal running.**

### Known-good startup line

```
[robolab-policy-server] ready domain='droid_lerobot' resolution='480' action_space=joint_pos
action_dim=8 chunk=32 history=1 use_state=True image=540x640 fps=15.0 guidance=3.0
num_steps=4 shift=5.0 seed=0 deterministic_seed=False
[robolab-policy-server] Server accessible at: ws://172.17.0.2:8000/
[robolab-policy-server] Health check: http://172.17.0.2:8000/healthz
INFO:websockets.server:server listening on 0.0.0.0:8000
```

Diff any future run against this. `chunk=32` and `fps=15.0` are the two to check — they must
match RoboLab's 15 Hz env and the client's `OPEN_LOOP_HORIZON = 32`.

---

## 6. Run the task — terminal 2

A second SSH session, **stock environment**. Do not source the cosmos venv, do not unset
anything — Isaac Sim needs its own env intact.

```bash
cd /workspace/isaaclab/RoboLab
/workspace/isaaclab/_isaac_sim/python.sh policies/cosmos3/run.py \
  --task BananaInBowlTask --num-envs 1 --headless
```

Start at `--num-envs 1`. The README's `--num-envs 10` assumes the policy server is on a
separate machine; here the 4B model and Isaac Sim share one GPU.

Output lands in `output/<timestamp>_cosmos3/`, same layout as the `run_empty` runs.

### This boots a different env than the smoke test

`policies/cosmos3/run.py:38` registers with `cameras=WRIST_LEFT_RIGHT_HEAD` — **four**
cameras, because `_extract_observation` needs `over_shoulder_left_camera`,
`over_shoulder_right_camera` and `wrist_cam`. The default `WRIST_LEFT` preset used by
`run_empty.py` has no right camera. So this registration has never been exercised before;
a `KeyError` on `over_shoulder_right_camera` would mean the preset didn't apply.

---

## 7. Server config worth knowing

From the startup line and `action_policy_server_robolab.py:65-68`:

| field | value | note |
|---|---|---|
| `chunk` | **32** | action chunk = one decision's worth of commitment |
| `fps` | 15.0 | conditioning fps; equals the RoboLab control rate |
| `action_dim` | 8 | 7 arm joints + 1 gripper |
| `action_space` | `joint_pos` | absolute joint position, **not** end-effector deltas |
| `history` | 1 | single frame of context |
| `use_state` | True | proprioception is fed in |
| `num_steps` | 4 | diffusion denoising steps |
| `guidance` | 3.0 | classifier-free guidance scale |
| `deterministic_seed` | **False** | repeated calls on the same observation return *different* samples |

The last two rows are the ones that matter for best-of-K. `deterministic_seed=False` is what
makes K>1 produce genuinely distinct candidates rather than K copies; `guidance` and
`num_steps` are the levers on how diverse those candidates are. **Verify diversity
empirically before trusting it** — a fixed seed silently collapsing K candidates into one is
a known trap.

`action_space=joint_pos` also matters: an executability score built on deltas needs a
different derivative chain than one built on absolute joint positions.

---

## 8. Condensed

```bash
# once, client side
/workspace/isaaclab/_isaac_sim/python.sh -m pip install --no-cache-dir --no-deps \
  "openpi-client @ git+https://github.com/xuningy/openpi@aa6420561529593114160d05e5ad155792b272f3#subdirectory=packages/openpi-client"

# once, server side
apt-get update && apt-get install -y --no-install-recommends curl ffmpeg git-lfs libx11-dev tree wget
curl -LsSf https://astral.sh/uv/install.sh | sh && source $HOME/.local/bin/env
cd /workspace && git clone https://github.com/NVIDIA/cosmos-framework.git && cd cosmos-framework
uv sync --all-extras --group=cu130-train --group=policy-server
/workspace/cosmos-framework/.venv/bin/hf auth login
hash -r

# terminal 1 — server
cd /workspace/cosmos-framework
export LD_LIBRARY_PATH= HF_HOME=/workspace/.cache/huggingface HF_HUB_DISABLE_XET=1
/workspace/cosmos-framework/.venv/bin/python -m cosmos_framework.scripts.action_policy_server_robolab \
  --checkpoint_path nvidia/Cosmos3-Edge-Policy-DROID --port 8000 --format-prompt-as-json True

# terminal 2 — client
cd /workspace/isaaclab/RoboLab
/workspace/isaaclab/_isaac_sim/python.sh policies/cosmos3/run.py \
  --task BananaInBowlTask --num-envs 1 --headless
```

---

## 9. Dead ends — do not repeat these

### 9.1 `sys.prefix` points at Isaac Sim — bash's command hash

Symptom: `which python` says `.venv/bin/python`, but `python -V` reports 3.11.13,
`sys.prefix` is `/workspace/isaaclab/_isaac_sim/kit/python`, and torch is `2.7.0+cu128`.

Cause: **bash caches resolved command paths.** `python` was resolved once to Isaac Sim's
interpreter and stayed pinned there. Every `source .venv/bin/activate` after that changed
`PATH` and changed nothing about which binary ran.

Fix: `hash -r`, then use absolute interpreter paths forever (§0).

**Things that looked like the cause and were not:** `PYTHONHOME` / `PYTHONPATH` (unsetting
them changed nothing), a broken `uv sync` (it had installed all 427 packages correctly),
and the venv's base interpreter (rebuilding on uv's own CPython didn't help while the hash
was still stale).

### 9.2 Creating the venv with `uv venv --python 3.11` first

Pointless. `uv sync` deletes it and rebuilds with its own managed CPython. Just run `uv sync`.

### 9.3 `--guardrails False`

Not a valid flag. `GuardrailOverrides.guardrails` exists in
`cosmos_framework/inference/common/args.py:754`, but `main()` builds its CLI from
`RobolabServerArgs` (`action_policy_server_robolab.py:299`), which never exposes it.
Guardrails cannot be turned off from the command line — `Cosmos-Guardrail1` **will** be
downloaded, so get access to it.

### 9.4 `Unable to parse string as hex hash value`

A bug in hf-xet, HF's chunked transfer backend
([xet-core#895](https://github.com/huggingface/xet-core/issues/895)), not an auth problem.
Fixed by `HF_HUB_DISABLE_XET=1`, which falls back to plain HTTP.

Distinguish it from the real auth error, which reads `Access denied. This repository
requires approval.` — different message, different fix (request access).

If a failed attempt left partial blobs:
```bash
rm -rf /workspace/.cache/huggingface/hub/models--nvidia--Cosmos-Guardrail1
```

### 9.5 The documented Docker path

`policies/cosmos3/README.md` and the model card both use `docker build` + `docker run`.
Vast.ai containers have no nested Docker (`docker info` fails), so the native `uv` path
above is the only option here.
