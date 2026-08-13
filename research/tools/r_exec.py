#!/usr/bin/env python3
"""WISE r_exec: action-suitability / temporal-regularity scoring (M6 prep).

Third of the three WISE signals (research/METHOD.md): action validity and
temporal regularity of a candidate's Cosmos-generated action chunk, computed
directly from absolute joint-position commands at the verified 15Hz control
rate (chunk=32, per M1's RUNBOOK) -- NOT from a velocity-action
interpretation, which would be wrong for a different embodiment/action
space. No model, no GPU: pure numeric validity check, usable standalone or
fused with r_cons (IDM) and r_task (Robometer) in M6.

Franka Emika Panda joint position/velocity limits verified directly against
the official datasheet (download.franka.de/Datasheet-EN.pdf, Release
04/2020), read in full after installing poppler-utils via the local
provisioner API (root-equivalent, no sudo password available on this box --
see research/RUNBOOK.md) on 2026-08-12. Matches exactly: position limits
A1,A3,A5,A7 +-166deg, A2 +-101deg, A4 -176/-4deg, A6 -1/215deg; velocity
limits A1-A4 150deg/s, A5-A7 180deg/s. The datasheet publishes no joint
acceleration/jerk figure -- JOINT_ACCEL_SOFT_MAX below is a heuristic, not a
spec. Cross-checked against nvidia/Cosmos3-DROID's own empirical
action.joint_position min/max (meta/stats.json) -- the DROID data stays
comfortably within these hardware bounds, as expected.
"""
from __future__ import annotations

import numpy as np

FPS = 15.0  # verified RoboLab/Cosmos3-Edge control rate (M1 RUNBOOK)

# Franka Emika Panda official joint position limits, radians: A1,A3,A5,A7:
# +-166 deg; A2: +-101 deg; A4: -176/-4 deg; A6: -1/215 deg.
JOINT_POS_MIN = np.array([-2.8973, -1.7628, -2.8973, -3.0718, -2.8973, -0.0175, -2.8973])
JOINT_POS_MAX = np.array([2.8973, 1.7628, 2.8973, -0.0698, 2.8973, 3.7525, 2.8973])

# Official joint velocity limits: A1-A4 150 deg/s, A5-A7 180 deg/s.
JOINT_VEL_MAX = np.array([2.6180, 2.6180, 2.6180, 2.6180, 3.1416, 3.1416, 3.1416])  # rad/s

# No official jerk/acceleration figure was confirmed from the source used;
# this is a soft heuristic bound only (large multiple of a "brisk but sane"
# accel), not a hardware spec -- flagged as a design variable to revisit.
JOINT_ACCEL_SOFT_MAX = 20.0  # rad/s^2, heuristic


