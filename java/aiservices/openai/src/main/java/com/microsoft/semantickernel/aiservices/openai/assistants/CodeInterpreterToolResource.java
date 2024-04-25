package com.microsoft.semantickernel.aiservices.openai.assistants;

import java.util.List;

/**  Represents a {@code code_interpreter} type of {@code tool_resource} */
public interface CodeInterpreterToolResource extends ToolResource {

    @Override
    default ToolType getType() {
        return ToolType.CODE_INTERPRETER;
    }
    
    /** 
     * A list of file IDs made available to the {@code code_interpreter} tool.
     * @return A list of file IDs.
     */
    List<String> getFileIds();
}
