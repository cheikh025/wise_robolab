# Run reproduction records

Create one `RUN_XXXX_<slug>.md` **before every non-trivial execution** and complete it immediately afterward.

This applies to:
- setup/install validation;
- RoboLab smoke runs;
- Cosmos B=1 / decoded-dream / diversity checks;
- Robometer offline scoring;
- Best-of-K;
- DROID IDM data checks, training, and validation;
- WISE integration/evaluation;
- diagnostics and failed reproductions.

Validation runs can and should be small. A one-task/one-episode smoke still gets a run record.

Use `RUN_TEMPLATE.md`. Never delete a failed run record; failure history is part of reproducibility.
