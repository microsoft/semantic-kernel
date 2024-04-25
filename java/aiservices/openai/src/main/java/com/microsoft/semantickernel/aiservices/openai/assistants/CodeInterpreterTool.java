package com.microsoft.semantickernel.aiservices.openai.assistants;

/**
 * Represents a {@code code_interperter} tool definition.
 */
public interface CodeInterpreterTool extends Tool {

    @Override
    default ToolType getType() {
        return ToolType.CODE_INTERPRETER;
    }
}
