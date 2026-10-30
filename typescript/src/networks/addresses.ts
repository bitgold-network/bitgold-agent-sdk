/**
 * On-chain address registry for Bitgold Network deployments.
 *
 * Source of truth for the BTG payment-token deployment plus the surrounding
 * commerce/router/policy proxies on `bitgold-testnet` (617) and
 * `bitgold-mainnet` (618).
 *
 * The ERC-8004 / ERC-8183 deployments on Bitgold Network are not published
 * yet, so every entry below is the zero-address placeholder. Fill this
 * manifest once the contracts are deployed — the SDK then treats them exactly
 * like any other deployment (direct-call targets, EIP-712 verifying contract).
 *
 * Only `paymentToken` is an EIP-712 verifyingContract (EIP-3009
 * `TransferWithAuthorization`). The remaining addresses are direct-call
 * targets and are exposed here purely as a lookup convenience — they are
 * **not** added to any signing allowlist by default.
 */

import { getAddress as toChecksumAddress } from "viem";

// ── Chain ids ────────────────────────────────────────────────────────────

export const BITGOLD_MAINNET_CHAIN_ID = 618;
export const BITGOLD_TESTNET_CHAIN_ID = 617;

// ── EIP-712 domain metadata for the payment token ────────────────────────
// Bitgold's payment asset is BTG (18 decimals, native). ERC-8183 escrow needs
// an ERC-20 surface, so the on-chain payment token is the BTG ERC-20
// deployment; replace these values with the verified domain once it exists.

export const PLACEHOLDER_TOKEN_ADDRESS =
  "0x000000000000000000000000000000000000B706" as const;

export const PAYMENT_TOKEN_EIP712_NAME = "BTG";
export const PAYMENT_TOKEN_EIP712_VERSION = "1";

/** Placeholder used until the Bitgold Network deployments are published. */
export const ZERO_ADDRESS = "0x0000000000000000000000000000000000000000" as const;

/** Snapshot of one network's contract deployment. */
export interface DeployedAddresses {
  readonly paymentToken: `0x${string}`;
  readonly treasury: `0x${string}`;
  readonly commerceProxy: `0x${string}`;
  readonly commerceImpl: `0x${string}`;
  readonly routerProxy: `0x${string}`;
  readonly routerImpl: `0x${string}`;
  readonly policy: `0x${string}`;
}

type RawAddresses = Record<keyof DeployedAddresses, string>;

const PLACEHOLDER: RawAddresses = {
  paymentToken: PLACEHOLDER_TOKEN_ADDRESS,
  treasury: ZERO_ADDRESS,
  commerceProxy: ZERO_ADDRESS,
  commerceImpl: ZERO_ADDRESS,
  routerProxy: ZERO_ADDRESS,
  routerImpl: ZERO_ADDRESS,
  policy: ZERO_ADDRESS,
};

// Placeholder manifest: every field is the zero address until the Bitgold
// Network deployments are published. The public `BITGOLD_CHAIN_ADDRESSES`
// table below is the checksummed form.
const RAW: Record<number, RawAddresses> = {
  [BITGOLD_TESTNET_CHAIN_ID]: { ...PLACEHOLDER },
  [BITGOLD_MAINNET_CHAIN_ID]: { ...PLACEHOLDER },
};

function build(): Record<number, DeployedAddresses> {
  const out: Record<number, DeployedAddresses> = {};
  for (const [chainIdStr, raw] of Object.entries(RAW)) {
    const chainId = Number(chainIdStr);
    const checksummed = Object.fromEntries(
      Object.entries(raw).map(([field, addr]) => [
        field,
        toChecksumAddress(addr),
      ]),
    ) as unknown as DeployedAddresses;
    out[chainId] = Object.freeze(checksummed);
  }
  return Object.freeze(out);
}

export const BITGOLD_CHAIN_ADDRESSES: Record<number, DeployedAddresses> = build();

/**
 * Return the deployment snapshot for `chainId`.
 *
 * @throws {Error} if `chainId` is not a known Bitgold Network deployment.
 */
export function getAddress(chainId: number): DeployedAddresses {
  const deployed = BITGOLD_CHAIN_ADDRESSES[chainId];
  if (deployed === undefined) {
    const known = Object.keys(BITGOLD_CHAIN_ADDRESSES)
      .map(Number)
      .sort((a, b) => a - b);
    throw new Error(
      `no Bitgold Network deployment registered for chain_id=${chainId}; known: [${known.join(", ")}]`,
    );
  }
  return deployed;
}

/**
 * `"chainId:checksumAddress"` keys of every registered payment token.
 *
 * Compatibility API for callers that still use the deployment registry.
 * `SigningPolicy.strictDefault()` derives its domain allowlist from the active
 * asset catalog's verified EIP-3009 metadata instead, so this set must not be
 * used to infer every strict-signing domain.
 *
 * A fresh `Set` is built on every call, so mutating the returned instance
 * never leaks back into the registry.
 */
export function knownPaymentTokens(): ReadonlySet<string> {
  const out = new Set<string>();
  for (const [chainId, deploy] of Object.entries(BITGOLD_CHAIN_ADDRESSES)) {
    out.add(`${chainId}:${deploy.paymentToken}`);
  }
  return out;
}
