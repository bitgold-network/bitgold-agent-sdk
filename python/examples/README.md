# Examples

End-to-end examples for ERC-8183 (AgenticCommerce + EvaluatorRouter + OptimisticPolicy).

## Directory layout

| Example | Role | Description |
| --- | --- | --- |
| [client/](client/) | Client | Stand-alone scripts that walk a job through each of the five canonical flows (happy path, dispute-reject, stalemate-expire, never-submit, cancel-open) |
| [voter/](voter/) | Voter | Whitelisted voter casting `voteReject` on disputed jobs |
| [a2a-agent/](a2a-agent/) | Provider (A2A) | **The recommended serving direction**: A2A agent card + `message/send` fronting SDK negotiation, with ERC-8004 discovery via `AgentEndpoint.a2a()` and a buyer counterpart |
| [agent-server/](agent-server/) | Provider (HTTP) | Self-contained HTTP serving reference: the FastAPI factory lives in `src/erc8183_server.py` (copy the directory and own it), funded-job poll loop, three storage backends |
| [twak/](twak/) | Wallet | TWAK wallet: hermetic quickstart (custody + capabilities + guard rails), delegated x402 payer demo, bitgold-testnet 13-intent smoke |
| [x402/](x402/) | Buyer | x402 micropayment buyer flow against a mock 402 server |
| [security/](security/) | Security | Defense-in-depth signing validation (assert-chain e2e) |

The SDK itself ships **no serving runtime** - how an agent faces the world (A2A, MCP, plain HTTP) is an application choice. These examples are the reference implementations of those choices; the SDK provides the headless primitives (`ERC8183JobOps`, `funded_job_watcher`, `NegotiationHandler`) and the ERC-8004 registration constructors (`AgentEndpoint.a2a()` / `.mcp()`).

## Recommended path

```
1. client/      → learn createJob → registerJob → setBudget → fund → submit → settle
2. voter/       → understand dispute quorum
3. a2a-agent/   → serve quotes over A2A + register discoverable identity (ERC-8004)
4. agent-server → run a full HTTP provider with the funded-job poll loop
5. twak/        → swap the client wallet for twak custody (also: WALLET_KIND=twak in client/)
```

## Prerequisites

- Python 3.10+
- Testnet BTG ([faucet](https://faucet.bitgold.network))
- `uv sync` or `pip install bitgold-agent`
- Some of the deployed payment token (default: U, see address below)
- TWAK examples (`twak/`, or `WALLET_KIND=twak` in `client/`) additionally need the twak CLI: `npm i -g @trustwallet/cli` (>= 0.20.0)

## Bitgold Testnet addresses (SDK defaults)

| Contract                     | Address                                      |
| ---------------------------- | -------------------------------------------- |
| AgenticCommerce (kernel)     | `0x0000000000000000000000000000000000000000` |
| EvaluatorRouter              | `0x0000000000000000000000000000000000000000` |
| OptimisticPolicy             | `0x0000000000000000000000000000000000000000` |
| Identity Registry (ERC-8004) | `0x0000000000000000000000000000000000000000` |

Payment token address is fetched at runtime via `ERC8183Client.payment_token`.
