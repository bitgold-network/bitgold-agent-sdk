# @bitgold-agent/sdk

[![npm](https://img.shields.io/npm/v/%40bitgold-agent%2Fsdk?logo=npm&label=%40bitgold-agent%2Fsdk)](https://www.npmjs.com/package/@bitgold-agent/sdk)
[![Node](https://img.shields.io/node/v/%40bitgold-agent%2Fsdk)](https://www.npmjs.com/package/@bitgold-agent/sdk)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](../LICENSE)

TypeScript toolkit for building on-chain AI agents on Bitgold Network: ERC-8004 identity, the ERC-8183 agentic-commerce protocol (escrow + evaluation + optimistic dispute policy), x402 micropayments, wallets (local keystore + pluggable executors), and the supporting core (nonce management, optional paymaster hook, tx tuning).

This is a layered port of the reference [Python SDK](../python) - same protocol semantics, same on-chain deployments, idiomatic TypeScript API. See [`ARCHITECTURE.md`](../ARCHITECTURE.md) for the full protocol reference; this README covers the TypeScript-specific surface and quickstart.

## Install

```bash
pnpm add @bitgold-agent/sdk
# or
npm install @bitgold-agent/sdk
```

Requires Node.js >= 20. The package ships both ESM (`import`) and CommonJS (`require`) builds plus TypeScript types.

## Package layout

The public API is split into a small **Tier 1** barrel (the handful of names most integrations need) and **Tier 2** subpath exports (each protocol module's full surface):

```ts
// Tier 1 - the essentials
import { ERC8183Client, EVMWalletProvider, JobStatus } from "@bitgold-agent/sdk";

// Tier 2 - full module surface, imported by subpath
import {
  ERC8183JobOps,
  fundedJobWatcher,
  CommerceClient,
} from "@bitgold-agent/sdk/erc8183";
import { ERC8004Agent, AgentURIGenerator } from "@bitgold-agent/sdk/erc8004";
import { X402Signer, SessionBudgetTracker } from "@bitgold-agent/sdk/x402";
import {
  LocalStorageProvider,
  IPFSStorageProvider,
} from "@bitgold-agent/sdk/storage";
import {
  LocalExecutor,
  UnsupportedWalletOperation,
} from "@bitgold-agent/sdk/wallets";
import { SigningPolicy, check } from "@bitgold-agent/sdk/signing";
import { getAddress, BITGOLD_CHAIN_ADDRESSES } from "@bitgold-agent/sdk/networks";
import { SlidingWindowLimiter, RateLimitExceeded } from "@bitgold-agent/sdk/utils";
```

Subpaths available: `./erc8004`, `./erc8183`, `./x402`, `./storage`, `./wallets`, `./signing`, `./networks`, `./utils`.

The TypeScript signing checker supports nested EIP-712 structs when their
dependency graph has one unambiguous root. Arrays of structs are supported;
ambiguous, disconnected and cyclic multi-struct graphs are rejected. This enables
explicitly opted-in Permit2 `PermitWitnessTransferFrom` requests through the
public wallet API. The normal primary-type/domain allowlists, denylist and
validity checks still run: nested signing does not grant a new payment permission.
Every schema, single- or multi-struct, is validated before signing: struct and
field names must be Solidity identifiers, field types must be EIP-712 atomic
types (no `uint`/`int` aliases) or declared structs, optionally as arrays, and
schemas are limited to 256 structs, 4096 total fields, depth 64 and
256-character identifiers. Violations raise `PolicyViolation` before signing.

Explicitly allowing a Permit2 domain and primary type is not a payment budget.
The generic SDK policy does not pin Permit2 witness schemas, spenders, token
amounts, recipients or `deadline` bounds. The trusted payment integration must
validate those values before calling the wallet; never forward untrusted raw
typed data after merely adding Permit2 to the allowlist.

## Quickstart

Both snippets assume a funded wallet on `bitgold-testnet` (get test BTG from the [Bitgold Network faucet](https://faucet.bitgold.network)) and an `.env` populated per the [environment variables](#environment-variables) table below. Call `loadEnv()` once at your entrypoint to load `.env`/`.env.local` (the SDK never does this for you - see its docstring for the precedence rules).

The ERC-8004 registry, the ERC-8183 stack and the BTG ERC-20 payment token are not deployed on Bitgold yet, so the presets carry the zero address: fill in `ERC8004_REGISTRY_ADDRESS` / `ERC8183_COMMERCE_ADDRESS` / `ERC8183_ROUTER_ADDRESS` / `ERC8183_POLICY_ADDRESS` (or edit the presets) before any on-chain call.

### (a) Client-side job lifecycle

The client creates a job, binds the on-chain dispute policy, funds escrow, and - once the provider submits - settles the job (permissionless: it just pulls the policy's verdict and applies it on-chain).

```ts
import {
  loadEnv,
  EVMWalletProvider,
  ERC8183Client,
  JobStatus,
} from "@bitgold-agent/sdk";

loadEnv(); // opt-in .env / .env.local loading

const wallet = new EVMWalletProvider({
  password: process.env.WALLET_PASSWORD!,
  // First run only - the SDK encrypts it to ~/.bitgold-agent/wallets/<address>.json
  // and subsequent runs only need the password.
  privateKey: process.env.PRIVATE_KEY,
});

const client = await ERC8183Client.create({
  walletProvider: wallet,
  network: "bitgold-testnet",
});

const decimals = await client.tokenDecimals();
const budget = 1n * 10n ** BigInt(decimals); // 1 token

// expiredAt must clear (disputeWindow + a safety buffer) or createJob()
// throws - a job whose deadline is too close can never be submitted.
const disputeWindow = await client.policy.disputeWindow();
const expiredAt = BigInt(Math.floor(Date.now() / 1000)) + disputeWindow + 600n; // +10 min slack

const { jobId } = await client.createJob({
  provider: process.env.PROVIDER_ADDRESS!,
  expiredAt,
  description: "ERC-8183 demo: summarize this week's Bitgold ecosystem news",
});
console.log(`[client] createJob jobId=${jobId}`);

// Bind the OptimisticPolicy so settle() has a verdict source.
await client.registerJob(jobId!);

// Escrow the budget - auto-approves the payment token if the allowance is short.
// Zero price: for a free job either party calls `setBudget(jobId, 0n)`,
// then `fund(jobId, 0n)` moves no tokens and skips the ERC-20 approve
// entirely. See examples/client/zeroPrice.ts.
await client.fund(jobId!, budget);
console.log("[client] fund OK (Open -> Funded)");

// ... provider calls jobOps.submitResult() / client.submit() here (see below) ...

// After the dispute window elapses with no rejection, settle() finalizes
// the job as COMPLETED (or REJECTED if the policy recorded a reject vote).
await client.settle(jobId!);
const job = await client.getJob(jobId!);
console.log(`[client] settle -> ${JobStatus[job.status]}`);
```

### (b) Provider earn loop

A headless provider agent polls for jobs funded to its address and submits a deliverable for each one. `ERC8183JobOps` handles verification (status, assignment, expiry, budget floor) and deliverable upload; `fundedJobWatcher` is a signer-free polling loop - it only _detects_ funded jobs, so the callback decides what to do (including delegating signing elsewhere).

```ts
import { EVMWalletProvider } from "@bitgold-agent/sdk";
import { ERC8183JobOps, fundedJobWatcher } from "@bitgold-agent/sdk/erc8183";
import { LocalStorageProvider } from "@bitgold-agent/sdk/storage";

const wallet = new EVMWalletProvider({
  password: process.env.WALLET_PASSWORD!,
});

const jobOps = await ERC8183JobOps.create({
  walletProvider: wallet,
  network: "bitgold-testnet",
  storageProvider: new LocalStorageProvider(".agent-data"),
  servicePrice: 1n * 10n ** 18n, // reject jobs budgeted below 1 token (18 decimals)
  agentUrl: process.env.ERC8183_AGENT_URL, // public base URL, used as a deliverable-URL fallback
});

await fundedJobWatcher(
  jobOps,
  async (job) => {
    const jobId = job.jobId as number;
    console.log(`[earn-loop] job ${jobId} funded, budget=${job.budget}`);

    const result = await jobOps.submitResult(
      jobId,
      `computed result for job ${jobId}`,
      { model: "my-model-v1" },
    );
    if (!result.success) {
      console.error(`[earn-loop] submit(${jobId}) failed: ${result.error}`);
      // Returning { retry: true } asks the watcher to re-validate and
      // re-fire this job on the next tick (only for transient failures).
      return { retry: result.retryable === true };
    }
    console.log(`[earn-loop] submitted ${jobId}, tx=${result.txHash}`);
  },
  { interval: 30 }, // seconds between polls
);
```

## Wallet providers

Every protocol client signs through the `WalletProvider` seam - swap the provider, keep the protocol code:

|  | `EVMWalletProvider` | `TWAKProvider` | `TurnkeyWalletProvider` |
| --- | --- | --- | --- |
| Custody | local key, Keystore V3 on disk | [twak CLI](../docs/twak.md) keystore (`~/.twak`) + OS keychain; the key never enters this process | key generated + held in [Turnkey](https://docs.turnkey.com)'s AWS Nitro enclave, never leaves it; the agent holds only a local P-256 API key that stamps each request |
| Capabilities | `sign.message/transaction/typed_data`, `calls.arbitrary`, `paymaster.sponsor` | `sign.message`, `broadcast.self`, `intents.erc8004`, `intents.erc8183` (no raw signing, no `x402.pay` until `requestExact` exists) | `sign.message/transaction/typed_data`, `calls.arbitrary`, `paymaster.sponsor` (same surface as EVM, remote signer) |
| Agent containment | `SigningPolicy` (in-process) | fixed command menu + out-of-process custody; twak's own `--max-payment` hard cap | `SigningPolicy` (in-process, pre-billing) + Turnkey's server-side policy engine — **root API keys bypass the server layer entirely; production needs a non-root API user + explicit ALLOW policy** |
| Gas | self-paid in BTG (no sponsorship on Bitgold; `paymaster.sponsor` is a hook for operators wiring their own ERC-4337 paymaster) | self-paid from the twak wallet's own BTG balance - pre-fund it | self-paid (broadcast is always the SDK's own RPC; Turnkey's managed broadcast is a paid feature the provider never uses) |
| ERC-8183 quote signing | EIP-191 via `walletProvider` | - | EIP-191 via `walletProvider` (1 billed signature per quote) |
| x402 payments | `X402Signer` | Delegated `TwakX402Payer` (`makeX402Payer()`, five-point quote precheck) | `X402Signer` — works, but $0.10/signature (PAYG) at 1 req/s makes high-frequency buying uneconomical; seller/low-frequency signing is the sweet spot |
| Extra install | - | `npm i @trustwallet/cli` (>= 0.20.0; the local `node_modules/.bin/twak` is auto-resolved) | `pnpm add @turnkey/sdk-server @turnkey/viem` (optional peers, lazily imported) |

Turnkey quick start (remote enclave signing; every successful signature is billed — free tier 25/month at 1 request/second, pay-as-you-go $0.10/signature):

```ts
import { TurnkeyWalletProvider } from "@bitgold-agent/sdk/wallets";

// env: TURNKEY_API_PUBLIC_KEY / TURNKEY_API_PRIVATE_KEY / TURNKEY_ORG_ID /
//      TURNKEY_SIGN_WITH (the wallet account's 0x ADDRESS, not a wallet id)
const wallet = TurnkeyWalletProvider.fromEnv({ expectedChainId: 617 });

const jobs = await ERC8183Client.create({
  walletProvider: wallet,
  network: "bitgold-testnet",
});
```

The provider is a pure signer: ERC-8004/8183 writes ride the default `LocalExecutor`, x402 rides `X402Signer`, and every write self-pays gas in BTG over the SDK's own RPC. All SDK-side guards — `SigningPolicy`, the `expectedChainId` pin, input validation — run *before* the billable API call, so a refusal never costs quota. One vendor quirk is patched inside `signTypedData`: `@turnkey/viem` <= 0.14.34 silently serializes the EIP-712 domain as `{}` when the `types` object lacks an explicit `EIP712Domain` entry, so the provider always injects it (the signature would otherwise bind an empty domain). Live verification: `TURNKEY_E2E=1 pnpm run e2e:turnkey` (5 billed signatures; see `examples/turnkey/e2e.ts`).

Negotiation quotes default to the maximum SDK lifetime of 900 seconds (and are shortened further when the wallet expires sooner). Provider-side `ERC8183JobOps` requires a valid signed quote by default and verifies it at the indexed `JobFunded` block before doing work or submitting. Buyer edits, signature removal, late funding, and provider/chain/Commerce mismatches are permanent `quote_invalid` rejections. `allowUnsignedJobs: true` is an explicit unsafe compatibility mode for pre-signature jobs.

### Relay submission verification

For local EVM signing through an operator-supplied ERC-4337 paymaster, a forwarded transaction hash must become visible to the chain before the SDK trusts it. If the primary RPC never sees the hash, the SDK asks fallback RPCs from distinct origins. A same-nonce self-pay is allowed only when at least two origins agree the relay transaction is absent; two agreeing that it is present suppress the fallback, and every weaker or conflicting result fails closed with `RelaySubmissionUnverifiedError`. Custom `BITGOLD_AGENT_FALLBACK_RPC_URLS` remain supported, but entries that share an origin count as one source. Custom endpoints form part of the operator's trust boundary: choose independently operated origins, because an operator-supplied quorum can authorize the fallback. `BITGOLD_AGENT_USE_PAYMASTER` is unset by default - every write self-pays gas in BTG - and is only a hook for operators wiring their own ERC-4337 paymaster.

`EVMWalletProvider` does not retain its construction password. Pass a password
explicitly to `exportKeystore(password)`, and call `destroy()` when local
signing is finished. The live private key necessarily remains in process
memory until then; use a remote or scoped wallet backend for higher-value
deployments.

## Environment variables

None of these are read automatically - call `loadEnv()` (from `@bitgold-agent/sdk`) at your entrypoint to load `.env.local` then `.env`, or set them however your deployment normally injects environment variables. See [`.env.example`](../.env.example) at the repo root for the authoritative, fully-commented reference.

| Variable | Used by | Notes |
| --- | --- | --- |
| `NETWORK` | `resolveNetwork` | Preset name: `bitgold-testnet` (default) or `bitgold-mainnet`. |
| `RPC_URL` / `RPC_URL_<NETWORK>` | `resolveNetwork` | Override the preset RPC endpoint; per-network var wins. |
| `WALLET_PASSWORD` | `EVMWalletProvider` | Required for the EVM backend. Encrypts/decrypts the local Keystore V3 file; unused by TWAK. |
| `PRIVATE_KEY` | `EVMWalletProvider` | EVM backend, first run only - imported then encrypted to disk; remove afterward. |
| `WALLET_ADDRESS` | `EVMWalletProvider` | Disambiguates which keystore to load when several exist. |
| `WALLET_KIND` | `ERC8183Config.fromEnv` | `evm` (default) or `twak`; TWAK owns its custody and does not use `PRIVATE_KEY`/`WALLET_PASSWORD`. |
| `ERC8183_COMMERCE_ADDRESS` | `getErc8183Config` | Override the AgenticCommerce kernel address (custom deployments only). |
| `ERC8183_ROUTER_ADDRESS` | `getErc8183Config` | Override the EvaluatorRouter address. |
| `ERC8183_POLICY_ADDRESS` | `getErc8183Config` | Override the OptimisticPolicy address. |
| `ERC8183_SERVICE_PRICE` | `ERC8183Config` / `ERC8183JobOps` | Minimum job budget (raw token units) a provider accepts. |
| `ERC8183_AGENT_URL` | `ERC8183JobOps` | Public base URL for the agent; fallback deliverable-URL host. |
| `ERC8183_FUNDED_POLL_INTERVAL` | agent-server examples | Poll interval (seconds) for the funded-job scan. |
| `ERC8183_MAX_RESPONSE_BYTES` / `ERC8183_MAX_METADATA_BYTES` | `ERC8183JobOps.submitResult` | Per-deliverable upload size caps. |
| `ERC8004_REGISTRY_ADDRESS` | `getErc8004Config` | Override the Identity Registry address. |
| `STORAGE_LOCAL_PATH` | `LocalStorageProvider.fromEnv` | Base directory for local storage. |
| `STORAGE_API_KEY` | `IPFSStorageProvider.fromEnv` | Required Pinata-compatible JWT. |
| `STORAGE_API_URL` / `STORAGE_GATEWAY_URL` | `IPFSStorageProvider` | Optional custom pin endpoint / gateway. |
| `BITGOLD_AGENT_MIN_GAS_PRICE_WEI` | `minGasPriceWei` | Global gas-price floor override (wei), all chains. |
| `BITGOLD_AGENT_RECEIPT_TIMEOUT` | `getDefaultReceiptTimeout` | Default transaction-receipt wait, in seconds. |
| `BITGOLD_AGENT_USE_PAYMASTER` | paymaster hook | Unset by default (every write self-pays gas in BTG); `1` enables an operator-supplied ERC-4337 paymaster, `0` forces self-pay. |
| `BITGOLD_AGENT_RELAY_UNSEEN_TIMEOUT` | `getRelayUnseenTimeout` | Seconds an unseen paymaster-forwarded hash may remain invisible before fallback handling; `0` disables the early abort. |
| `BITGOLD_AGENT_FALLBACK_RPC_URLS` | relay verifier | Comma-separated RPC endpoints used to confirm whether a relay-returned hash is unseen; overrides the built-in Bitgold endpoint list. A decisive result requires two distinct URL origins. |

## Parity with the Python SDK

This package mirrors [`python/bitgold_agent`](../python/bitgold_agent) module-for-module - same contract addresses, same protocol invariants, same env var names. For protocol-level detail (the ERC-8183 state machine, negotiation handshake, x402 payment flow, signing-policy threat model, wallet capability model), see [`ARCHITECTURE.md`](../ARCHITECTURE.md) and the Python package's own `README.md` files under `python/bitgold_agent/*/README.md` - those docs are protocol reference, not Python-specific, and apply equally here.
