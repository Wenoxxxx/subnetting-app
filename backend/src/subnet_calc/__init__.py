"""Subnet calculator core: IPv4 FLSM/VLSM, IPv6 splits, nth usable IP."""
from .common import SubnetInfo, describe_network, nth_usable_ip, parse_network
from .ipv4_flsm import calculate_flsm
from .ipv6_subnet import calculate_ipv6_subnets
from .vlsm import VlsmRequirement, calculate_vlsm, prefix_for_hosts

__all__ = [
    "SubnetInfo",
    "VlsmRequirement",
    "calculate_flsm",
    "calculate_vlsm",
    "calculate_ipv6_subnets",
    "describe_network",
    "nth_usable_ip",
    "parse_network",
    "prefix_for_hosts",
]
