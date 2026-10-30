"""Bitgold Network deployment registry — addresses + EIP-712 metadata.

Public API::

    from bitgold_agent.networks import (
        BITGOLD_CHAIN_ADDRESSES,
        DeployedAddresses,
        get_address,
        known_payment_tokens,
        BITGOLD_MAINNET_CHAIN_ID,
        BITGOLD_TESTNET_CHAIN_ID,
        PAYMENT_TOKEN_EIP712_NAME,
        PAYMENT_TOKEN_EIP712_VERSION,
    )
"""

from __future__ import annotations

from .addresses import (
    BITGOLD_CHAIN_ADDRESSES,
    BITGOLD_MAINNET_CHAIN_ID,
    BITGOLD_TESTNET_CHAIN_ID,
    PAYMENT_TOKEN_EIP712_NAME,
    PAYMENT_TOKEN_EIP712_VERSION,
    PLACEHOLDER_TOKEN_ADDRESS,
    DeployedAddresses,
    get_address,
    known_payment_tokens,
)
from .assets import (
    ASSET_CATALOG,
    AssetAlias,
    AssetCatalog,
    AssetId,
    B402Kind,
    B402PaymentAsset,
    B402TransferMethod,
    EIP3009Domain,
    PaymentAsset,
    PaymentAssetAvailability,
    PaymentAssetUnavailableError,
    get_asset,
    get_asset_by_address,
    get_asset_metadata,
    get_b402_asset,
    get_b402_asset_by_address,
    known_eip3009_payment_tokens,
    list_assets,
    parse_asset_id,
    resolve_asset_alias,
    to_asset_atomic,
)

__all__ = [
    "BITGOLD_CHAIN_ADDRESSES",
    "ASSET_CATALOG",
    "AssetAlias",
    "AssetCatalog",
    "AssetId",
    "B402Kind",
    "B402PaymentAsset",
    "B402TransferMethod",
    "BITGOLD_MAINNET_CHAIN_ID",
    "BITGOLD_TESTNET_CHAIN_ID",
    "DeployedAddresses",
    "EIP3009Domain",
    "PAYMENT_TOKEN_EIP712_NAME",
    "PLACEHOLDER_TOKEN_ADDRESS",
    "PAYMENT_TOKEN_EIP712_VERSION",
    "PaymentAsset",
    "PaymentAssetAvailability",
    "PaymentAssetUnavailableError",
    "get_asset",
    "get_asset_by_address",
    "get_b402_asset",
    "get_b402_asset_by_address",
    "get_asset_metadata",
    "known_eip3009_payment_tokens",
    "get_address",
    "known_payment_tokens",
    "list_assets",
    "parse_asset_id",
    "resolve_asset_alias",
    "to_asset_atomic",
]
