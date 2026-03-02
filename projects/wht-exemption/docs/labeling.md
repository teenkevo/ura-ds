# Label Definition

Define the supervised learning target for `p_safe_to_exempt`.

## Candidate label (recommended)
Positive (1): exemption granted AND no adverse event during exemption period.
Negative (0): exemption granted AND revoked or major adverse compliance event.

## Notes
- Train only on rule-pass population (no fatal violations) to keep ML focused on risk stratification.
