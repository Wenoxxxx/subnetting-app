"""JSON stdin/stdout bridge so Electron can call Python without extra deps.

Protocol:
  stdin: one JSON object per line, e.g.
    {"action": "flsm", "network": "192.168.1.0/24", "new_prefix": 26}
    {"action": "vlsm", "network": "10.0.0.0/24",
     "requirements": [{"name": "A", "hosts_needed": 50}]}
    {"action": "ipv6", "network": "2001:db8::/48", "new_prefix": 56}
    {"action": "nth", "network": "192.168.1.0/26", "n": 100}
    {"action": "describe", "network": "192.168.1.0/24"}
  stdout: one JSON object per line: {"ok": true, ...} or {"ok": false, "error": "..."}.
"""
from __future__ import annotations

import json
import sys

from .common import describe_network, nth_usable_ip, parse_network
from .ipv4_flsm import calculate_flsm
from .ipv6_subnet import calculate_ipv6_subnets
from .vlsm import calculate_vlsm


def handle_request(request: dict) -> dict:
    """Execute one JSON-RPC-like request dict."""
    if not isinstance(request, dict):
        return {"ok": False, "error": "Request must be a JSON object."}
    action = request.get("action")
    try:
        if action == "flsm":
            subnets = calculate_flsm(
                request["network"],
                new_prefix=request.get("new_prefix"),
                subnet_count=request.get("subnet_count"),
            )
            return {"ok": True, "subnets": [s.to_dict() for s in subnets]}
        if action == "vlsm":
            subnets = calculate_vlsm(request["network"], request.get("requirements", []))
            return {"ok": True, "subnets": [s.to_dict() for s in subnets]}
        if action == "ipv6":
            subnets = calculate_ipv6_subnets(request["network"], request["new_prefix"])
            return {"ok": True, "subnets": [s.to_dict() for s in subnets]}
        if action == "nth":
            return {"ok": True, "ip": nth_usable_ip(request["network"], int(request["n"]))}
        if action == "describe":
            info = describe_network(parse_network(request["network"]))
            return {"ok": True, "subnet": info.to_dict()}
        return {"ok": False, "error": f"Unknown action {action!r}. Use flsm|vlsm|ipv6|nth|describe."}
    except (ValueError, KeyError, TypeError) as exc:
        # KeyError/TypeError = malformed request (client fault); surface message.
        return {"ok": False, "error": str(exc)}


def main() -> int:
    """Read JSON lines from stdin, write JSON lines to stdout."""
    for line_number, line in enumerate(sys.stdin, start=1):
        if not line.strip():
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            sys.stdout.write(json.dumps({"ok": False, "error": f"Line {line_number}: invalid JSON: {exc}"}) + "\n")
            sys.stdout.flush()
            continue
        try:
            response = handle_request(request)
        except Exception as exc:  # Never let one bad line kill the bridge.
            response = {"ok": False, "error": f"Internal error: {exc}"}
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
