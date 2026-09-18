"""FLSM (equal-size) subnetting for IPv4."""
from __future__ import annotations

import math
from ipaddress import IPv4Network

from .common import describe_network, parse_network, SubnetInfo


def calculate_flsm(network_cidr: str, new_prefix: int | None = None, subnet_count: int | None = None) -> list[SubnetInfo]:
    """Split IPv4 network into equal-size subnets.

    Caller provides either new_prefix or subnet_count (not both).

    Args:
        network_cidr: Base network, e.g. "192.168.1.0/24".
        new_prefix: Desired subnet prefix length, e.g. 26.
        subnet_count: Desired number of equal subnets, e.g. 4.

    Returns:
        List of SubnetInfo in address order.

    Raises:
        ValueError: On invalid input or impossible split.
    """
    base = parse_network(network_cidr)
    if not isinstance(base, IPv4Network):
        raise ValueError(f"FLSM expects an IPv4 network, got '{network_cidr}'.")
    target_prefix = _resolve_target_prefix(base, new_prefix, subnet_count)
    if target_prefix < base.prefixlen:
        raise ValueError(
            f"Target prefix /{target_prefix} is larger than base {base}."
        )
    return [describe_network(sub) for sub in base.subnets(new_prefix=target_prefix)]


def _resolve_target_prefix(
    base: IPv4Network, new_prefix: int | None, subnet_count: int | None
) -> int:
    if (new_prefix is None) == (subnet_count is None):
        raise ValueError("Provide exactly one of new_prefix or subnet_count.")
    if new_prefix is not None:
        if not isinstance(new_prefix, int) or not 0 <= new_prefix <= 32:
            raise ValueError(f"new_prefix must be 0-32, got {new_prefix!r}.")
        if new_prefix < base.prefixlen:
            raise ValueError(
                f"new_prefix /{new_prefix} cannot be shorter than base /{base.prefixlen}."
            )
        return new_prefix
    assert subnet_count is not None
    if not isinstance(subnet_count, int) or subnet_count < 1:
        raise ValueError(f"subnet_count must be a positive integer, got {subnet_count!r}.")
    bits_needed = math.ceil(math.log2(subnet_count))
    target = base.prefixlen + bits_needed
    if target > 32:
        raise ValueError(
            f"Cannot fit {subnet_count} subnets inside {base}: needs /{target}."
        )
    return target
