package com.microsoft.semantickernel.aiservices.openai.azuresdk;

public class OpenAIFunctionReturnParameter {
    private final String description;
    private final Class<?> parameterType;

    /**
     * Initializes an OpenAIFunctionReturnParameter.
     *
     * @param description   A description of the return parameter.
     * @param parameterType The type of the return parameter, if known.
     */
    OpenAIFunctionReturnParameter(String description, Class<?> parameterType) {
        this.description = (description != null) ? description : "";
        this.parameterType = parameterType;
    }

    /**
     * Gets a description of the return parameter.
     *
     * @return A description of the return parameter.
     */
    public String getDescription() {
        return description;
    }

    /**
     * Gets the type of the return parameter, if known.
     *
     * @return The type of the return parameter, or null if not known.
     */
    public Class<?> getParameterType() {
        return parameterType;
    }
}
