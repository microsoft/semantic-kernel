package com.microsoft.semantickernel.aiservices.openai.assistants;

import java.util.List;

/**
 * Details on the tool outputs needed for this run to continue.
 */
public interface SubmitToolOutputs extends RequiredAction {
    
        @Override
        default RequiredActionType getType() {
            return RequiredActionType.SUBMIT_TOOL_OUTPUTS;
        }
    
        /**
        * The tool outputs that need to be submitted.
        */
        List<ToolCall> getToolOutputs();

}
