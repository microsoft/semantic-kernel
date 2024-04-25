package com.microsoft.semantickernel.aiservices.openai.assistants;

/**
 * Represents a file search tool definition.
 */
public interface FileSearchTool extends Tool {

    @Override
    default ToolType getType() {
        return ToolType.FILE_SEARCH;
    }

}
