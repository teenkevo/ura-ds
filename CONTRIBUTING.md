# Contributing

## Workflow
1. Create a feature branch from `main`
2. Make small, reviewable commits
3. Open a Pull Request (PR)
4. Ensure CI passes and required reviews are obtained
5. Merge via PR (no direct pushes to `main`)

## Documentation expectations
Any meaningful change to model logic, features, thresholds, or rules must include documentation updates:
- `MODEL_CARD.md`
- `docs/design.md`
- `docs/labeling.md`
- `docs/evaluation.md`

## Quality
- Add tests for new logic
- Keep changes reproducible (document how to run training/scoring)
