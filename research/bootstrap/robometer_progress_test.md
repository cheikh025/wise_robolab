# Robometer progress test on Cosmos3-Edge dreams

**Status: not yet executed.** Every command here is derived from Robometer's own
source (paths cited inline) and from the verified Cosmos3 runbook, but nothing in
this file has been run end to end. Mark steps as you confirm them.

Markers used below: **[S]** read from Robometer source · **[M]** measured on our box
in an earlier session · **[?]** expected, unconfirmed.

---

## 0. What this test is

Two questions, nothing else:

1. **Is Robometer installed and running correctly?**
2. **Can it predict sensible progress on our data?**

Explicitly *not* in scope: best-of-K, candidate selection, any coupling into the
policy loop. This is **offline, post-hoc scoring of saved mp4s**. The policy server
and the sim never talk to Robometer. That keeps the failure surface small — if
something breaks, it broke in one place.

**Input decision: one camera per Robometer call. The three views are scored
separately, never composited.** Robometer takes exactly one camera per sample —
their own DROID deployment sends `server.image_keys='["observation/exterior_image_1_left"]'`
(`robometer-policy-learning/docs/REAL_ROBOT_README.md`), a single left exterior.
We test all three of ours independently rather than assume which one carries the
signal. No rescaling: each panel goes in at its native size.

---

## 1. Why Robometer needs its own environment

The box will now carry **three** Python environments. They cannot be merged.

| env | interpreter | Python | torch | runs |
|---|---|---|---|---|
| Isaac | `/workspace/isaaclab/_isaac_sim/python.sh` | 3.11.13 | 2.7.0+cu128 | RoboLab, sim |
| cosmos | `/workspace/cosmos-framework/.venv/bin/python` | 3.13.14 | 2.10.0+cu130 | policy server |
| **robometer** | `/workspace/robometer/.venv/bin/python` | **3.10** | **2.8.0+cu128** | scoring |

Robometer pins `requires-python = "==3.10.*"` and `torch==2.8.0` (cu128 index) in
`pyproject.toml:10,62,159-166` **[S]**. Both conflict with both existing envs. Do not
try to install it into either one.

**The absolute-path rule from the Cosmos3 runbook applies here too.** Never rely on
`python` resolving correctly — bash caches the resolution and it silently ran the
wrong interpreter for an hour once. Always type the full path, and `hash -r` after
any activate.

---

## 2. Install

```bash
cd /workspace
git clone https://github.com/robometer/robometer.git
cd robometer
uv sync --extra robometer
```

`--extra robometer` pulls `transformers>=4.57` and `trl==0.20.0`
(`pyproject.toml:104-107` **[S]**). The `vlac` extra is declared as conflicting
(`pyproject.toml:140-145`) — never pass both.

**Do not pre-create the venv.** `uv sync` deletes any existing `.venv` and rebuilds
it on its own interpreter. A `uv venv --python 3.10` beforehand is wasted work.

**Do not improvise shim packages or hand-install `unsloth`.** Run the repo's own
install and nothing else. Deviating from a working install path is exactly what
broke this last time.

This is a heavy sync — the dependency list includes `tensorflow==2.19`,
`unsloth`, `xformers`, `robosuite`, `decord`, `metaworld`. Most is unused for
inference, but let it install rather than pruning by hand.

Verify the interpreter before anything else:

```bash
hash -r
/workspace/robometer/.venv/bin/python -c "import sys, torch; print(sys.version, torch.__version__, torch.cuda.is_available())"
```

Expect `3.10.x`, `2.8.0+cu128`, `True` **[?]**.

---

## 3. Checkpoint

`robometer/Robometer-4B` — public, ungated, Apache-2.0. **8.90 GB**, two shards,
4,450,286,861 params all BF16 **[M, from the HF API]**.

Authenticate properly — do **not** paste a token into the shell:

```bash
hf auth login
```

Pre-fetch so the first scoring run isn't also a download:

```bash
HF_HUB_DISABLE_XET=1 hf download robometer/Robometer-4B
```

`HF_HUB_DISABLE_XET=1` avoids the `Unable to parse string as hex hash value`
xet-core bug that bit us on the Cosmos3 checkpoint **[M]**.

---

## 4. Produce the run data

Nothing new here — this is the existing Cosmos3 flow with dreams enabled. Two
terminals.

**Terminal A — policy server.** Must include `--decode-video`, a bare switch with
no value:

```bash
cd /workspace/cosmos-framework
HF_HUB_DISABLE_XET=1 /workspace/cosmos-framework/.venv/bin/python \
  cosmos_framework/scripts/action_policy_server_robolab.py \
  --policy-checkpoint nvidia/Cosmos3-Edge-Policy-DROID \
  --decode-video
```

Wait for the ready line before starting B.

**Terminal B — one task, one env.**

