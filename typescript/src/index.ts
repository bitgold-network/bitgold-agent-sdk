/**
 * BitgoldAgent SDK — TypeScript toolkit for building on-chain AI agents on Bitgold Network.
 *
 * Tier 1 (public API — available via `import { ... } from "@bitgold-agent/sdk"`):
 *     NetworkConfig, NETWORKS, resolveNetwork
 *     BitgoldAgentError, ContractError, StorageError, ConfigurationError,
 *     ABILoadError, NetworkError, RpcRangeLimitError, JobError,
 *     NegotiationError, TransactionPendingError, RelaySubmissionUnverifiedError,
 *     ERC8004PartialRegistrationError
 *     ERC8004Agent, AgentEndpoint
 *     WalletProvider, EVMWalletProvider, TWAKProvider, TurnkeyWalletProvider
 *     ERC8183Client, JobStatus, Verdict
 *     SigningPolicy, PolicyViolation
 *     X402Signer
 *     loadEnv
 *     setMinGasPriceWei, minGasPriceWei, setDefaultReceiptTimeout, getDefaultReceiptTimeout
 *     Paymaster, NonceManager, SCAN_API_URL
 *
 * Tier 2 (import from subpath — full package surface):
 *     import { CommerceClient, RouterClient, PolicyClient, ERC8183JobOps, fundedJobWatcher } from "@bitgold-agent/sdk/erc8183";
 *     import { AgentURIGenerator, ContractInterface, getErc8004Config } from "@bitgold-agent/sdk/erc8004";
 *     import { SessionBudgetTracker, X402SignerError } from "@bitgold-agent/sdk/x402";
 *     import { LocalStorageProvider, IPFSStorageProvider } from "@bitgold-agent/sdk/storage";
 *     import { LocalExecutor, UnsupportedWalletOperation } from "@bitgold-agent/sdk/wallets";
 *     import { check, EIP3009_TYPES } from "@bitgold-agent/sdk/signing";
 *     import { getAddress, BITGOLD_CHAIN_ADDRESSES } from "@bitgold-agent/sdk/networks";
 *     import { SlidingWindowLimiter, RateLimitExceeded, type RateLimiter } from "@bitgold-agent/sdk/utils";
 *
 * Mirrors `python/bitgold_agent/__init__.py`'s Tier 1 surface; see
 * `ARCHITECTURE.md` for the full protocol/module reference.
 */

// Configuration
export { type NetworkConfig, NETWORKS, resolveNetwork } from "./config.js";

// Exceptions
export {
  BitgoldAgentError,
  ContractError,
  StorageError,
  ConfigurationError,
  ABILoadError,
  NetworkError,
  RpcRangeLimitError,
  JobError,
  JobPaymentTokenMismatchError,
  NegotiationError,
  TransactionPendingError,
  RelaySubmissionUnverifiedError,
  RelayFallbackFailedError,
  RelayRejectedError,
  ERC8004PartialRegistrationError,
} from "./errors.js";
export type { RelayObservationStatus } from "./errors.js";

// Relay observability — secondary confirmation of unseen relay hashes
export {
  confirmTxUnseen,
  resolveFallbackRpcUrls,
} from "./core/relayVerifier.js";
export type {
  RelayVerifierOpts,
  SecondaryConfirmation,
  TxPresenceProbe,
  TxProbeResult,
} from "./core/relayVerifier.js";

// ERC-8004 Identity Registry
export { ERC8004Agent } from "./erc8004/agent.js";
export { AgentEndpoint } from "./erc8004/models.js";

// Wallets
export { WalletProvider } from "./wallets/walletProvider.js";
export { EVMWalletProvider } from "./wallets/evmWalletProvider.js";
// Self-broadcasting TWAK (Trust Wallet Agent Kit CLI) wallet — twak is an
// npm CLI; install @trustwallet/cli and the provider finds the local bin.
export { TWAKProvider } from "./wallets/twak/index.js";
// Pure-signer Turnkey wallet (remote signing, keys in AWS Nitro enclaves).
// The backing @turnkey/* peers are optional and loaded lazily on first use.
export { TurnkeyWalletProvider } from "./wallets/turnkey/index.js";

// ERC-8183 — only essential public API
export { ERC8183Client } from "./erc8183/client.js";
export type { TokenMetadata, TokenReference } from "./erc8183/client.js";
export { JobStatus, Verdict } from "./erc8183/types.js";

// Signing policy
export { SigningPolicy } from "./signing/policy.js";
export { PolicyViolation } from "./signing/errors.js";

// x402 payment signer
export { X402Signer } from "./x402/signer.js";

// Opt-in .env loading (never called at import time — applications opt in)
export { loadEnv } from "./core/env.js";

// Transaction tuning (gas-price floor + receipt timeout) — public knobs that
// replace any downstream monkey-patching of SDK internals.
export {
  setMinGasPriceWei,
  minGasPriceWei,
  setDefaultReceiptTimeout,
  getDefaultReceiptTimeout,
  setRelayUnseenTimeout,
  getRelayUnseenTimeout,
} from "./core/txConfig.js";

// Paymaster + nonce management
export { Paymaster } from "./core/paymaster.js";
export { NonceManager } from "./core/nonceManager.js";

// Shared constants
export { SCAN_API_URL } from "./constants.js";
