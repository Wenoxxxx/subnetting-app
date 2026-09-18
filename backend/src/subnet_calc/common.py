"""Shared types and helpers for subnet calculations."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from ipaddress import IPv4Network, IPv6Network, ip_network
from typing import Union

Network = Union[IPv4Network, IPv6Network]


@dataclass(frozen=True)
class SubnetInfo:
    """Single calculated subnet row for table display."""

    network_address: str
    prefix_length: int
    subnet_mask: str | None
    first_usable: str | None
    last_usable: str | None
    broadcast_address: str | None
    usable_count: int
    name: str | None = None

    def to_dict(self) -> dict:
        """Return JSON-serializable dict."""
        return asdict(self)


def parse_network(cidr: str) -> Network:
    """Parse CIDR string, raising descriptive ValueError on bad input.

    Args:
        cidr: Network in CIDR notation, e.g. "192.168.1.0/24".

    Returns:
        IPv4Network or IPv6Network with strict=False (host bits allowed).

    Raises:
        ValueError: If input is empty or not valid CIDR.
    """
    if not cidr or not cidr.strip():
        raise ValueError("Network CIDR is required, e.g. '192.168.1.0/24'.")
    try:
        return ip_network(cidr.strip(), strict=False)
    except ValueError as exc:
        raise ValueError(f"Invalid network '{cidr}': {exc}") from exc


def describe_network(net: Network, name: str | None = None) -> SubnetInfo:
    """Build SubnetInfo for one network.

    Args:
        net: Parsed IPv4/IPv6 network.
        name: Optional label (used by VLSM allocation).

    Returns:
        Populated SubnetInfo.
    """
    if isinstance(net, IPv4Network):
        return _describe_ipv4(net, name)
    return _describe_ipv6(net, name)


def _describe_ipv4(net: IPv4Network, name: str | None) -> SubnetInfo:
    prefix = net.prefixlen
    if prefix == 32:
        # Single-host: address itself is usable, no broadcast range.
        return SubnetInfo(
            network_address=str(net.network_address),
            prefix_length=prefix,
            subnet_mask=str(net.netmask),
            first_usable=str(net.network_address),
            last_usable=str(net.network_address),
            broadcast_address=None,
            usable_count=1,
            name=name,
        )
    if prefix == 31:
        # RFC 3021 point-to-point: both addresses usable, no broadcast.
        return SubnetInfo(
            network_address=str(net.network_address),
            prefix_length=prefix,
            subnet_mask=str(net.netmask),
            first_usable=str(net.network_address),
            last_usable=str(net.broadcast_address),
            broadcast_address=None,
            usable_count=2,
            name=name,
        )
    first = net.network_address + 1
    last = net.broadcast_address - 1
    return SubnetInfo(
        network_address=str(net.network_address),
        prefix_length=prefix,
        subnet_mask=str(net.netmask),
        first_usable=str(first),
        last_usable=str(last),
        broadcast_address=str(net.broadcast_address),
        usable_count=int(net.num_addresses) - 2,
        name=name,
    )


def _describe_ipv6(net: IPv6Network, name: str | None) -> SubnetInfo:
    # IPv6 has no broadcast; every address is usable.
    # first/last can be huge ranges — still exact via int math.
    first = net.network_address
    last = net.network_address + (net.num_addresses - 1)
    return SubnetInfo(
        network_address=str(net.network_address),
        prefix_length=net.prefixlen,
        subnet_mask=None,
        first_usable=str(first),
        last_usable=str(last),
        broadcast_address=None,
        usable_count=int(net.num_addresses),
        name=name,
    )


def nth_usable_ip(cidr: str, n: int) -> str:
    """Return nth usable IP (1-indexed) inside usable range.

    Args:
        cidr: Subnet in CIDR notation.
        n: 1-indexed position inside usable range.

    Returns:
        IP address string.

    Raises:
        ValueError: If n out of range or input invalid.
    """
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"Position n must be a positive integer, got {n!r}.")
    net = parse_network(cidr)
    info = describe_network(net)
    if info.first_usable is None or info.last_usable is None:
        raise ValueError(f"Network '{cidr}' has no usable addresses.")
    if n > info.usable_count:
        raise ValueError(
            f"Position {n} out of range: subnet '{cidr}' "
            f"has {info.usable_count} usable addresses."
        )
    if isinstance(net, IPv6Network):
        return str(net.network_address + (n - 1))
    if net.prefixlen == 32:
        return str(net.network_address)
    if net.prefixlen == 31:
        return str(net.network_address + (n - 1))
    return str(net.network_address + n)