```bash
cd /workspace/RoboLab
/workspace/isaaclab/_isaac_sim/python.sh policies/cosmos3/run.py \
  --task BananaInBowlTask --num-envs 1 --headless
```

This requires the patched `policies/cosmos3/client.py` (the `_save_dream` /
`_cur_env_id` edits). Without it the server sends video and the client throws it
away.

Afterwards you should have, under the run's output dir:

- `dreams/dream_env0_call000.mp4` … — each `(33, 528, 640, 3)` **[M]**
- the sensor video, `2560x360` = `head | left | right | wrist` **[M]**
- `events` / metrics JSON — needed in §7 to know *when* the grasp and release happened

---

## 5. The scoring script

Save as `/workspace/score_dreams.py`. Runs in the robometer env only.

```python
"""Score Cosmos3 dreams (and the matching real frames) with Robometer.

One camera per call, three views scored separately, no rescaling.
Prints per-frame progress for each view.
"""
import argparse, glob, json, os
import cv2
import numpy as np
import torch

from robometer.utils.save import load_model_from_hf
from robometer.utils.setup_utils import setup_batch_collator
from robometer.evals.eval_server import process_batch_helper
from robometer.evals.eval_utils import raw_dict_to_sample

CHUNK = 32  # env steps per policy call


def read_video(path):
    cap = cv2.VideoCapture(path)
    frames = []
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    cap.release()
    return np.asarray(frames, dtype=np.uint8)


def detect_seam(frame):
    """Row of the wrist / exterior boundary, found by max row-to-row change."""
    g = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(np.float32)
    d = np.abs(np.diff(g, axis=0)).mean(axis=1)
    lo, hi = int(len(d) * 0.55), int(len(d) * 0.78)
    return lo + int(d[lo:hi].argmax())


def split_dream(dream):
    """(T, 528, 640, 3) -> {'wrist','left','right'}, each (T, h, w, 3).

    The client stacks wrist (360 of 540 rows) over [left|right], so wrist owns
    the top 2/3. The dream comes back 528 rather than 540 and we have never
    measured where the 12 rows are lost -- so derive the seam by ratio, then
    check it against the detected edge and shout if they disagree.
    """
    h, w = dream.shape[1:3]
    seam = round(h * 2 / 3)
    found = detect_seam(dream[0])
    if abs(found - seam) > 4:
        print(f"  !! seam mismatch: ratio says {seam}, image says {found}. Using {found}.")
        seam = found
    else:
        print(f"  seam row {seam} (detected {found})")
    return {"wrist": dream[:, :seam],
            "left":  dream[:, seam:, : w // 2],
            "right": dream[:, seam:, w // 2:]}


def split_sensor(sensor, start, n):
    """2560x360 sensor video -> the same three cameras at native 360x640.

    Panels are head | left | right | wrist at 640 px each. head is rendered by
    the sim but never sent to the policy, so it is skipped.
    """
    clip = sensor[start:start + n]
    return {"wrist": clip[:, :, 1920:2560],
            "left":  clip[:, :, 640:1280],
            "right": clip[:, :, 1280:1920]}


def load_robometer(path, device):
    dev = torch.device(device)
    exp_config, tokenizer, processor, model = load_model_from_hf(model_path=path, device=dev)
    model.eval()
    collator = setup_batch_collator(processor, tokenizer, exp_config, is_eval=True)
    loss_cfg = getattr(exp_config, "loss", None)
    return {
        "model": model, "tokenizer": tokenizer, "collator": collator, "device": dev,
        "is_discrete": getattr(loss_cfg, "progress_loss_type", "l2").lower() == "discrete",
        "num_bins": getattr(loss_cfg, "progress_discrete_bins", None)
                    or getattr(exp_config.model, "progress_discrete_bins", 10),
        "max_frames": int(getattr(getattr(exp_config, "data", None), "max_frames", 8)),
        "model_type": exp_config.model.model_type,
    }


def score(rm, frames, task):
    """One clip -> (per_frame_progress, last_frame_progress)."""
    raw = {"frames": np.ascontiguousarray(frames), "task": task, "id": "0",
           "metadata": {"subsequence_length": int(frames.shape[0])},
           "video_embeddings": None, "text_embedding": None}
    s = raw_dict_to_sample(raw_data=raw, max_frames=rm["max_frames"], sample_type="progress")
    # autocast is required, not optional -- see upstream issue #38, reported on
    # this exact GPU (RTX PRO 6000 Blackwell) and this exact torch (2.8.0+cu128):
    # "RuntimeError: expected scalar type BFloat16 but found Float".
    with torch.autocast("cuda", dtype=torch.bfloat16):
        out = process_batch_helper(
            model_type=rm["model_type"], model=rm["model"], tokenizer=rm["tokenizer"],
            batch_collator=rm["collator"], device=rm["device"],
            batch_data=[s.model_dump()], job_id=0,
            is_discrete_mode=rm["is_discrete"], num_bins=rm["num_bins"],
            use_frame_steps=False,
        )
    # progress_pred[i] is the PER-FRAME list; extract_rewards_from_output keeps
    # only [-1] (eval_utils.py:39-48). We want the whole curve.
    per_frame = [float(x) for x in out["outputs_progress"]["progress_pred"][0]]
    return per_frame, max(0.0, min(1.0, per_frame[-1]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-dir", required=True)
    p.add_argument("--sensor-video", required=True)
    p.add_argument("--task", required=True, help="verbatim env instruction")
    p.add_argument("--model-path", default="robometer/Robometer-4B")
    p.add_argument("--device", default="cuda")
    a = p.parse_args()

    rm = load_robometer(a.model_path, a.device)
    print(f"loaded: max_frames={rm['max_frames']} bins={rm['num_bins']} "
          f"discrete={rm['is_discrete']} model_type={rm['model_type']}")

    sensor = read_video(a.sensor_video)
    print(f"sensor video: {sensor.shape}")

    rows = []
    for path in sorted(glob.glob(os.path.join(a.run_dir, "dreams", "dream_env0_call*.mp4"))):
        k = int(path.split("call")[-1].split(".")[0])
        dream = read_video(path)
        print(f"call {k:03d}  dream {dream.shape}")

        dream_views = split_dream(dream)
        real_views = split_sensor(sensor, k * CHUNK, len(dream))
        if len(real_views["wrist"]) == 0:
            # Episode ended inside this chunk -- no real frames left to compare.
            print("    (no real frames for this call, skipping)")
            continue

        row = {"call": k}
        for v in ("wrist", "left", "right"):
            dv, rv = dream_views[v], real_views[v]
            d_curve, d_last = score(rm, dv, a.task)
            r_curve, r_last = score(rm, rv, a.task)
            print(f"    {v:<5} dream {dv.shape[1]}x{dv.shape[2]} last={d_last:.3f} | "
                  f"real {rv.shape[1]}x{rv.shape[2]} last={r_last:.3f}")
            print(f"          dream {[round(x, 3) for x in d_curve]}")
            print(f"          real  {[round(x, 3) for x in r_curve]}")
            row[v] = {"dream_last": d_last, "real_last": r_last,
                      "dream_curve": d_curve, "real_curve": r_curve}
        rows.append(row)

    with open(os.path.join(a.run_dir, "robometer_progress.json"), "w") as f:
        json.dump(rows, f, indent=2)


if __name__ == "__main__":
    main()
```

