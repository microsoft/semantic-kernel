/**
 * Constants for tracing agent activities with semantic conventions.
 * Ideally, we should use the attributes from the semcov package.
 * However, many of the attributes are not yet available in the package,
 * so we define them here for now.
 */

/**
 * Activity tags
 */
export const OPERATION = 'gen_ai.operation.name'
export const AGENT_ID = 'gen_ai.agent.id'
export const AGENT_NAME = 'gen_ai.agent.name'
export const AGENT_DESCRIPTION = 'gen_ai.agent.description'
export const AGENT_INVOCATION_INPUT = 'gen_ai.input.messages'
export const AGENT_INVOCATION_OUTPUT = 'gen_ai.output.messages'
export const AGENT_TOOL_DEFINITIONS = 'gen_ai.tool.definitions'
export const ERROR_TYPE = 'error.type'
