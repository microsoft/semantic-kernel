package com.microsoft.semantickernel.aiservices.openai.assistants;

/**
 * Metadata about a tool call
 */
public interface ToolCall {

    /**
     * The ID of the tool call.
     * @return The ID of the tool call.
     */
    String getId();

    /**
     * The type of tool call the output is required for.
     * @return The type of tool call the output is required for.
     */
    default ToolType getType() { return ToolType.FUNCTION; }

    /**
     * The function definition.
     * @return The function definition.
     */
    FunctionTool getFunction();
}
