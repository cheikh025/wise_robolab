# PROGRESS_0001 — M1 Cosmos3-Edge + RoboLab baseline

## Purpose

- associated run record(s): `research/runs/RUN_0001_cosmos_b1_smoke.md`, `RUN_0002_cosmos_diversity.md`, `RUN_0003_cosmos_dream_video.md`
- milestone: M1_COSMOS
- question/decision: is the frozen `nvidia/Cosmos3-Edge-Policy-DROID` checkpoint (not Nano) correctly integrated end-to-end through RoboLab's stock client — right observation/action wire format, right control rate/chunk size, genuine same-context candidate diversity, and retainable native rollout video — establishing a trustworthy B=1 baseline before Robometer/IDM/WISE work begins?
- parent implementation/baseline: M0 (RoboLab infra baseline, no policy)

## Exact code state

- repo: `https://github.com/cheikh025/RoboLab`
- branch: `wise/m0-setup`
- commit: `16513ca` (dream-video patch), preceded by `4ab19bf` (M0 uv.lock) and `1a4364a` (M0 video-writing patch)
- diff summary: `policies/cosmos3/client.py` +35 lines (dream-video retention); no changes to action/observation semantics or benchmark success predicates

## Environment

- system-info artifact: not separately captured (see RUNBOOK.md)
- interpreter(s): RoboLab `/workspace/RoboLab/.venv/bin/python` (3.11.15, torch 2.7.0+cu128); Cosmos `/workspace/cosmos-framework/.venv/bin/python` (3.13.13, torch 2.10.0+cu130) — two isolated envs, never crossed
- GPU/driver/CUDA: 2x A100-SXM4-80GB, driver 580.95.05, CUDA 13.0 (unchanged from M0)
- key package versions: cosmos-framework `a98dec05aa93ff6e2ebab2f38b590b86fe84f757`; `openpi-client==0.1.0` (git, pinned commit `aa6420561529593114160d05e5ad155792b272f3`, `--no-deps`)

## Configuration

- Cosmos checkpoint/revision: `nvidia/Cosmos3-Edge-Policy-DROID`, revision `main` (auxiliary: `nvidia/Cosmos-Guardrail1` @ `d6d4bfa899a71454a700907664f3e88f503950cf`, `Qwen/Qwen3Guard-Gen-0.6B`, `Wan-AI/Wan2.2-TI2V-5B` VAE @ `921dbaf3f1674a56f47e83fb80a34bac8a8f203e` — all pulled implicitly at server startup, not mentioned in prior bootstrap notes, now recorded)
- Robometer checkpoint/revision: n/a
- IDM checkpoint/config if applicable: n/a
- RoboLab task(s): `BananaInBowlTask`
- num envs / runs: 1 env; 3 separate episodes total across the 3 runs (RUN_0001, RUN_0003; RUN_0002 used 0 episodes, direct server calls)
- candidate budget K: 1 (B=1) for episodes; K=5 for the diversity check (no execution)
- action prefix: full 32-step chunk executed open-loop between replans (client's `OPEN_LOOP_HORIZON=32`)
- seeds/randomness: server `seed=0`, `deterministic_seed=False` (confirmed to matter — RUN_0002)
- score/calibration/fusion settings: n/a (no selector yet)

## Commands

See each RUN file for exact commands. Summary:

```bash
# server (once checkpoints cached, ~4min boot; cold start ~19min)
cd /workspace/cosmos-framework
export LD_LIBRARY_PATH= HF_HOME=/workspace/.hf_home HF_HUB_DISABLE_XET=1
/workspace/cosmos-framework/.venv/bin/python -m cosmos_framework.scripts.action_policy_server_robolab \
  --checkpoint-path nvidia/Cosmos3-Edge-Policy-DROID --port 8000 --format-prompt-as-json True --decode-video

# client
cd /workspace/RoboLab && source .venv/bin/activate && export OMNI_KIT_ACCEPT_EULA=Y
uv run python policies/cosmos3/run.py --task BananaInBowlTask --num-envs 1 --headless
```

## What happened

- runtime: server cold start ~19 min (checkpoint + 3 auxiliary model downloads dominate); episodes ~60-70s wall each; diversity check ~seconds
- peak VRAM when useful: not sampled
- failures/warnings: `openpi_client` missing from RoboLab's declared deps (fixed, `uv pip install --no-deps` with pinned commit — `pip` itself isn't present in the uv-managed venv, had to use `uv pip install`); one apparent stdout-buffering illusion of a stuck HF download lock (debug.log showed it wasn't actually stuck); otherwise clean
- output paths: `/workspace/RoboLab/output/2026-08-12_07-30-46_cosmos3/`, `/workspace/RoboLab/output/2026-08-12_07-37-11_cosmos3/`

## Evidence

### RoboLab outcome

- success: BananaInBowlTask succeeded on both executed episodes (RUN_0001: score=1.0, 155 steps; RUN_0003: score=1.0, 141 steps) — real Cosmos3-Edge policy behavior, not random actions
- task-level results: see RUN_0001/RUN_0003 for full metrics (SPARC, path length, joint RMSE, timing breakdown)

### Candidate/selector evidence

- candidate diversity: K=5 identical-context requests -> 5 distinct action chunks, pairwise L2 mean=2.057 (min=1.258, max=2.701), zero duplicate pairs (RUN_0002)
- raw `r_exec` / `r_cons` / `r_task`: n/a — no selector yet (M3/M5/M6)
- selected candidate behavior: n/a (B=1, no selection)

### Robometer evidence

- n/a for M1

### IDM evidence

- n/a for M1

## Decision

- `MILESTONE_PASS`
- reason: all M1 exit criteria met — Edge checkpoint verified loaded (not Nano) via the server's own ready-line config and prompt/response inspection; observation/state/action-space/control-rate/chunk-size/gripper-post-processing all verified from live behavior, matching bootstrap notes and current source; one normal episode runs end-to-end through the unmodified client semantics and succeeds; native rollout video is retained via a minimal, non-invasive patch with empirically-verified geometry; same-context diversity is real, not collapsed. B=1 baseline established (n=2 successful episodes; broader statistical confirmation deliberately deferred to M7 per CLAUDE.md's validation-budget discipline — a wide 95% CI at small n is expected and acceptable at this stage, not a defect).
- next action: M2 — `/validate-robometer-on-cosmos`. Use the dream videos already produced in RUN_0003 as one of the first offline scoring inputs.

## Reproducibility checklist

- [x] exact commit recorded
- [x] exact commands recorded
- [x] revisions/checkpoints recorded
- [x] output artifacts preserved
- [x] no benchmark semantics silently changed (video retention is additive/observational; action path untouched, verified by re-running the same task successfully after the patch)
