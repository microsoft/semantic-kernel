package com.microsoft.semantickernel.aiservices.openai.assistants;

/**
 * Controls which (if any) tool is called by the model
 */
public interface ToolChoice {

    /**
     * The type of tool choice
     * @return the type of tool choice
     */
    ToolChoiceType getType();

    /**
     * If the type is {@code function}, the function to call
     * @return the function to call, or @code null} if the type is not {@code function}
     */
    String getFunction();

}
