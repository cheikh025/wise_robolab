# Research Goal

## Primary goal

Implement and rigorously evaluate **WISE** as a test-time rollout selector for frozen `nvidia/Cosmos3-Edge-Policy-DROID` on RoboLab.

At every control decision, generate K native Cosmos world-action candidates from the same context and rank complete candidates before execution.

WISE combines:

- `r_exec`: action validity / temporal regularity;
- `r_cons`: agreement between Cosmos's co-generated action and the action inferred from its imagined future by an independently trained DROID IDM;
- `r_task`: instruction-conditioned task progress from general `Robometer-4B`.

RoboLab's state-based task success remains the downstream evaluation metric.

## Required evidence chain

1. RoboLab is reproducibly working.
2. Cosmos3-Edge is correctly integrated and measured at B=1.
3. Native imagined rollout video can be retained and K candidates are genuinely diverse.
4. Robometer runs offline and gives meaningful progress signal on relevant RoboLab/Cosmos data.
5. Robometer-only Best-of-K is implemented and benchmarked as a strong baseline.
6. A DROID IDM is trained and validated first on held-out real DROID data, then on Cosmos-generated dreams.
7. Full WISE is integrated with separable score terms and candidate-relative calibration.
8. Controlled experiments establish whether full WISE improves selection beyond the strongest simpler baselines.

## Scientific question

The key question is not simply whether more samples help. It is whether **process-level evaluation of the native world-action pair** gives better action selection than evaluating imagined task progress alone.

In particular, test whether adding action suitability and cross-output action/future coherence improves over Robometer-only Best-of-K.

## Constraints

- Keep the Cosmos policy frozen for the core WISE experiments unless a later experiment is explicitly about changing the base policy.
- No speculative environment execution during candidate selection.
- Do not use RoboLab success predicates as selector inputs.
- Preserve canonical RoboLab task/success semantics for direct comparisons.
- Record latency/compute as well as success: test-time scaling must report the cost of K.
