const AGENT_TYPE_REGEX = /^[\w\-.]+$/

/**
 * Check if the agent type is valid.
 *
 * Note: This function is marked as 'experimental' and may change in the future.
 */
export function isValidAgentType(value: string): boolean {
  return AGENT_TYPE_REGEX.test(value)
}
