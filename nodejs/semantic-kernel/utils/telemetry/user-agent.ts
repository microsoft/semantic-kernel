import * as packageJson from '../../../package.json'

const USER_AGENT = 'User-Agent'

// Note that if this environment variable does not exist, telemetry is enabled.
const TELEMETRY_DISABLED_ENV_VAR = 'AZURE_TELEMETRY_DISABLED'

export const IS_TELEMETRY_ENABLED =
  (process.env[TELEMETRY_DISABLED_ENV_VAR] || 'false').toLowerCase() !== 'true' &&
  (process.env[TELEMETRY_DISABLED_ENV_VAR] || 'false').toLowerCase() !== '1'

export const HTTP_USER_AGENT = 'semantic-kernel-nodejs'

let versionInfo

try {
  // Try to load version from package.json
  // In a bundled environment, this may not work, so we use 'dev' as fallback
  versionInfo = packageJson.version || 'dev'
} catch {
  // If package.json cannot be loaded, use 'dev'
  versionInfo = 'dev'
}

export const APP_INFO = IS_TELEMETRY_ENABLED
  ? {
      'semantic-kernel-version': `nodejs/${versionInfo}`,
    }
  : null

export const SEMANTIC_KERNEL_USER_AGENT = `${HTTP_USER_AGENT}/${versionInfo}`

/**
 * Prepend "semantic-kernel" to the User-Agent in the headers.
 *
 * @param headers - The existing headers dictionary
 * @returns The modified headers dictionary with "semantic-kernel-nodejs/{version}" prepended to the User-Agent
 */
export function prependSemanticKernelToUserAgent(headers: Record<string, any>): Record<string, any> {
  headers[USER_AGENT] = headers[USER_AGENT]
    ? `${SEMANTIC_KERNEL_USER_AGENT} ${headers[USER_AGENT]}`
    : SEMANTIC_KERNEL_USER_AGENT

  return headers
}
