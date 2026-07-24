"""qfire CLI: evaluate a prompt or validate a rule set from the command line.

stdlib argparse only — no CLI framework dependency for two subcommands.
"""

from __future__ import annotations

import argparse
import json
import sys

from qfire import evaluate, load_chains, load_rules, validate_rule
from qfire.errors import QfireError


def _cmd_evaluate(args: argparse.Namespace) -> int:
    try:
        rules = load_rules(args.rules)
        chains = load_chains(args.chains, rules)
        decision = evaluate(
            args.prompt, chain_id=args.chain_id, chains=chains, normalize=not args.no_normalize
        )
    except QfireError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyError as exc:
        print(f"error: unknown chain id {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(decision.trace.as_dict(), indent=2, default=str))
    else:
        print(f"decision: {decision.decision}")
        if decision.fired_rule_id:
            print(f"fired_rule_id: {decision.fired_rule_id}")
        if decision.trace.error:
            print(f"error: {decision.trace.error}")
    return 1 if decision.decision == "block" else 0


def _cmd_validate(args: argparse.Namespace) -> int:
    try:
        rules = load_rules(args.rules)
    except QfireError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    any_failed = False
    for rule in rules:
        result = validate_rule(rule)
        status = "PASS" if not result.failed else "FAIL"
        print(f"{status} {rule.id} ({len(result.passed)} passed, {len(result.failed)} failed)")
        for prompt, actual in result.failed:
            any_failed = True
            print(f"  - {prompt!r} -> expected opposite of {actual!r}")
    return 1 if any_failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qfire", description="Declarative prompt firewall.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_eval = sub.add_parser("evaluate", help="evaluate a prompt against a chain")
    p_eval.add_argument("prompt", help="the prompt text to evaluate")
    p_eval.add_argument("--rules", required=True, help="rule file or directory")
    p_eval.add_argument("--chains", required=True, help="chain file or directory")
    p_eval.add_argument("--chain-id", required=True, help="chain id to evaluate against")
    p_eval.add_argument("--no-normalize", action="store_true", help="skip de-obfuscation pass")
    p_eval.add_argument("--json", action="store_true", help="print the full decision trace as JSON")
    p_eval.set_defaults(func=_cmd_evaluate)

    p_validate = sub.add_parser("validate", help="validate every rule's own exemplars")
    p_validate.add_argument("--rules", required=True, help="rule file or directory")
    p_validate.set_defaults(func=_cmd_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
