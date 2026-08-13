# Research Notes

Use this for concise cross-experiment observations that are worth remembering but do not belong in `STATE.md`.

Do not paste raw logs here.

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
soon-to-be-built IDM (M4/M5) work is unaffected either way.
