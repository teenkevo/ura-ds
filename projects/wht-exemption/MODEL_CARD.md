# Model Card — WHT Exemption

## Summary
Predicts probability `p_safe_to_exempt` for WHT exemption decision support.

## Intended use
Decision support with human oversight. ML does not override fatal legal rules.

## Inputs
Feature store row keyed by (`tin`, `as_of_date`) as defined in `configs/feature_spec.yaml`.

## Outputs
Decision record JSON (see `src/wht_exemption/schemas/decision_record.schema.json`).

## Performance
See `docs/evaluation.md`.

## Monitoring
- Decision volume, auto-approve rate, override rate
- Drift on key composites
- Post-decision adverse events

## Limitations
- Dependent on correctness and freshness of upstream feature store.
- Policy changes require versioned rule updates.
