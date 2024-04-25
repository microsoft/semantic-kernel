package com.microsoft.semantickernel.aiservices.openai.assistants;

/**  Represents a {@code tool_resources} object */
public interface ToolResource {
    /**
     * Get the identifier of the tool resource definition.
     * @return The identifier of the tool resource definition.
     */
    ToolType getType();
}
