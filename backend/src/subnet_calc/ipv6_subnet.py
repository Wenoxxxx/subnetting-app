"""IPv6 subnetting (equal-size splits)."""
from __future__ import annotations

from ipaddress import IPv6Network

from .common import describe_network, parse_network, SubnetInfo


def calculate_ipv6_subnets(network_cidr: str, new_prefix: int) -> list[SubnetInfo]:
    """Split IPv6 network into equal-size subnets.

    Args:
        network_cidr: Base IPv6 network, e.g. "2001:db8::/48".
        new_prefix: Target prefix, must be longer than base.

    Returns:
        List of SubnetInfo. Note: caller should cap new_prefix growth
        since IPv6 splits explode combinatorially.
    """
    base = parse_network(network_cidr)
    if not isinstance(base, IPv6Network):
        raise ValueError(f"Expected IPv6 network, got '{network_cidr}'.")
    if not isinstance(new_prefix, int) or not 0 <= new_prefix <= 128:
        raise ValueError(f"new_prefix must be 0-128, got {new_prefix!r}.")
    if new_prefix < base.prefixlen:
        raise ValueError(
            f"new_prefix /{new_prefix} cannot be shorter than base /{base.prefixlen}."
        )
    # Guard against accidental billion-subnet generation.
    diff = new_prefix - base.prefixlen
    if diff > 16:
        raise ValueError(
            f"Split /{base.prefixlen} -> /{new_prefix} would create "
            f"{2 ** diff} subnets; limit prefix growth to 16 bits."
        )
    return [describe_network(sub) for sub in base.subnets(new_prefix=new_prefix)]
