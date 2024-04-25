package com.microsoft.semantickernel.aiservices.openai.assistants;

/**
 * Represents a tool definition.
 */
public interface Tool {
    /**
     * Get the identifier of the tool definition.
     * @return The identifier of the tool definition.
     */
    ToolType getType();
}
