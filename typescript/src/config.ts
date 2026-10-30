/**
 * Top-level SDK configuration.
 *
 * Exports:
 *
 * - {@link NetworkConfig} — per-network defaults (RPC endpoint, explorer and
 *   contract addresses for every module that uses on-chain state).
 * - {@link resolveNetwork} — looks up a preset by name, with an optional
 *   `RPC_URL` env override. **Module-specific contract overrides live in
 *   their own module configs**, not here.
 *
 * Env var surface
 * ---------------
 * `resolveNetwork` reads only two env families: the `RPC_URL` overrides
 * (`RPC_URL` / `RPC_URL_<NETWORK>`) and the tri-state paymaster toggle
 * `BITGOLD_AGENT_USE_PAYMASTER` (`"1"` force on, `"0"` force off, unset =
 * inherit the preset). Module-scoped env vars are owned by the corresponding
 * module config. The project-root `.env.example` is the authoritative
 * reference.
 *
 * Contract addresses ship as zero-address placeholders: the Bitgold Network
 * deployments of the ERC-8004 registry and the ERC-8183 stack are not
 * published yet. Point the `ERC8004_REGISTRY_ADDRESS` / `ERC8183_*_ADDRESS`
 * env vars — or edit the presets below — once they are.
 */

import { getEnv } from "./core/envUtil.js";

/** Placeholder used until the Bitgold Network deployments are published. */
export const ZERO_ADDRESS = "0x0000000000000000000000000000000000000000" as const;

/** Bitgold Mainnet / testnet chain ids. */
export const BITGOLD_MAINNET_CHAIN_ID = 618;
export const BITGOLD_TESTNET_CHAIN_ID = 617;

/**
 * Per-network configuration with ALL protocol addresses.
 *
 * ERC-8183 is a three-contract stack: AgenticCommerce kernel (escrow),
 * EvaluatorRouter (routing + hook), and OptimisticPolicy (silence-approves,
 * vote-rejects). Payment token is NOT configured here — it is immutable on
 * the Commerce kernel and read at runtime via `ERC8183Client.paymentToken`.
 *
 * Bitgold has no gas-sponsorship relay: `paymasterUrl` is unset and
 * `usePaymaster` is `false` (writes self-pay gas in BTG). Both fields stay so
 * an operator can wire their own ERC-4337 paymaster later.
 */
export interface NetworkConfig {
  name: string;
  chainId: number;
  rpcUrl: string;
  paymasterUrl?: string;
  usePaymaster: boolean;
  /** ERC-8004 Identity Registry */
  registryContract: string;
  /** ERC-8183 stack */
  commerceContract: string;
  routerContract: string;
  policyContract: string;
  /** Human-facing endpoints (documentation / tooling convenience). */
  explorerUrl?: string;
  faucetUrl?: string;
  docsUrl?: string;
}

export const NETWORKS: Record<string, NetworkConfig> = {
  "bitgold-testnet": {
    name: "bitgold-testnet",
    chainId: BITGOLD_TESTNET_CHAIN_ID,
    rpcUrl: "https://testnet1.bitgold.network",
    // No gas sponsorship on Bitgold: every write self-pays in BTG, so a fresh
    // agent needs a small BTG balance from the faucet before it can register.
    usePaymaster: false,
    registryContract: ZERO_ADDRESS,
    commerceContract: ZERO_ADDRESS,
    routerContract: ZERO_ADDRESS,
    policyContract: ZERO_ADDRESS,
    explorerUrl: "https://testnet.bitgold.live",
    faucetUrl: "https://faucet.bitgold.network",
    docsUrl: "https://docs.bitgold.network",
  },
  "bitgold-mainnet": {
    name: "bitgold-mainnet",
    chainId: BITGOLD_MAINNET_CHAIN_ID,
    rpcUrl: "https://rpc.bitgold.network",
    usePaymaster: false,
    registryContract: ZERO_ADDRESS,
    commerceContract: ZERO_ADDRESS,
    routerContract: ZERO_ADDRESS,
    policyContract: ZERO_ADDRESS,
    explorerUrl: "https://www.bitgold.live",
    docsUrl: "https://docs.bitgold.network",
  },
};

/**
 * Resolve a network preset to a concrete `NetworkConfig`.
 *
 * Accepts either a preset name (`"bitgold-testnet"` / `"bitgold-mainnet"`) or a
 * concrete `NetworkConfig` instance:
 *
 * - **String** → look up the preset; apply the RPC env override if set.
 *   Module-scoped contract-address envs are NOT read here — they belong to
 *   each module's own config loader.
 * - **NetworkConfig** → returned as-is; env vars are never applied (fully
 *   explicit control is the point of passing an object).
 *
 * RPC override precedence (a process that touches several networks needs
 * per-network pins — a single shared URL would silently apply to the wrong
 * chain):
 *
 * 1. `RPC_URL_<NETWORK>` — per-network, e.g. `RPC_URL_BITGOLD_TESTNET` /
 *    `RPC_URL_BITGOLD_MAINNET` (preset name uppercased, `-` → `_`).
 * 2. `RPC_URL` — global, network-agnostic.
 * 3. The preset default.
 *
 * `usePaymaster` precedence, independent of the RPC one:
 *
 * 1. `BITGOLD_AGENT_USE_PAYMASTER` — explicit tri-state escape hatch, wins over
 *    everything.
 * 2. A loopback RPC override (`localhost` / `127.0.0.1` / `[::1]`) forces it
 *    off — a local dev node is never behind a hosted relay.
 * 3. The preset's own value (off by default on Bitgold).
 */
export function resolveNetwork(
  network: string | NetworkConfig = "bitgold-testnet",
): NetworkConfig {
  if (typeof network !== "string") {
    return network;
  }

  const nc = NETWORKS[network];
  if (nc === undefined) {
    throw new Error(`Unknown network: ${network}`);
  }

  const perNetworkKey = `RPC_URL_${nc.name.toUpperCase().replace(/-/g, "_")}`;
  const rpcOverride = getEnv(perNetworkKey) ?? getEnv("RPC_URL");
  const envPaymaster = paymasterEnvOverride();

  if (rpcOverride) {
    const usePaymaster =
      envPaymaster ?? (isLocalRpcUrl(rpcOverride) ? false : nc.usePaymaster);
    return { ...nc, rpcUrl: rpcOverride, usePaymaster };
  }

  if (envPaymaster !== undefined && envPaymaster !== nc.usePaymaster) {
    return { ...nc, usePaymaster: envPaymaster };
  }
  return nc;
}

/**
 * Tri-state read of `BITGOLD_AGENT_USE_PAYMASTER`: `"1"` → `true`, `"0"` → `false`,
 * unset/empty → `undefined` (inherit). Any other value is ignored with a
 * warning so a typo never silently flips gas sponsorship.
 */
function paymasterEnvOverride(): boolean | undefined {
  const raw = getEnv("BITGOLD_AGENT_USE_PAYMASTER");
  if (raw === undefined) return undefined;
  if (raw === "1") return true;
  if (raw === "0") return false;
  console.warn(
    `[resolveNetwork] ignoring BITGOLD_AGENT_USE_PAYMASTER='${raw}' — expected '0' or '1'.`,
  );
  return undefined;
}

/**
 * True when `url`'s host is loopback (any scheme/port). Unparseable URLs are
 * treated as non-local.
 */
function isLocalRpcUrl(url: string): boolean {
  let host: string;
  try {
    host = new URL(url).hostname;
  } catch {
    return false;
  }
  return (
    host === "localhost" ||
    host === "127.0.0.1" ||
    host === "[::1]" ||
    host === "::1"
  );
}
