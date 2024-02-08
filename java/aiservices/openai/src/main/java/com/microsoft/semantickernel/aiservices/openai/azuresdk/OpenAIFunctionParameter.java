package com.microsoft.semantickernel.aiservices.openai.azuresdk;

public class OpenAIFunctionParameter {
    private final String name;
    private final String description;
    private final boolean isRequired;
    private final Class<?> parameterType;

    /**
     * Initializes an OpenAIFunctionParameter.
     *
     * @param name          The name of the parameter.
     * @param description   A description of the parameter.
     * @param isRequired    Whether the parameter is required vs optional.
     * @param parameterType The type of the parameter, if known.
     */
    OpenAIFunctionParameter(String name, String description, boolean isRequired, Class<?> parameterType) {
        this.name = (name != null) ? name : "";
        this.description = (description != null) ? description : "";
        this.isRequired = isRequired;
        this.parameterType = parameterType;
    }

    /**
     * Gets the name of the parameter.
     *
     * @return The name of the parameter.
     */
    public String getName() {
        return name;
    }

    /**
     * Gets a description of the parameter.
     *
     * @return A description of the parameter.
     */
    public String getDescription() {
        return description;
    }

    /**
     * Checks whether the parameter is required vs optional.
     *
     * @return True if the parameter is required, false if it is optional.
     */
    public boolean isRequired() {
        return isRequired;
    }

    /**
     * Gets the type of the parameter, if known.
     *
     * @return The type of the parameter, or null if not known.
     */
    public Class<?> getParameterType() {
        return parameterType;
    }
}
