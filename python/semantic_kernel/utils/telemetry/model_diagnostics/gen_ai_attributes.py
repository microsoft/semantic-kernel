# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.contents.utils.author_role import AuthorRole

# Constants for tracing activities with semantic conventions.
# Ideally, we should use the attributes from the semcov package.
# However, many of the attributes are not yet available in the package,
# so we define them here for now.

# Activity tags
OPERATION = "gen_ai.operation.name"
SYSTEM = "gen_ai.system"
ERROR_TYPE = "error.type"
MODEL = "gen_ai.request.model"
SEED = "gen_ai.request.seed"
PORT = "server.port"
ENCODING_FORMATS = "gen_ai.request.encoding_formats"
FREQUENCY_PENALTY = "gen_ai.request.frequency_penalty"
MAX_TOKENS = "gen_ai.request.max_tokens"
STOP_SEQUENCES = "gen_ai.request.stop_sequences"
TEMPERATURE = "gen_ai.request.temperature"
TOP_K = "gen_ai.request.top_k"
TOP_P = "gen_ai.request.top_p"
FINISH_REASON = "gen_ai.response.finish_reason"
RESPONSE_ID = "gen_ai.response.id"
INPUT_TOKENS = "gen_ai.usage.input_tokens"
OUTPUT_TOKENS = "gen_ai.usage.output_tokens"
ADDRESS = "server.address"

# Activity events
EVENT_NAME = "event.name"
SYSTEM_MESSAGE = "gen_ai.system.message"
USER_MESSAGE = "gen_ai.user.message"
ASSISTANT_MESSAGE = "gen_ai.assistant.message"
TOOL_MESSAGE = "gen_ai.tool.message"
CHOICE = "gen_ai.choice"
PROMPT = "gen_ai.prompt"

# Kernel specific attributes
AVAILABLE_FUNCTIONS = "sk.available_functions"


ROLE_EVENT_MAP = {
    AuthorRole.SYSTEM: SYSTEM_MESSAGE,
    AuthorRole.USER: USER_MESSAGE,
    AuthorRole.ASSISTANT: ASSISTANT_MESSAGE,
    AuthorRole.TOOL: TOOL_MESSAGE,
}
