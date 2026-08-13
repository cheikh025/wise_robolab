# WISE Method Contract for this Project

At RoboLab control decision `t`, let the frozen Cosmos WAM receive current observation/state/instruction `h_t` and sample K native candidates:

`c_t^(i) = (xhat^(i), a^(i))`.

Each candidate must remain a coupled pair. WISE scores candidate `i` with three signals.

## 1. Action suitability: r_exec

Use known DROID/RoboLab action-interface validity plus temporal regularity.

For Cosmos joint-position control, derivatives must be interpreted from **absolute joint-position commands** at the verified control rate. Do not copy velocity-action interpretations from a different embodiment.

Include gripper-specific handling and the boundary from the previously executed action/chunk where meaningful.

Explicit non-finite or hard-invalid candidates may be rejected before fusion.

## 2. World-action consistency: r_cons

Run the independent IDM on current observation/proprioception + the candidate's imagined future:

`atilde^(i) = g_phi(o_t, p_t, xhat^(i))`.

Compare `atilde^(i)` with Cosmos's co-generated `a^(i)` in a normalized action space. Treat the gripper separately if its executed representation is discrete/thresholded.

This measures **internal cross-output coherence**, not whether the imagined future will match reality.

## 3. Task progress: r_task

Use general Robometer-4B on the candidate imagined trajectory with the exact environment instruction.

Robometer provides selector evidence. RoboLab state predicates remain the ground-truth evaluation outcome.

The initial scalarization of Robometer progress must be explicit. If using endpoint advancement, record exactly whether it is `u_end`, `u_end-u_start`, or another aggregation. Keep raw per-frame predictions when practical.

## Calibration and fusion

Raw scores have different scales. Define candidate-relative calibration explicitly before fusion, e.g. robust/z-score/rank based. The choice is an experiment variable until fixed by evidence.

`R_WISE = w_exec z_exec + w_cons z_cons + w_task z_task`.

Store raw and calibrated values so failures can be diagnosed after the episode.

## Receding horizon

Select one candidate, execute a fixed action prefix, re-observe RoboLab, then resample. The initial reproduction may execute the native full Cosmos chunk if that matches the baseline; shorter prefixes are later experimental variables.
