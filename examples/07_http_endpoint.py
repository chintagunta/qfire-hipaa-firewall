"""Use case: expose evaluate() as an HTTP endpoint in front of your own LLM call.

This is a minimal example using only the stdlib (no new dependency for the library itself).
For a production service you'd likely reach for FastAPI/Flask — the wiring is the same:
call qfire.evaluate() first, and only forward to your LLM provider on "allow".

Run:    python examples/07_http_endpoint.py
Try:    curl -s localhost:8000/evaluate -d '{"prompt": "hello", "chain_id": "hipaa_phi"}'
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from qfire import evaluate, load_chains, load_rules

RULES = load_rules("rules/")
CHAINS = load_chains("chains/", RULES)


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/evaluate":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            prompt = body["prompt"]
            chain_id = body["chain_id"]
        except (json.JSONDecodeError, KeyError) as exc:
            self._json(400, {"error": f"bad request: {exc}"})
            return

        try:
            decision = evaluate(prompt, chain_id=chain_id, chains=CHAINS)
        except KeyError:
            self._json(404, {"error": f"unknown chain_id {chain_id!r}"})
            return

        status = 403 if decision.decision == "block" else 200
        self._json(
            status,
            {
                "decision": decision.decision,
                "fired_rule_id": decision.fired_rule_id,
                "trace": decision.trace.as_dict(),
            },
        )

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002 - quiet by default
        pass


if __name__ == "__main__":
    server = HTTPServer(("localhost", 8000), Handler)
    print("qfire evaluate endpoint listening on http://localhost:8000/evaluate")
    server.serve_forever()
