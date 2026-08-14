# Primary sources to re-check during the project

The agent should prefer current official/primary sources and pin exact revisions in `research/RUNBOOK.md`.

- User fork: https://github.com/cheikh025/RoboLab
- RoboLab upstream: https://github.com/NVlabs/RoboLab
- RoboLab Cosmos3 client: https://github.com/NVlabs/RoboLab/tree/main/policies/cosmos3
- NVIDIA cosmos-framework: https://github.com/NVIDIA/cosmos-framework
- Cosmos RoboLab server: https://github.com/NVIDIA/cosmos-framework/blob/main/cosmos_framework/scripts/action_policy_server_robolab.py
- Cosmos3-Edge-Policy-DROID: https://huggingface.co/nvidia/Cosmos3-Edge-Policy-DROID
- Cosmos3-DROID dataset at the IDM-pinned revision: https://huggingface.co/datasets/nvidia/Cosmos3-DROID/tree/5c11a20accb11497270a5247a7f1e66ad04c956c
- DROID dataset: https://droid-dataset.github.io/
- DROID schema/downloads: https://droid-dataset.github.io/droid/the-droid-dataset.html
- DROID trajectory collection action alignment (pinned source): https://github.com/droid-dataset/droid/blob/33ae6a67274f36d2e29525b86f23a56616ef43a7/droid/trajectory_utils/misc.py#L70-L115
- Robometer repository: https://github.com/robometer/robometer
- Robometer-4B: https://huggingface.co/robometer/Robometer-4B
- Robometer paper: https://arxiv.org/abs/2603.02115
- DreamZero paper: https://arxiv.org/abs/2602.15922
- EVA inverse-dynamics paper: https://arxiv.org/abs/2603.17808
- EVA reference implementation: https://github.com/RobbinW/EVA

Do not assume flags or defaults from this list. Inspect the exact current revision used by the run.
