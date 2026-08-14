# WISE Method Contract for this Project

At RoboLab control decision `t`, let the frozen Cosmos WAM receive current observation/state/instruction `h_t` and sample `K` native candidates:

`c_t^(i) = (xhat^(i), a^(i))`.

Each imagined future `xhat^(i)` must remain paired with its co-generated action chunk `a^(i)` through scoring and selection. WISE scores candidate `i` with three independent signals.

## 1. Action suitability: r_exec

Use known DROID/RoboLab action-interface validity plus temporal regularity.

For Cosmos joint-position control, derivatives must be interpreted from absolute joint-position commands at the verified 15 Hz control rate. Do not copy velocity-action interpretations from a different embodiment. Handle the binary gripper separately using the external convention `0 = open`, `1 = closed`.

Include the boundary from the previously executed action/chunk where meaningful. Explicit non-finite or hard-invalid candidates may be rejected before score fusion.

## 2. World-action consistency: r_cons

Run the independent, frozen IDM on the candidate's complete three-view imagined video only:

`atilde^(i) = g_phi(xhat^(i))`.

The IDM receives no initial robot state, proprioception, language, task, success/failure, or lab identity. It was trained only on pinned DROID data; Cosmos dreams were not used in IDM training. Its production input is 33 frames and its output is the aligned 32 x 8 absolute joint-position plus binary-gripper action chunk specified in `research/IDM_DESIGN.md`.

For joint dimensions `j = 1..7`, use the training-set standard deviations `sigma_j`:

`E_joint^(i) = mean_{t,j} |(atilde[t,j] - a[t,j]) / sigma_j|`

`S_joint^(i) = exp(-E_joint^(i))`

Threshold both gripper sequences at `> 0.5`, then compute:

`S_gripper^(i) = mean_t 1[atilde[t,8] = a[t,8]]`

The raw consistency score is:

`r_cons^(i) = 0.5 * S_joint^(i) + 0.5 * S_gripper^(i)`.

This is a direct deterministic action reconstruction comparison. There is no learned video-action verifier or auxiliary action encoder. It measures internal cross-output coherence, not whether the imagined future will match reality.

Dream decoding is fixed at `33 x 528 x 640 x 3`: wrist above row 360, exterior 1 below-left, and exterior 2 below-right. Validate that geometry rather than inferring a seam.

## 3. Task progress: r_task

Use general Robometer-4B on the candidate imagined trajectory with the exact environment instruction.

Robometer provides selector evidence. RoboLab state predicates remain the ground-truth evaluation outcome.

The scalarization of Robometer progress must be explicit. If using endpoint advancement, record exactly whether it is `u_end`, `u_end-u_start`, or another aggregation. Keep raw per-frame predictions when practical.

## Calibration and fusion

Raw scores have different scales. Define candidate-relative calibration explicitly before fusion, for example robust, z-score, or rank calibration. The choice remains an experiment variable until fixed by evidence.

`R_WISE = w_exec z_exec + w_cons z_cons + w_task z_task`.

Store raw and calibrated values so failures can be diagnosed after the episode.

## Receding horizon

Select one complete candidate, execute a fixed action prefix, re-observe RoboLab, then resample. The initial reproduction may execute the native full Cosmos chunk if that matches the baseline; shorter prefixes are later experimental variables.