def score_r_exec(action_chunk: np.ndarray, prev_last_action: np.ndarray | None = None) -> dict:
    """action_chunk: (T, 8) absolute joint-position (7) + gripper (1) commands
    at FPS Hz. prev_last_action: (8,) the previously executed chunk's final
    action, for boundary-continuity scoring (optional -- None for B=1/first
    decision of an episode).

    Returns raw sub-scores (each in [0,1], 1=fully valid/smooth) plus a
    combined scalar. Candidate-relative calibration/fusion weights are NOT
    applied here (per METHOD.md, that is an explicit, separate step in the
    selector) -- this returns the raw per-candidate signal only.

    No hard-reject path (by explicit user direction, 2026-08-12): every
    candidate gets a continuous soft score, including non-finite/extreme
    cases -- METHOD.md allows hard-rejection ("may be rejected") but does
    not require it, and for now candidates are ranked purely by this
    continuous signal rather than some being dropped outright. Non-finite
    entries are treated as a very large violation (not an early return) so
    they still flow through the same soft-decay formula and land near, but
    not discontinuously at, 0.
    """
    joints = action_chunk[:, :7].astype(np.float64)
    gripper = action_chunk[:, 7].astype(np.float64)

    non_finite_mask = ~np.isfinite(action_chunk)
    if non_finite_mask.any():
        # Substitute a large-but-finite placeholder so downstream arithmetic
        # stays well-defined; the violation math below will then naturally
        # score these entries near 0 without a special-cased branch.
        action_chunk = np.where(non_finite_mask, 1e6, action_chunk)
        joints = action_chunk[:, :7].astype(np.float64)
        gripper = action_chunk[:, 7].astype(np.float64)

    # 1. Joint-limit respect. Averaging a per-(timestep,joint) soft score
    # across all 32*7 entries would let one severe single-frame spike (e.g.
    # a corrupted generation) get diluted to near-invisibility (empirically
    # found via this module's own smoke test: a single joint driven to 100
    # rad only moved a mean-based score by ~0.004). Use the WORST violation,
    # not the average, so a single bad frame still meaningfully drags the
    # score down -- but always continuous, never an early return/hard 0.
    margin = 0.05  # rad, small tolerance for measurement/generation noise
    below = np.clip((JOINT_POS_MIN - margin) - joints, 0, None)
    above = np.clip(joints - (JOINT_POS_MAX + margin), 0, None)
    violation = below + above  # (T,7), 0 where in-range
    max_joint_violation = float(violation.max())
    joint_limit_score = float(np.exp(-max_joint_violation / 0.2))

    # 2. Temporal smoothness: velocity from ABSOLUTE joint-position deltas at
    # the verified control rate (not a velocity-action interpretation).
    # Same worst-case-not-mean reasoning as above, still fully continuous.
    vel = np.diff(joints, axis=0) * FPS  # (T-1, 7), rad/s
    vel_violation = np.clip(np.abs(vel) - JOINT_VEL_MAX, 0, None)
    max_vel_violation = float(vel_violation.max())
    vel_score = float(np.exp(-max_vel_violation / 0.5))

    accel = np.diff(vel, axis=0) * FPS  # (T-2, 7), rad/s^2
    accel_violation = np.clip(np.abs(accel) - JOINT_ACCEL_SOFT_MAX, 0, None)
    accel_score = float(np.exp(-float(accel_violation.max()) / 5.0))
    smoothness_score = float(0.6 * vel_score + 0.4 * accel_score)

    # 3. Gripper: range validity only (execution thresholds it; smoothness
    # is not meaningful for a channel that legitimately snaps open/closed).
    gripper_score = float(np.mean((gripper >= -0.02) & (gripper <= 1.02)))

    # 4. Boundary continuity with the previously executed action, if given.
    if prev_last_action is not None:
        jump = np.abs(joints[0] - prev_last_action[:7].astype(np.float64))
        boundary_score = float(np.mean(np.exp(-jump / 0.3)))
    else:
        boundary_score = 1.0  # first decision of an episode: nothing to compare against

    r_exec = float(np.mean([joint_limit_score, smoothness_score, gripper_score, boundary_score]))

    return {
        "r_exec": r_exec,
        "joint_limit_score": joint_limit_score,
        "smoothness_score": smoothness_score,
        "gripper_score": gripper_score,
        "boundary_score": boundary_score,
    }


if __name__ == "__main__":
    # Minimal smoke test: a clean chunk should score near 1.0; an injected
    # discontinuity/out-of-range chunk should score visibly lower.
    rng = np.random.default_rng(0)
    t = np.linspace(0, 1, 32)
    joint_center = (JOINT_POS_MIN + JOINT_POS_MAX) / 2  # respect each joint's own (possibly asymmetric) range, e.g. A4
    joint_amp = (JOINT_POS_MAX - JOINT_POS_MIN) / 2 * 0.1
    clean = np.stack([joint_center[i] + joint_amp[i] * np.sin(2 * np.pi * t + i) for i in range(7)], axis=1)
    clean = np.concatenate([clean, (t > 0.5).astype(np.float64)[:, None]], axis=1)
    print("clean chunk:", score_r_exec(clean))

    broken = clean.copy()
    broken[10, 3] = 100.0       # wild out-of-range spike
    broken[20, 0] = np.nan      # non-finite
    print("broken chunk (nan):", score_r_exec(broken))

    broken2 = clean.copy()
    broken2[10, 3] = 100.0
    print("broken chunk (out-of-range+jerky):", score_r_exec(broken2))
