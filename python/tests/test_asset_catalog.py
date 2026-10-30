"""Cross-language contract tests for the Bitgold Network payment-asset catalog.

Bitgold settles in BTG only (18 decimals). The catalog ships one entry per
network, pinned to the documented placeholder token address until the on-chain
deployment lands.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from typing import Any

import pytest

import bitgold_agent.networks as networks

MAINNET = 618
TESTNET = 617
PLACEHOLDER = "0x000000000000000000000000000000000000B706"


def _api(name: str) -> Any:
    assert hasattr(networks, name), f"bitgold_agent.networks.{name} is not implemented"
    return getattr(networks, name)


def _snapshot() -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for chain_id in (MAINNET, TESTNET):
        for asset in networks.list_assets(chain_id):
            result.append(
                {
                    "chain_id": asset.chain_id,
                    "asset_id": asset.asset_id.value,
                    "symbol": asset.symbol,
                    "address": asset.address,
                    "decimals": asset.decimals,
                    "availability": asset.availability,
                    "b402_methods": asset.b402_methods,
                    "eip3009_domain": (
                        None
                        if asset.eip3009_domain is None
                        else (asset.eip3009_domain.name, asset.eip3009_domain.version)
                    ),
                    "is_default": asset.is_default,
                }
            )
    return result


def test_asset_catalog_snapshot_is_btg_only() -> None:
    assert _snapshot() == [
        {
            "chain_id": MAINNET,
            "asset_id": "BTG",
            "symbol": "BTG",
            "address": PLACEHOLDER,
            "decimals": 18,
            "availability": "active",
            "b402_methods": ("eip3009", "permit2-exact"),
            "eip3009_domain": ("BTG", "1"),
            "is_default": True,
        },
        {
            "chain_id": TESTNET,
            "asset_id": "TEST_BTG",
            "symbol": "tBTG",
            "address": PLACEHOLDER,
            "decimals": 18,
            "availability": "active",
            "b402_methods": ("eip3009", "permit2-exact"),
            "eip3009_domain": ("BTG", "1"),
            "is_default": True,
        },
    ]


def test_catalog_entries_are_consistent_across_networks() -> None:
    mainnet = networks.get_asset(MAINNET, networks.AssetId.BTG)
    testnet = networks.get_asset(TESTNET, networks.AssetId.TEST_BTG)

    assert mainnet.chain_id == MAINNET and testnet.chain_id == TESTNET
    assert mainnet.decimals == testnet.decimals == 18
    assert mainnet.address == testnet.address == networks.PLACEHOLDER_TOKEN_ADDRESS
    assert networks.get_b402_asset(MAINNET, networks.AssetId.BTG).address == PLACEHOLDER
    assert networks.get_asset_by_address(MAINNET, PLACEHOLDER.lower()) is mainnet
    assert networks.get_b402_asset_by_address(TESTNET, PLACEHOLDER.lower()).address == PLACEHOLDER


def test_alias_resolution_is_network_scoped() -> None:
    assert networks.resolve_asset_alias(MAINNET, "BTG") is networks.AssetId.BTG
    assert networks.resolve_asset_alias(TESTNET, "BTG") is networks.AssetId.TEST_BTG
    assert networks.resolve_asset_alias(TESTNET, "TBTG") is networks.AssetId.TEST_BTG
    with pytest.raises(KeyError, match="unknown asset alias"):
        networks.resolve_asset_alias(TESTNET, "USDC")
    with pytest.raises(KeyError):
        networks.resolve_asset_alias(56, "BTG")


def test_unknown_assets_and_chains_are_rejected() -> None:
    with pytest.raises(ValueError, match="unknown canonical AssetId"):
        networks.parse_asset_id("USDC")
    with pytest.raises(KeyError):
        networks.list_assets(56)
    with pytest.raises((KeyError, ValueError)):
        networks.get_asset(MAINNET, "USDC")
    with pytest.raises(KeyError):
        networks.get_address(1)


def test_atomic_amounts_use_eighteen_decimals() -> None:
    assert networks.to_asset_atomic(MAINNET, networks.AssetId.BTG, "0") == 0
    assert (
        networks.to_asset_atomic(MAINNET, networks.AssetId.BTG, "1.5") == 1_500_000_000_000_000_000
    )
    assert (
        networks.to_asset_atomic(TESTNET, networks.AssetId.TEST_BTG, "0.000000000000000001") == 1
    )

    for invalid in ("", "-1", "1e18", "1.2.3", " 1", "1."):
        with pytest.raises(ValueError, match="invalid decimal amount"):
            networks.to_asset_atomic(MAINNET, networks.AssetId.BTG, invalid)
    with pytest.raises(TypeError):
        networks.to_asset_atomic(MAINNET, networks.AssetId.BTG, 1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="exceeds 18 decimal places"):
        networks.to_asset_atomic(MAINNET, networks.AssetId.BTG, "0.0000000000000000001")


def test_strict_signing_domains_cover_the_placeholder_token() -> None:
    assert networks.known_eip3009_payment_tokens() == frozenset(
        {(MAINNET, PLACEHOLDER), (TESTNET, PLACEHOLDER)}
    )
    assert networks.known_payment_tokens() == frozenset(
        {(MAINNET, PLACEHOLDER), (TESTNET, PLACEHOLDER)}
    )


def test_asset_metadata_is_immutable() -> None:
    asset = networks.get_asset(MAINNET, networks.AssetId.BTG)
    with pytest.raises(FrozenInstanceError):
        asset.decimals = 6  # type: ignore[misc]


def _active_asset(**overrides: object) -> Any:
    fields: dict[str, object] = {
        "chain_id": MAINNET,
        "asset_id": networks.AssetId.BTG,
        "symbol": "BTG",
        "address": "0x000000000000000000000000000000000000b707",
        "decimals": 18,
        "b402_methods": ("eip3009",),
        "eip3009_domain": networks.EIP3009Domain("BTG", "1"),
        "is_default": True,
        "b402_kinds": (networks.B402Kind("eip3009", "BTG", "1"),),
    }
    fields.update(overrides)
    return networks.PaymentAsset(**fields)


def test_catalog_accepts_a_custom_deployed_entry() -> None:
    catalog = networks.AssetCatalog((_active_asset(),))
    asset = catalog.get(MAINNET, networks.AssetId.BTG)
    assert asset.address == "0x000000000000000000000000000000000000b707"
    assert catalog.by_address(MAINNET, asset.address.lower()) is asset
    assert catalog.get_b402(MAINNET, networks.AssetId.BTG).decimals == 18


def test_catalog_rejects_duplicate_entries() -> None:
    with pytest.raises(ValueError, match="duplicate catalog key"):
        networks.AssetCatalog((_active_asset(), _active_asset()))


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"address": "0x" + "0" * 40}, "active asset cannot use zero address"),
        ({"availability": "placeholder"}, "placeholder asset must use zero address"),
        (
            {
                "address": "0x" + "0" * 40,
                "availability": "placeholder",
                "b402_kinds": (),
            },
            "placeholder asset cannot declare B402 methods",
        ),
        (
            {
                "address": "0x" + "0" * 40,
                "availability": "placeholder",
                "b402_methods": (),
                "b402_kinds": (),
            },
            "placeholder asset cannot declare an EIP-3009 domain",
        ),
        (
            {
                "address": "0x" + "0" * 40,
                "availability": "placeholder",
                "b402_methods": (),
                "b402_kinds": (),
                "eip3009_domain": None,
            },
            "placeholder asset cannot be the default asset",
        ),
    ],
)
def test_catalog_constructor_rejects_invalid_availability_invariants(
    changes: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        networks.AssetCatalog((_active_asset(**changes),))


def test_omitted_availability_defaults_to_active() -> None:
    legacy = replace(_active_asset(), availability="active")
    catalog = networks.AssetCatalog((legacy,))
    assert catalog.get(MAINNET, networks.AssetId.BTG).availability == "active"