Run it:

```bash
hash -r
/workspace/robometer/.venv/bin/python /workspace/score_dreams.py \
  --run-dir  /workspace/RoboLab/outputs/<timestamp>_cosmos3 \
  --sensor-video /workspace/RoboLab/outputs/<timestamp>_cosmos3/<sensor>.mp4 \
  --task "put the banana in the bowl"
```

The task string must be the **verbatim** instruction the env used — it goes straight
into Robometer's prompt template. A paraphrase is a different input.

---

## 6. What the code actually does with our frames

Worth knowing so the output isn't a black box. All **[S]**.

- `raw_dict_to_sample` requires `(T, H, W, C)` and errors on anything else
  (`evals/eval_utils.py:114-115`). Each cropped view is `(33, h, w, 3)`.
- It calls `linspace_subsample_frames(frames, 8)`, whose docstring says **"The first
  and last frames are always included"** (`data/datasets/helpers.py:283`). So 33 -> 8.
- **No resize happens anywhere in the inference path.** `resized_height` and
  `resized_width` are `null` in the checkpoint config, and the collator passes them
  straight through (`utils/setup_utils.py:1395-1396`). Each panel reaches Qwen3-VL's
  processor at its native size. This is why "no rescaling" is achievable — it is the
  default.
- Each frame becomes its own image entry followed by `<|prog_token|>`
  (`data/collators/rbm_heads.py:229-239`). `use_multi_image` means *frames as
  images*, not cameras. There is no camera axis in the input at all.
- The prompt is fixed (`data/collators/rbm_heads.py:378`):

  > The task for the robot is '{task}'. Given the trajectory video, predict the task
  > progress at each frame, how far along the robot is towards completing the task, a
  > float between 0 and 1, where 0 is the starting state and 1 is when the task is
  > completed. **If the robot is not performing the same task, predict 0 progress.**

- Progress is discrete: 10 bin logits -> softmax -> expectation over bin centers.

---

## 7. Reading the result

Six numbers per call: three views x {dream, real}.

The trailing prompt clause above is trained behaviour — the model has a learned escape
to emit **0** when the video does not read as the task. So a rejected input comes back
as flat zero, not as noise. That makes the outcomes separable:

