# Runbook — WHT Exemption

## Service ownership
- Owners: URA DS team / WHT squad

## Scoring
- Inputs: (`tin`, `as_of_date`) feature snapshot
- Outputs: Decision record JSON

## Operational checks
- Validate feature spec version matches deployed model bundle
- Validate rules version matches approved policy baseline

## Incident response
- If scoring fails due to missing features: route to manual review and log reason
- If rules config hash changes unexpectedly: block auto-decisions
