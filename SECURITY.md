# Security Policy

qfire-port is a security-adjacent library (a prompt firewall). We take reports of both
implementation vulnerabilities and detection bypasses seriously.

## Reporting a vulnerability

Please do **not** open a public GitHub issue for:

- A bypass of a shipped rule/chain (an attack prompt that should be blocked but is allowed)
- A vulnerability in the evaluation engine itself (e.g., a way to make `evaluate()` fail open)
- Any issue that could expose PHI or other sensitive data through the library's own behavior

Instead, open a private security advisory on GitHub ("Security" tab → "Report a
vulnerability"), or contact the maintainer directly via the email in the commit history.

Please include: the prompt/rule/chain combination that reproduces the issue, the expected
vs. actual decision, and whether it's a false-negative (bypass) or false-positive
(over-blocking) class of bug.

## Scope

In scope: the `qfire` package (`src/qfire/`) and the shipped example rules/chains under
`rules/`/`chains/`. Rules you author yourself are your own responsibility to validate with
`qfire validate`.

Out of scope: vulnerabilities in third-party dependencies (report those upstream) and
denial-of-service via arbitrarily large/complex rule files you authored yourself.
