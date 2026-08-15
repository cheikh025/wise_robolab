# cosmos-framework patch: expose raw vision latent

`cosmos-framework` is NVIDIA's own upstream repo
(github.com/nvidia/cosmos-framework) -- not something this project can push
to directly, so this local change is archived here on its own branch instead
of living only in an uncommitted working-tree edit.

## What it does

`action_policy_server_robolab.py`'s `RobolabPolicyService.infer()` already
computes the raw pre-decode vision latent internally
(`samples["vision"][0]`) when `--decode-video` is set, but only ever used it
to render the decoded RGB video -- never returned it. The patch adds
`outputs["vision_latent"]` alongside the existing `outputs["video"]`, gated
on the same flag.

## Why

`research/tools/consensus_baseline.py`'s Consistency-Consensus baseline
(arXiv:2605.07514) needs each candidate's predicted-future latent to build
the consensus and score agreement. Without this patch, the only option would
be decoding to RGB and re-encoding with a separate VAE -- wasteful and a
worse match to the paper's "VAE latent space" method. This uses the model's
own native latent directly instead.

## Provenance

- upstream repo: https://github.com/nvidia/cosmos-framework
- patched against commit: `18d90eacbda778e666e6978dc1ab6ba8635400e3`
  ("Release 2026-08-14 (i4 8229ae3d) (#198)")
- patched file: `cosmos_framework/scripts/action_policy_server_robolab.py`
- apply with: `git apply vision_latent.patch` from the repo root at that commit
