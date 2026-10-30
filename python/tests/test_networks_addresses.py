"""Tests for bitgold_agent.networks address registry."""

from __future__ import annotations

import pytest
from web3 import Web3

from bitgold_agent.config import NETWORKS
from bitgold_agent.networks import (
    BITGOLD_CHAIN_ADDRESSES,
    BITGOLD_MAINNET_CHAIN_ID,
    BITGOLD_TESTNET_CHAIN_ID,
    PAYMENT_TOKEN_EIP712_NAME,
    PAYMENT_TOKEN_EIP712_VERSION,
    get_address,
    known_payment_tokens,
)


def test_get_address_returns_mainnet_payment_token():
    d = get_address(BITGOLD_MAINNET_CHAIN_ID)
    assert d.payment_token == "0x000000000000000000000000000000000000B706"


def test_get_address_returns_testnet_payment_token():
    d = get_address(BITGOLD_TESTNET_CHAIN_ID)
    assert d.payment_token == "0x000000000000000000000000000000000000B706"


def test_address_registry_matches_current_apex_deployments():
    testnet = get_address(BITGOLD_TESTNET_CHAIN_ID)
    assert testnet.commerce_impl.lower() == "0x0000000000000000000000000000000000000000"
    assert testnet.router_impl.lower() == "0x0000000000000000000000000000000000000000"
    assert testnet.policy.lower() == "0x0000000000000000000000000000000000000000"
    assert NETWORKS["bitgold-testnet"].policy_contract.lower() == testnet.policy.lower()

    mainnet = get_address(BITGOLD_MAINNET_CHAIN_ID)
    assert mainnet.commerce_impl.lower() == "0x0000000000000000000000000000000000000000"


def test_get_address_unknown_chain_raises_keyerror():
    with pytest.raises(KeyError, match="chain_id=1"):
        get_address(1)


def test_all_addresses_are_checksummed():
    """Every address on every chain must be EIP-55 checksum-encoded."""
    for chain_id, deploy in BITGOLD_CHAIN_ADDRESSES.items():
        for field_name in (
            "payment_token",
            "treasury",
            "commerce_proxy",
            "commerce_impl",
            "router_proxy",
            "router_impl",
            "policy",
        ):
            addr = getattr(deploy, field_name)
            assert Web3.is_checksum_address(addr), (
                f"chain {chain_id} field {field_name}={addr} is not checksummed"
            )


def test_known_payment_tokens_contains_both_networks():
    pairs = known_payment_tokens()
    assert (BITGOLD_MAINNET_CHAIN_ID, "0x000000000000000000000000000000000000B706") in pairs
    assert (BITGOLD_TESTNET_CHAIN_ID, "0x000000000000000000000000000000000000B706") in pairs
    assert len(pairs) == 2  # update when adding more networks


def test_known_payment_tokens_is_frozenset_for_policy_use():
    """Must be hashable + immutable so SigningPolicy can use it directly."""
    pairs = known_payment_tokens()
    assert isinstance(pairs, frozenset)
    # frozensets are hashable
    hash(pairs)


def test_deployed_addresses_is_frozen():
    d = get_address(BITGOLD_MAINNET_CHAIN_ID)
    with pytest.raises((AttributeError, Exception)):
        d.payment_token = "0xdeadbeef"  # type: ignore[misc]


def test_eip712_domain_constants_match_phase0_verification():
    """name+version constants must match what's encoded in U token's
    DOMAIN_SEPARATOR on-chain. Phase 0 verification recovered these by
    brute-forcing keccak(name)|keccak(version)|chainId|verifyingContract
    against the live DOMAIN_SEPARATOR() return value."""
    assert PAYMENT_TOKEN_EIP712_NAME == "BTG"
    assert PAYMENT_TOKEN_EIP712_VERSION == "1"