| observation | conclusion |
|---|---|
| exception, NaN, shape error | install or wiring — **goal 1 failed** |
| all six flat ~0 | goal 1 passed, but nothing is landing — suspect the task string or the prompt path before blaming the views |
| real rises on some view, dream flat on the same view | that view works; the **dream** is what fails there |
| a view rises on both dream and real, toward 1.0 near the container event | **both goals passed for that view** — use it |
| flat non-zero, no trend | reading something, but not progress |

**Judge against the event log**, which gives the exact step of the grasp and of
`OBJECT_IN_CONTAINER_SUCCESS`. On a success, progress should climb and approach 1.0
around that step. `TARGET_OBJECT_DROPPED` can fire *on* success — it is the release
into the bowl, not a fumble **[M]**.

### Sizes going in, and the one confound

| view | dream panel | real panel | Robometer trained at |
|---|---|---|---|
| wrist | 352x640 | 360x640 | shortest edge 240 (224 in their online DROID config) |
| left | 176x320 | 360x640 | same |
| right | 176x320 | 360x640 | same |

**Wrist is the clean dream-vs-real comparison** — 352 against 360, near-matched, so a
gap there is the dream and nothing else. **The exteriors are confounded**: 176 vs 360
mixes "the dream is worse" with "the panel is smaller." If an exterior shows a big
dream-vs-real gap, that is not yet evidence about dreaming.

Both exteriors sit *below* the 240 Robometer was trained on; wrist sits above it.

### Which view we expect to win, and why that is not a prediction

Their DROID deployment sends **one left exterior**
(`server.image_keys='["observation/exterior_image_1_left"]'`), and their OXE spec lists
DROID `primary: exterior_image_1_left` (`oxe_helper.py:567-572`). The paper: *"For most
other datasets, we only use external cameras unless wrist is the only viewpoint
available."*

So external is their default. But our external panels are the small ones, and DROID
wrist was specifically included in RBM-1M *"due to the wide-angle of the DROID wrist
cameras."* That is why we measure all three instead of picking.

**Why never the composite.** RBM-1M contains zero tiled frames — every loader iterates
views and emits each as a separate trajectory
(`dataset_upload/dataset_loaders/failsafe_loader.py:148,162-176`), and
`generate_hf_dataset.py:859-864` hard-errors if a dataset does not declare exactly one
view **[S]**. A stacked three-camera canvas is a kind of image the model has never
seen, and sending it would also give us no way to tell which view carried the signal.
One camera per call is both in-distribution and attributable.

---

## 8. Traps

| trap | reality |
|---|---|
| `python` resolves to the wrong interpreter | bash caches it. `hash -r`, then absolute paths. Cost us an hour once. |
| pre-creating the venv | `uv sync` deletes and rebuilds it |
| installing into the Isaac or cosmos env | Robometer needs 3.10 + torch 2.8.0; both existing envs conflict |
| `--decode-video True` | bare switch, no value — a value is rejected |
| hf-xet hex hash crash | `HF_HUB_DISABLE_XET=1` |
| `extract_rewards_from_output` | last frame only; read `outputs_progress["progress_pred"]` for the curve |
| paraphrasing the task string | it is the prompt; use the env's instruction verbatim |
| exporting `HF_TOKEN=` inline | lands in shell history and every pasted log. `hf auth login` |
| assuming the dream is 540 tall | it is **528** — the VAE rounds to a multiple of 16 **[M]** |
| hardcoding the seam row | the 12 lost rows have never been located. The script derives it by ratio and cross-checks against the detected edge — read that line of output before trusting any crop. |
| sending all three views in one image | never. One camera per call, or you cannot attribute the result **[S]** |
| `RuntimeError: expected scalar type BFloat16 but found Float` | upstream issue #38, reported on **our exact GPU and torch**. Wrap the call in `torch.autocast("cuda", dtype=torch.bfloat16)`. Already in the script above. |
| expecting fast inference | upstream issue #14: *"runs slower than VLAC-8B"*, >3x slower at half the params on an A800. Open since March 2026, **no maintainer reply**. |

---

## 9. Still open after this test

- Per-frame progress *within* a call is 8 points from a 33-frame dream. If the curve
  looks promising, `use_frame_steps=True` gives prefix-expanded denser curves at
  higher cost.
- No inference latency for Robometer is published anywhere, and upstream issue #14
  reports it as slow on an A800 with no maintainer reply — measure it here on our
  Blackwell, it sets what K is affordable.
- Where the dream loses its 12 rows. The script cross-checks but does not settle it;
  one look at a frame would.
- Whether an exterior panel upscaled to 240+ beats it at native 176. Deliberately not
  tested here — this run is no-rescale by design, and that comparison is only worth
  making if an exterior shows signal at all.
