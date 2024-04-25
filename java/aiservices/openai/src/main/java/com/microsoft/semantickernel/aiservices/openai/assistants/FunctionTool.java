package com.microsoft.semantickernel.aiservices.openai.assistants;

import com.microsoft.semantickernel.semanticfunctions.InputVariable;

/**
 * Represents a tool that is a function.
 */
public interface FunctionTool extends Tool {

    /**
     * Get the name of the function to be called.
     *
     * @return the name of the function to be called.
     */
    public String getName();

    /**
     * Get the description of what the function does, used by the model to choose when and how
     * to call the function.
     *
     * @return a description of what the function does.
     */
    public String getDescription();

    /**
     * Get the parameters the functions accepts.
     *
     * @return the parameters value.
     */
    public InputVariable getParameters();

}
