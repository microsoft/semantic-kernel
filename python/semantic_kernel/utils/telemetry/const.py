# Copyright (c) Microsoft. All rights reserved.
#
# Constants for tracing activities with semantic conventions.

# Activity tags
SYSTEM = "gen_ai.system"
OPERATION = "gen_ai.operation.name"
CHAT_COMPLETION_OPERATION = "chat.completions"
TEXT_COMPLETION_OPERATION = "text.completions"
MODEL = "gen_ai.request.model"
MAX_TOKENS = "gen_ai.request.max_tokens"  # nosec
TEMPERATURE = "gen_ai.request.temperature"
TOP_P = "gen_ai.request.top_p"
RESPONSE_ID = "gen_ai.response.id"
FINISH_REASON = "gen_ai.response.finish_reason"
PROMPT_TOKENS = "gen_ai.response.prompt_tokens"  # nosec
COMPLETION_TOKENS = "gen_ai.response.completion_tokens"  # nosec
ADDRESS = "server.address"
PORT = "server.port"
ERROR_TYPE = "error.type"

# Activity events
PROMPT_EVENT = "gen_ai.content.prompt"
COMPLETION_EVENT = "gen_ai.content.completion"

# Activity event attributes
PROMPT_EVENT_PROMPT = "gen_ai.prompt"
COMPLETION_EVENT_COMPLETION = "gen_ai.completion"
