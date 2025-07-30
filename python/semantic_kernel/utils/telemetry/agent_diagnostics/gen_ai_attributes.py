# Copyright (c) Microsoft. All rights reserved.

# Constants for tracing agent activities with semantic conventions.
# Ideally, we should use the attributes from the semcov package.
# However, many of the attributes are not yet available in the package,
# so we define them here for now.

# Activity tags
OPERATION = "gen_ai.operation.name"
AGENT_ID = "gen_ai.agent.id"
AGENT_NAME = "gen_ai.agent.name"
AGENT_DESCRIPTION = "gen_ai.agent.description"
AGENT_INVOCATION_INPUT = "gen_ai.agent.invocation_input"
AGENT_INVOCATION_OUTPUT = "gen_ai.agent.invocation_output"
ERROR_TYPE = "error.type"
