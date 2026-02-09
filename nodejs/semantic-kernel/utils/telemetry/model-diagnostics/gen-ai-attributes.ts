import { AuthorRole } from '../../../contents/utils/author-role'

// Constants for tracing activities with semantic conventions.
// Ideally, we should use the attributes from the semcov package.
// However, many of the attributes are not yet available in the package,
// so we define them here for now.

// Activity tags
export const OPERATION = 'gen_ai.operation.name'
export const SYSTEM = 'gen_ai.system'
export const ERROR_TYPE = 'error.type'
export const MODEL = 'gen_ai.request.model'
export const SEED = 'gen_ai.request.seed'
export const PORT = 'server.port'
export const ENCODING_FORMATS = 'gen_ai.request.encoding_formats'
export const FREQUENCY_PENALTY = 'gen_ai.request.frequency_penalty'
export const MAX_TOKENS = 'gen_ai.request.max_tokens'
export const STOP_SEQUENCES = 'gen_ai.request.stop_sequences'
export const TEMPERATURE = 'gen_ai.request.temperature'
export const TOP_K = 'gen_ai.request.top_k'
export const TOP_P = 'gen_ai.request.top_p'
export const FINISH_REASON = 'gen_ai.response.finish_reason'
export const RESPONSE_ID = 'gen_ai.response.id'
export const INPUT_TOKENS = 'gen_ai.usage.input_tokens'
export const OUTPUT_TOKENS = 'gen_ai.usage.output_tokens'
export const TOOL_CALL_ID = 'gen_ai.tool.call.id'
export const TOOL_CALL_ARGUMENTS = 'gen_ai.tool.call.arguments'
export const TOOL_CALL_RESULT = 'gen_ai.tool.call.result'
export const TOOL_DESCRIPTION = 'gen_ai.tool.description'
export const TOOL_NAME = 'gen_ai.tool.name'
export const ADDRESS = 'server.address'

// Activity events
export const EVENT_NAME = 'event.name'
export const SYSTEM_MESSAGE = 'gen_ai.system.message'
export const USER_MESSAGE = 'gen_ai.user.message'
export const ASSISTANT_MESSAGE = 'gen_ai.assistant.message'
export const TOOL_MESSAGE = 'gen_ai.tool.message'
export const CHOICE = 'gen_ai.choice'
export const PROMPT = 'gen_ai.prompt'

// Kernel specific attributes
export const AVAILABLE_FUNCTIONS = 'sk.available_functions'

export const ROLE_EVENT_MAP: Record<AuthorRole, string> = {
  [AuthorRole.SYSTEM]: SYSTEM_MESSAGE,
  [AuthorRole.USER]: USER_MESSAGE,
  [AuthorRole.ASSISTANT]: ASSISTANT_MESSAGE,
  [AuthorRole.TOOL]: TOOL_MESSAGE,
  [AuthorRole.DEVELOPER]: ASSISTANT_MESSAGE, // Map DEVELOPER to ASSISTANT_MESSAGE as fallback
}
