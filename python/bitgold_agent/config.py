"""Top-level SDK configuration.

Exports:

- :class:`NetworkConfig` — per-network defaults (RPC endpoint, explorer, and
  contract addresses for every module that uses on-chain state).
- :func:`resolve_network` — looks up a preset by name, with an optional
  ``RPC_URL`` env override. **Module-specific contract overrides live in
  their own module configs** (e.g. ``ERC8183Config``, ``get_erc8004_config``),
  not here.

Env var surface
---------------
``resolve_network`` is intentionally narrow: it only reads ``RPC_URL``.
Module-scoped env vars (``ERC8183_COMMERCE_ADDRESS``, ``ERC8004_REGISTRY_ADDRESS``,
``STORAGE_*``, ...) are owned by the corresponding module config. The
project-root ``.env.example`` is the authoritative reference.

Contract addresses ship as zero-address placeholders: the Bitgold Network
deployments of the ERC-8004 registry and the ERC-8183 stack (AgenticCommerce,
EvaluatorRouter, OptimisticPolicy) are not published yet. Point the
``ERC8004_REGISTRY_ADDRESS`` / ``ERC8183_*_ADDRESS`` env vars — or edit the
presets below — once they are.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .core.config import get_env

logger = logging.getLogger(__name__)

#: Placeholder used until the Bitgold Network deployments are published.
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

#: Bitgold Mainnet / testnet chain ids.
BITGOLD_MAINNET_CHAIN_ID = 618
BITGOLD_TESTNET_CHAIN_ID = 617


@dataclass
class NetworkConfig:
    """Per-network configuration with ALL protocol addresses.

    ERC-8183 is a three-contract stack: AgenticCommerce kernel (escrow),
    EvaluatorRouter (routing + hook), and OptimisticPolicy (silence-approves,
    vote-rejects). Payment token is NOT configured here — it is immutable
    on the Commerce kernel and read at runtime via ``ERC8183Client.payment_token``.

    Bitgold has no gas-sponsorship relay: ``paymaster_url`` stays ``None`` and
    ``use_paymaster`` stays ``False`` (writes self-pay gas in BTG). The fields
    are kept so an operator can wire their own ERC-4337 paymaster later.
    """

    name: str
    chain_id: int
    rpc_url: str
    paymaster_url: str | None = None
    use_paymaster: bool = False
    # ERC-8004 Identity Registry
    registry_contract: str = ""
    # ERC-8183 stack
    commerce_contract: str = ""
    router_contract: str = ""
    policy_contract: str = ""
    # Human-facing endpoints (documentation / tooling convenience).
    explorer_url: str = ""
    faucet_url: str = ""
    docs_url: str = "https://docs.bitgold.network"


NETWORKS: dict[str, NetworkConfig] = {
    "bitgold-testnet": NetworkConfig(
        name="bitgold-testnet",
        chain_id=BITGOLD_TESTNET_CHAIN_ID,
        rpc_url="https://testnet1.bitgold.network",
        paymaster_url=None,
        use_paymaster=False,
        registry_contract=ZERO_ADDRESS,
        commerce_contract=ZERO_ADDRESS,
        router_contract=ZERO_ADDRESS,
        policy_contract=ZERO_ADDRESS,
        explorer_url="https://testnet.bitgold.live",
        faucet_url="https://faucet.bitgold.network",
    ),
    "bitgold-mainnet": NetworkConfig(
        name="bitgold-mainnet",
        chain_id=BITGOLD_MAINNET_CHAIN_ID,
        rpc_url="https://rpc.bitgold.network",
        paymaster_url=None,
        use_paymaster=False,
        registry_contract=ZERO_ADDRESS,
        commerce_contract=ZERO_ADDRESS,
        router_contract=ZERO_ADDRESS,
        policy_contract=ZERO_ADDRESS,
        explorer_url="https://www.bitgold.live",
        faucet_url="",
    ),
}


def resolve_network(network: str | NetworkConfig = "bitgold-testnet") -> NetworkConfig:
    """Resolve a network preset to a concrete ``NetworkConfig``.

    Accepts either a preset name (``"bitgold-testnet"`` / ``"bitgold-mainnet"``) or a
    concrete ``NetworkConfig`` instance:

    - **String** → look up the preset; apply the RPC env override if set.
      Module-scoped contract-address envs (``ERC8183_*``, ``ERC8004_*``) are
      NOT read here — they belong to each module's own config loader.
    - **NetworkConfig** → returned as-is; env vars are never applied (fully
      explicit control is the point of passing an object).

    RPC override precedence (a process that touches several networks needs
    per-network pins — a single shared URL would silently apply to the wrong
    chain):

    1. ``RPC_URL_<NETWORK>`` — per-network, e.g. ``RPC_URL_BITGOLD_TESTNET`` /
       ``RPC_URL_BITGOLD_MAINNET`` (preset name uppercased, ``-`` → ``_``).
    2. ``RPC_URL`` — global, network-agnostic.
    3. The preset default.
    """
    if isinstance(network, NetworkConfig):
        return network

    nc = NETWORKS.get(network)
    if nc is None:
        raise ValueError(f"Unknown network: {network}")

    per_network_key = f"RPC_URL_{nc.name.upper().replace('-', '_')}"
    rpc_override = get_env(per_network_key) or get_env("RPC_URL")
    if rpc_override:
        return NetworkConfig(
            name=nc.name,
            chain_id=nc.chain_id,
            rpc_url=rpc_override,
            paymaster_url=nc.paymaster_url,
            use_paymaster=nc.use_paymaster,
            registry_contract=nc.registry_contract,
            commerce_contract=nc.commerce_contract,
            router_contract=nc.router_contract,
            policy_contract=nc.policy_contract,
            explorer_url=nc.explorer_url,
            faucet_url=nc.faucet_url,
            docs_url=nc.docs_url,
        )
    return nc
