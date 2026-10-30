"""On-chain address registry for Bitgold Network deployments.

Source of truth for the BTG payment-token deployment plus the surrounding
commerce/router/policy proxies on ``bitgold-testnet`` (617) and
``bitgold-mainnet`` (618).

The ERC-8004 / ERC-8183 deployments on Bitgold Network are **not published
yet**, so every entry below is the zero-address placeholder. Fill this
manifest once the contracts are deployed — the SDK then treats them exactly
like the reference deployment (direct-call targets, EIP-712 verifying
contract).

Only ``payment_token`` is an EIP-712 verifyingContract (EIP-3009
``TransferWithAuthorization``). The remaining addresses are direct-call
targets (used via ``sign_transaction``) and are exposed here purely as a
lookup convenience — they are **not** added to any signing allowlist by
default.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

from web3 import Web3

from ..config import BITGOLD_MAINNET_CHAIN_ID, BITGOLD_TESTNET_CHAIN_ID, ZERO_ADDRESS

# ── EIP-712 domain metadata for the payment token ─────────────────────────
# Bitgold's payment asset is BTG (18 decimals, native). ERC-8183 escrow needs
# an ERC-20 surface, so the on-chain payment token is the BTG token wrapper;
# its verified EIP-712 domain metadata replaces these values once deployed.

PLACEHOLDER_TOKEN_ADDRESS = "0x000000000000000000000000000000000000B706"

PAYMENT_TOKEN_EIP712_NAME = "BTG"
PAYMENT_TOKEN_EIP712_VERSION = "1"


@dataclass(frozen=True)
class DeployedAddresses:
    """Snapshot of one network's contract deployment."""

    payment_token: str
    treasury: str
    commerce_proxy: str
    commerce_impl: str
    router_proxy: str
    router_impl: str
    policy: str


# Placeholder manifest: every field is the zero address until the Bitgold
# Network deployments are published. The public ``BITGOLD_CHAIN_ADDRESSES``
# table below is the checksummed form.
_RAW: dict[int, dict[str, str]] = {
    BITGOLD_TESTNET_CHAIN_ID: {
        "payment_token": PLACEHOLDER_TOKEN_ADDRESS,
        "treasury": ZERO_ADDRESS,
        "commerce_proxy": ZERO_ADDRESS,
        "commerce_impl": ZERO_ADDRESS,
        "router_proxy": ZERO_ADDRESS,
        "router_impl": ZERO_ADDRESS,
        "policy": ZERO_ADDRESS,
    },
    BITGOLD_MAINNET_CHAIN_ID: {
        "payment_token": PLACEHOLDER_TOKEN_ADDRESS,
        "treasury": ZERO_ADDRESS,
        "commerce_proxy": ZERO_ADDRESS,
        "commerce_impl": ZERO_ADDRESS,
        "router_proxy": ZERO_ADDRESS,
        "router_impl": ZERO_ADDRESS,
        "policy": ZERO_ADDRESS,
    },
}


def _build() -> dict[int, DeployedAddresses]:
    out: dict[int, DeployedAddresses] = {}
    field_names = {f.name for f in fields(DeployedAddresses)}
    for chain_id, raw in _RAW.items():
        missing = field_names - raw.keys()
        if missing:
            raise RuntimeError(f"chain {chain_id} missing addresses: {missing}")
        out[chain_id] = DeployedAddresses(
            **{k: Web3.to_checksum_address(v) for k, v in raw.items()}
        )
    return out


BITGOLD_CHAIN_ADDRESSES: dict[int, DeployedAddresses] = _build()


def get_address(chain_id: int) -> DeployedAddresses:
    """Return the deployment snapshot for ``chain_id``.

    Raises:
        KeyError: if ``chain_id`` is not a known Bitgold Network deployment.
    """
    try:
        return BITGOLD_CHAIN_ADDRESSES[chain_id]
    except KeyError as e:
        raise KeyError(
            f"no Bitgold Network deployment registered for chain_id={chain_id}; "
            f"known: {sorted(BITGOLD_CHAIN_ADDRESSES)}"
        ) from e


def known_payment_tokens() -> frozenset[tuple[int, str]]:
    """``(chain_id, checksum_address)`` pairs of every registered payment token.

    Compatibility API for deployment-registry callers. ``SigningPolicy``
    ``strict_default()`` derives its domain allowlist from active catalog
    assets with verified EIP-3009 metadata, so this set must not be used to
    infer every strict-signing domain.
    """
    return frozenset(
        (cid, deploy.payment_token) for cid, deploy in BITGOLD_CHAIN_ADDRESSES.items()
    )
