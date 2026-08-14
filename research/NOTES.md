# Research Notes

Use this for concise cross-experiment observations that are worth remembering but do not belong in `STATE.md`.

Do not paste raw logs here.

## Frozen production IDM decision (2026-08-13)

- Train a direct point-estimate inverse dynamics model on DROID only. Cosmos is not part of IDM training; it appears later when WISE scores generated candidate video/action pairs.
- Input is exactly three RGB views and 33 consecutive frames. Do not supply initial robot state, proprioception, language, task text, success/failure, lab identity, or candidate actions to the model.
- Predict 32 aligned absolute joint-position commands plus a binary executed gripper target. There is no learned action encoder, compatibility verifier, query decoder, temporal subsampling, frame deletion, or idle filtering.
- Use the sole fixed 1K scene-disjoint validation manifest. There is no extra test split or mandatory two-view/fusion pilot.
- The complete architecture, data quotas, alignment, preprocessing, and score formula live in `research/IDM_DESIGN.md`; do not re-derive them from the legacy RUN_0007-RUN_0019 configurations.

## M6 fusion design (lower priority, revisit at M6, flagged 2026-08-12)

User flagged: the naive fixed-weight linear combination in `METHOD.md`
(`R_WISE = w_exec*z_exec + w_cons*z_cons + w_task*z_task`) is a starting
point, not necessarily the best way to combine the three WISE terms
(`r_exec`, `r_cons`, `r_task`). Worth exploring alternatives at M6 before
locking in fixed weights: learned/tuned weights, rank-based fusion instead
of raw z-scores, or treating `r_exec` more as a soft gate/filter than a
linearly-additive term (it measures validity, which arguably shouldn't
trade off linearly against task progress the same way `r_cons`/`r_task`
trade off against each other). Not urgent -- current single-term (M3) and
production IDM (M4/M5) work is unaffected either way.
