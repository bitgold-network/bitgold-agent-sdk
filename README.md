# BitgoldAgent SDK

[![PyPI](https://img.shields.io/pypi/v/bitgold-agent?logo=pypi&logoColor=white&label=bitgold-agent%20%28PyPI%29)](https://pypi.org/project/bitgold-agent/)
[![npm](https://img.shields.io/npm/v/%40bitgold-agent%2Fsdk?logo=npm&label=%40bitgold-agent%2Fsdk%20%28npm%29)](https://www.npmjs.com/package/@bitgold-agent/sdk)
[![Python](https://img.shields.io/pypi/pyversions/bitgold-agent)](https://pypi.org/project/bitgold-agent/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)

BitgoldAgent provides first-class Python and TypeScript SDKs for building on-chain AI agents on Bitgold Network - register identities, negotiate, accept jobs, deliver work, and get paid trustlessly through on-chain escrow.

Both implementations are actively maintained and will be supported in parallel long term. Choose the language that fits your application; they target the same protocols and network deployments, while language-specific wallet and runtime integrations may differ.

The SDK exposes two core capabilities:

- **ERC-8004 (Agent Identity)** - Register your AI agent on-chain with a unique identity token, manage wallets, and make your agent discoverable. Every write self-pays gas in BTG (tBTG on testnet), so fund the wallet first.
- **ERC-8183 (Agentic Commerce)** - A three-layer stack (AgenticCommerce kernel + EvaluatorRouter + OptimisticPolicy) where agents negotiate pricing, accept jobs, deliver work, and settle payment automatically via optimistic settlement.

> The ERC-8004 registry and the ERC-8183 stack (AgenticCommerce / EvaluatorRouter / OptimisticPolicy) are not deployed on Bitgold yet, so the presets carry the zero address: the SDK is API-complete, but on-chain writes need the deployment addresses filled in through `ERC8004_REGISTRY_ADDRESS`, `ERC8183_COMMERCE_ADDRESS`, `ERC8183_ROUTER_ADDRESS`, `ERC8183_POLICY_ADDRESS` (or by editing the presets).

> The SDKs are under active development and may introduce breaking changes. Use them at your own risk.

## SDKs

The Python and TypeScript SDKs live in the same repository and ship independently. Their release versions and channels may differ without changing the long-term support commitment for either language.

| Directory | Language | Package | Current version | Support |
| --- | --- | --- | --- | --- |
| [`python/`](./python) | Python | [`bitgold_agent`](https://pypi.org/project/bitgold-agent/) on PyPI | [![PyPI](https://img.shields.io/pypi/v/bitgold-agent?label=%20)](https://pypi.org/project/bitgold-agent/) | First-class, long-term |
| [`typescript/`](./typescript) | TypeScript | [`@bitgold-agent/sdk`](https://www.npmjs.com/package/@bitgold-agent/sdk) on npm | [![npm](https://img.shields.io/npm/v/%40bitgold-agent%2Fsdk?label=%20)](https://www.npmjs.com/package/@bitgold-agent/sdk) | First-class, long-term |

The two badges above are live: because Python and TypeScript ship independently, they will
often show different numbers. That is expected and does not indicate that either language is
behind — see the release-channel note above.

Shared, language-neutral material lives at the root:

- [`ARCHITECTURE.md`](./ARCHITECTURE.md) - cross-cutting design and protocol overview
- [`docs/`](./docs) - additional documentation
- [`LICENSE`](./LICENSE) - MIT

## Wallets

Every protocol client signs through the `WalletProvider` seam, so the wallet is a construction-time choice. Three backends ship today:

| Wallet | Custody | SDK | Notes |
| --- | --- | --- | --- |
| `EVMWalletProvider` | local key (Keystore V3 on disk) | Python + TypeScript | full signing surface (`sign.message/transaction/typed_data`), optional operator-supplied ERC-4337 paymaster hook |
| `TWAKProvider` | [Trust Wallet Agent Kit](./docs/twak.md) CLI (`twak` >= v0.20.0) | Python + TypeScript | self-broadcasting; ERC-8004/8183 intents + delegated x402; pays gas from its own BTG balance |
| `TurnkeyWalletProvider` | [Turnkey](https://docs.turnkey.com) remote signing — keys live in AWS Nitro enclaves, the agent holds only a P-256 API key | Python + TypeScript | full signing surface; broadcasts self-paid over the SDK's own RPC; every successful signature is billed (free tier 25/month at 1 req/s, PAYG $0.10); production requires a non-root API user + explicit ALLOW policy (root keys bypass all Turnkey policies) |

Details: [`python/bitgold_agent/wallets/README.md`](./python/bitgold_agent/wallets/README.md) (EVM + TWAK + Turnkey), [`typescript/README.md`](./typescript/README.md) (EVM + TWAK + Turnkey), and [`docs/twak.md`](./docs/twak.md).

### Bring your own MPC custody

`mpc` is a recognised wallet kind (`SUPPORTED_WALLET_KINDS = ("evm", "twak", "mpc", "turnkey")`) but is a **stub by design**. The SDK deliberately ships no in-process MPC implementation: threshold-key custody, audit trails, and policy enforcement belong in a dedicated provider (Coinbase CDP, Fireblocks, Web3Auth, and similar), which already solves them at the enclave level.

Selecting it fails loudly rather than falling through silently:

```python
>>> from bitgold_agent.wallets.factory import create_wallet_provider
>>> create_wallet_provider("mpc")
NotImplementedError: MPC wallet support is not yet implemented. Please use EVMWalletProvider for now.
```

To sign through an MPC backend, adapt its API in your own project by subclassing `WalletProvider` (`from bitgold_agent.wallets import WalletProvider`). Implement only the `sign_*` methods your backend supports — `capabilities()` reports the matching `sign.*` entries from your overrides, and anything you leave alone raises a descriptive `UnsupportedWalletOperation`, so never override a method just to raise.

`MPCWalletProvider` is exported for `isinstance` checks and as a subclassing reference, but its `__init__` raises unconditionally — subclass `WalletProvider` directly unless you also override `__init__`.

## Getting started

### Python

```bash
pip install bitgold-agent
```

See [`python/README.md`](./python/README.md) for the full guide: installation, quick starts (register an agent, run an ERC-8183 provider, use the client), configuration reference, and examples.

### TypeScript

```bash
npm install @bitgold-agent/sdk
```

See [`typescript/README.md`](./typescript/README.md) for the full guide: installation, API reference, wallet providers, configuration, and examples.

## Links

- Homepage: https://github.com/bitgold-network/bitgold-agent-sdk
- Issues: https://github.com/bitgold-network/bitgold-agent-sdk/issues
- Standards: [ERC-8004](https://eips.ethereum.org/EIPS/eip-8004) · ERC-8183 (Agentic Commerce)

## Related

- [bitgold-agent-studio-evals](https://github.com/bitgold-network/bitgold-agent-studio-evals) - security evaluation suite for BTG Agent Studio (EMNLP 2026 System Demonstrations artifact). Studio-provisioned agents build their signing layer on this SDK (`bitgold_agent.erc8183`), and the suite evaluates that stack end to end (confused-deputy / prompt-injection). Originally proposed here as [#48](https://github.com/bitgold-network/bitgold-agent-sdk/pull/48), then migrated.

---

## License

[MIT](./LICENSE)
