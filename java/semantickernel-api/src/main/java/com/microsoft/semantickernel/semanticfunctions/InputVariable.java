package com.microsoft.semantickernel.semanticfunctions;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.microsoft.semantickernel.exceptions.SKException;
import javax.annotation.Nullable;

/**
 * Metadata for an input variable of a {@link com.microsoft.semantickernel.orchestration.KernelFunction}.
 */
public class InputVariable {

    private String name;
    private String type;
    @Nullable
    private String description;
    @Nullable
    private String defaultValue;
    private boolean isRequired;

    /**
     * Creates a new instance of {@link InputVariable}.
     *
     * @param name the name of the input variable
     */
    public InputVariable(String name) {
        this.name = name;
        this.type = String.class.getName();
        this.description = null;
        this.defaultValue = null;
        this.isRequired = true;
    }

    /**
     * Creates a new instance of {@link InputVariable}.
     *
     * @param name the name of the input variable
     * @param type the type of the input variable
     * @param description the description of the input variable
     * @param defaultValue the default value of the input variable
     * @param isRequired whether the input variable is required
     */
    @JsonCreator
    public InputVariable(
        @JsonProperty("name") String name,
        @JsonProperty("type") String type,
        @JsonProperty("description") @Nullable String description,
        @JsonProperty("default") @Nullable String defaultValue,
        @JsonProperty("is_required") boolean isRequired) {
        this.name = name;

        if (type == null) {
            type = "java.lang.String";
        }
        this.type = type;
        this.description = description;
        this.defaultValue = defaultValue;
        this.isRequired = isRequired;
    }

    /**
     * Gets the name of the input variable.
     * @return the name of the input variable
     */
    public String getName() {
        return name;
    }

    /**
     * Gets the type of the input variable.
     * @return the type of the input variable
     */
    public String getType() {
        return type;
    }

    /**
     * Gets the description of the input variable.
     * @return the description of the input variable
     */
    @Nullable
    public String getDescription() {
        return description;
    }

    /**
     * Gets the default value of the input variable.
     * @return the default value of the input variable
     */
    @Nullable
    public String getDefaultValue() {
        return defaultValue;
    }

    /**
     * Gets whether the input variable is required.
     * @return whether the input variable is required
     */
    public boolean isRequired() {
        return isRequired;
    }

    /**
     * Gets the class of the type of the input variable.
     * @return the class of the type of the input variable
     */
    public Class<?> getTypeClass() {
        try {
            return Thread.currentThread().getContextClassLoader().loadClass(type);
        } catch (ClassNotFoundException e) {
            throw new SKException(
                "Could not load class for type: " + type + " for input variable " + name +
                    ". This needs to be a fully qualified class name, e.g. 'java.lang.String'.");
        }
    }
}
