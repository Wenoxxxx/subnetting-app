"""Tests for subnet core: FLSM, VLSM, IPv6, nth usable. Uses stdlib unittest (no new deps)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from subnet_calc import (  # noqa: E402
    calculate_flsm,
    calculate_ipv6_subnets,
    calculate_vlsm,
    describe_network,
    nth_usable_ip,
    parse_network,
    prefix_for_hosts,
)
from subnet_calc.cli import handle_request  # noqa: E402


class TestFlsm(unittest.TestCase):
    def test_split_24_into_26s(self):
        result = calculate_flsm("192.168.1.0/24", new_prefix=26)
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0].network_address, "192.168.1.0")
        self.assertEqual(result[1].network_address, "192.168.1.64")
        self.assertEqual(result[0].subnet_mask, "255.255.255.192")
        self.assertEqual(result[0].first_usable, "192.168.1.1")
        self.assertEqual(result[0].last_usable, "192.168.1.62")
        self.assertEqual(result[0].broadcast_address, "192.168.1.63")
        self.assertEqual(result[0].usable_count, 62)

    def test_split_by_count(self):
        result = calculate_flsm("10.0.0.0/24", subnet_count=4)
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0].prefix_length, 26)

    def test_split_by_count_rounds_up(self):
        result = calculate_flsm("10.0.0.0/24", subnet_count=5)
        self.assertEqual(len(result), 8)  # next power of two

    def test_rejects_both_or_neither(self):
        with self.assertRaises(ValueError):
            calculate_flsm("10.0.0.0/24")
        with self.assertRaises(ValueError):
            calculate_flsm("10.0.0.0/24", new_prefix=26, subnet_count=4)

    def test_rejects_shorter_prefix(self):
        with self.assertRaises(ValueError):
            calculate_flsm("10.0.0.0/24", new_prefix=16)

    def test_rejects_bad_cidr(self):
        with self.assertRaises(ValueError):
            calculate_flsm("not-an-ip", new_prefix=26)


class TestDescribeEdgeCases(unittest.TestCase):
    def test_slash32(self):
        info = describe_network(parse_network("10.0.0.5/32"))
        self.assertEqual(info.usable_count, 1)
        self.assertEqual(info.first_usable, "10.0.0.5")
        self.assertIsNone(info.broadcast_address)

    def test_slash31(self):
        info = describe_network(parse_network("10.0.0.0/31"))
        self.assertEqual(info.usable_count, 2)
        self.assertEqual(info.first_usable, "10.0.0.0")
        self.assertEqual(info.last_usable, "10.0.0.1")

    def test_empty_input(self):
        with self.assertRaises(ValueError):
            parse_network("")


class TestVlsm(unittest.TestCase):
    def test_allocates_largest_first(self):
        result = calculate_vlsm(
            "10.0.0.0/24",
            [
                {"name": "Small", "hosts_needed": 10},
                {"name": "Big", "hosts_needed": 50},
            ],
        )
        self.assertEqual(result[0].name, "Big")
        self.assertEqual(result[0].prefix_length, 26)  # 62 usable >= 50
        self.assertEqual(result[1].name, "Small")
        self.assertEqual(result[1].prefix_length, 28)  # 14 usable >= 10
        # No overlap: second starts at/after first ends.
        self.assertNotEqual(result[0].network_address, result[1].network_address)

    def test_exhaustion_raises(self):
        with self.assertRaises(ValueError):
            calculate_vlsm("10.0.0.0/30", [{"name": "A", "hosts_needed": 50}])

    def test_prefix_for_hosts(self):
        self.assertEqual(prefix_for_hosts(1), 32)
        self.assertEqual(prefix_for_hosts(2), 31)
        self.assertEqual(prefix_for_hosts(50), 26)
        with self.assertRaises(ValueError):
            prefix_for_hosts(0)


class TestNthUsable(unittest.TestCase):
    def test_100th_ip(self):
        # 192.168.1.0/24 usable .1-.254, so 100th = .100
        self.assertEqual(nth_usable_ip("192.168.1.0/24", 100), "192.168.1.100")

    def test_out_of_range(self):
        with self.assertRaises(ValueError):
            nth_usable_ip("192.168.1.0/30", 3)  # only 2 usable

    def test_bad_n(self):
        with self.assertRaises(ValueError):
            nth_usable_ip("192.168.1.0/24", 0)


class TestIpv6(unittest.TestCase):
    def test_split_48_to_56(self):
        result = calculate_ipv6_subnets("2001:db8::/48", 56)
        self.assertEqual(len(result), 256)
        self.assertIsNone(result[0].broadcast_address)
        self.assertIsNone(result[0].subnet_mask)

    def test_rejects_huge_split(self):
        with self.assertRaises(ValueError):
            calculate_ipv6_subnets("2001:db8::/32", 64)


class TestCliBridge(unittest.TestCase):
    def test_rejects_non_dict_request(self):
        for bad in ([1, 2], "flsm", 42, None):
            res = handle_request(bad)
            self.assertFalse(res["ok"])
            self.assertIn("JSON object", res["error"])

    def test_unknown_action(self):
        res = handle_request({"action": "nope"})
        self.assertFalse(res["ok"])

    def test_malformed_request_returns_error_not_raise(self):
        res = handle_request({"action": "flsm"})  # missing network
        self.assertFalse(res["ok"])
        res = handle_request({"action": "nth", "network": "10.0.0.0/24", "n": "abc"})
        self.assertFalse(res["ok"])

    def test_valid_flsm_roundtrip(self):
        res = handle_request({"action": "flsm", "network": "10.0.0.0/24", "new_prefix": 26})
        self.assertTrue(res["ok"])
        self.assertEqual(len(res["subnets"]), 4)


if __name__ == "__main__":
    unittest.main()
