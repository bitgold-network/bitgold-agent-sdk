import packageJson from "../package.json" with { type: "json" };

/**
 * SDK version, used to build the `built_with` ERC-8004 metadata tag
 * (`https://github.com/bitgold-network/bitgold-agent-sdk#v<version>`).
 *
 * `tsup` inlines this value into the ESM and CJS bundles, so installed
 * packages do not read package.json at runtime.
 */
export const SDK_VERSION = packageJson.version;
