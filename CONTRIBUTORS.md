# Contributors Guide

This repository follows a simple and objective contribution workflow.

## Documentation Language Policy

All `.md` files in this repository must be written in **English**.

- New Markdown files must be created in English.
- Existing Markdown updates must keep content in English.
- If a file is in another language, normalize it to English as part of the change.

## Standard Issue Rule

Every change must start with an Issue.

### Minimum required Issue structure

- **Clear title**: imperative verb + object (e.g., "Add permission validation to CLI").
- **Context**: what real problem is being solved.
- **Objective**: expected outcome of the change.
- **Scope**:
  - **Includes**: what will be done.
  - **Excludes**: what will not be done (avoid scope creep).
- **Acceptance criteria**: verifiable checklist.
- **Risks and impact**: security, compatibility, performance.
- **Validation plan**: how to test (commands, scenarios, data).

### Rules

- 1 Issue = 1 main problem/deliverable.
- No Issue, no PR.
- Every PR must reference an Issue (`Closes #<id>` or `Refs #<id>`).
- Large changes must be split into smaller Issues.

---

## Contribution Best Practices

### Code

- Make small, focused changes.
- Fix the root cause, not only the symptom.
- Preserve the existing project style and patterns.
- Avoid unnecessary renames/refactors outside scope.

### Tests

- Add or update tests when behavior changes.
- Run relevant tests before opening a PR.
- Do not break existing tests without explicit justification.

### Security

- Never commit secrets (`.env`, tokens, keys).
- Do not expose credentials in logs, examples, or screenshots.
- Review user inputs and error handling to avoid data leakage.

### Documentation

- Update documentation when changing interfaces, flags, or usage flow.
- Prefer executable instructions and real examples.
- Keep `README.md` concise; place details in `docs/`.

### Commits and PRs

- Use clear and objective commit messages.
- PR must include:
  - summary of the change,
  - motivation,
  - test evidence,
  - impact and rollback plan (if applicable).

---

## Quick checklist before PR

- [ ] Issue created and referenced.
- [ ] Scope validated (no unplanned extras).
- [ ] Tests run and passing.
- [ ] No secrets or improper versioning.
- [ ] Documentation updated.
- [ ] Change ready for review.

---

## How to get started

1. Open an Issue using the template above.
2. Create a branch from `main`.
3. Implement in small increments.
4. Run tests and validations.
5. Open a PR referencing the Issue.
