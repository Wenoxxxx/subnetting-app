"""VLSM (variable-size) allocation for IPv4."""
from __future__ import annotations

import math
from dataclasses import dataclass
from ipaddress import IPv4Network

from .common import describe_network, parse_network, SubnetInfo


@dataclass(frozen=True)
class VlsmRequirement:
    """One allocation request."""

    name: str
    hosts_needed: int


def prefix_for_hosts(hosts_needed: int) -> int:
    """Return smallest prefix length fitting hosts_needed usable hosts.

    Accounts for network+broadcast overhead, with /31 and /32 specials.

    Args:
        hosts_needed: Usable hosts required (>=1).

    Returns:
        Prefix length 32 down to 0.
    """
    if not isinstance(hosts_needed, int) or hosts_needed < 1:
        raise ValueError(f"hosts_needed must be >= 1, got {hosts_needed!r}.")
    if hosts_needed == 1:
        return 32
    if hosts_needed == 2:
        return 31
    # +2 for network + broadcast, then round up to power of two.
    total = hosts_needed + 2
    host_bits = math.ceil(math.log2(total))
    return 32 - host_bits


def calculate_vlsm(base_cidr: str, requirements: list[VlsmRequirement | dict]) -> list[SubnetInfo]:
    """Allocate subnets largest-first inside base network.

    Args:
        base_cidr: Base network, e.g. "10.0.0.0/24".
        requirements: List of VlsmRequirement or {"name","hosts_needed"} dicts.

    Returns:
        Allocated SubnetInfo list in allocation order (largest first).

    Raises:
        ValueError: On bad input or address-space exhaustion.
    """
    base = parse_network(base_cidr)
    if not isinstance(base, IPv4Network):
        raise ValueError(f"VLSM expects an IPv4 base network, got '{base_cidr}'.")
    normalized = _normalize_requirements(requirements)
    if not normalized:
        raise ValueError("At least one VLSM requirement is needed.")
    # Largest first minimizes fragmentation.
    normalized.sort(key=lambda r: r.hosts_needed, reverse=True)

    base_int = int(base.network_address)
    base_size = base.num_addresses
    cursor = base_int
    results: list[SubnetInfo] = []
    for req in normalized:
        prefix = prefix_for_hosts(req.hosts_needed)
        size = 2 ** (32 - prefix)
        # Align cursor to prefix boundary relative to base start.
        offset = cursor - base_int
        remainder = offset % size
        if remainder:
            cursor += size - remainder
        if cursor + size > base_int + base_size:
            raise ValueError(
                f"Insufficient space in {base}: '{req.name}' "
                f"needs /{prefix} ({size} addresses)."
            )
        subnet = IPv4Network((cursor, prefix))
        results.append(describe_network(subnet, name=req.name))
        cursor += size
    return results


def _normalize_requirements(
    requirements: list[VlsmRequirement | dict],
) -> list[VlsmRequirement]:
    normalized: list[VlsmRequirement] = []
    for index, item in enumerate(requirements):
        if isinstance(item, dict):
            name = item.get("name", f"Net{index + 1}")
            hosts = item.get("hosts_needed", item.get("hosts"))
        elif isinstance(item, VlsmRequirement):
            name, hosts = item.name, item.hosts_needed
        else:
            raise ValueError(
                f"Requirement #{index + 1} must be VlsmRequirement or dict, got {type(item).__name__}."
            )
        if not isinstance(hosts, int) or hosts < 1:
            raise ValueError(
                f"Requirement '{name}' needs hosts_needed >= 1, got {hosts!r}."
            )
        normalized.append(VlsmRequirement(name=str(name), hosts_needed=hosts))
    return normalized
