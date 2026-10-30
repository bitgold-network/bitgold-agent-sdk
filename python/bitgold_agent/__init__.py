"""
BitgoldAgent SDK — Python toolkit for building on-chain AI agents on Bitgold Network.

Tier 1 (public API — available via ``from bitgold_agent import ...``):
    NetworkConfig, BitgoldAgentError
    ERC8004Agent, AgentEndpoint
    WalletProvider, EVMWalletProvider
    ERC8183Client, JobStatus, Verdict
    SigningPolicy, PolicyViolation
    X402Signer
    load_env
    set_default_receipt_timeout, get_default_receipt_timeout, set_min_gas_price_wei

Tier 2 (import from subpackage):
    from bitgold_agent.erc8183 import (
        CommerceClient, RouterClient, PolicyClient, NegotiationHandler,
    )
    from bitgold_agent.erc8183 import ERC8183JobOps, funded_job_watcher
    from bitgold_agent.erc8183.config import ERC8183Config
    from bitgold_agent.utils import SlidingWindowLimiter, RateLimitExceeded
    from bitgold_agent.core import create_web3
    from bitgold_agent.erc20 import MinimalERC20Client, load_erc20_abi
    from bitgold_agent.storage import LocalStorageProvider, IPFSStorageProvider
    from bitgold_agent.networks import get_address, BITGOLD_CHAIN_ADDRESSES
    from bitgold_agent.signing import check, EIP3009_TYPES, PERMIT_UNBOUNDED_TYPES
    from bitgold_agent.x402 import SessionBudgetTracker, X402SignerError
"""

from __future__ import annotations

from ._version import __version__

# Configuration
from .config import NetworkConfig

# Transaction tuning (gas-price floor + receipt timeout) — public knobs that
# replace any downstream monkey-patching of SDK internals.
from .core.contract_mixin import (
    get_default_receipt_timeout,
    set_default_receipt_timeout,
    set_min_gas_price_wei,
)

# Opt-in .env loading (never called at import time — applications opt in)
from .core.env import load_env

# ERC-8004 Identity Registry
from .erc8004 import AgentEndpoint, ERC8004Agent

# ERC-8183 — only essential public API
from .erc8183 import (
    ERC8183Client,
    JobPaymentTokenMismatchError,
    JobStatus,
    TokenMetadata,
    Verdict,
)

# Exceptions
from .exceptions import (
    BitgoldAgentError,
    ERC8004PartialRegistrationError,
    RelaySubmissionUnverifiedError,
    TransactionPendingError,
)

# Signing policy
from .signing import PolicyViolation, SigningPolicy

# Wallets
from .wallets import EVMWalletProvider, WalletProvider

# x402 payment signer
from .x402 import X402Signer

__all__ = [
    # Core
    "__version__",
    "NetworkConfig",
    "BitgoldAgentError",
    "TransactionPendingError",
    "RelaySubmissionUnverifiedError",
    "ERC8004PartialRegistrationError",
    "load_env",
    # Transaction tuning
    "set_default_receipt_timeout",
    "get_default_receipt_timeout",
    "set_min_gas_price_wei",
    # ERC-8004
    "ERC8004Agent",
    "AgentEndpoint",
    # Wallets
    "WalletProvider",
    "EVMWalletProvider",
    # ERC-8183
    "ERC8183Client",
    "JobStatus",
    "Verdict",
    "TokenMetadata",
    "JobPaymentTokenMismatchError",
    # Signing policy
    "SigningPolicy",
    "PolicyViolation",
    # x402 payment signer
    "X402Signer",
]
