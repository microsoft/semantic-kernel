// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import java.util.Objects;
import javax.annotation.Nullable;

/**
 * Metadata for an input variable of a {@link KernelFunction}.
 */
public class InputVariable {

    private final String name;
    @Nullable
    private final String description;
    @Nullable
    private final String defaultValue;
    private final boolean isRequired;
    private final String type;

    /**
     * Creates a new instance of {@link InputVariable}.
     *
     * @param name         the name of the input variable
     * @param type         the type of the input variable
     * @param description  the description of the input variable
     * @param defaultValue the default value of the input variable
     * @param isRequired   whether the input variable is required
     */
    @JsonCreator
    public InputVariable(
        @JsonProperty("name") String name,
        @JsonProperty("type") String type,
        @JsonProperty("description") @Nullable String description,
        @JsonProperty("default") @Nullable String defaultValue,
        @JsonProperty("is_required") boolean isRequired) {
        this.name = name;
        this.description = description;
        this.defaultValue = defaultValue;
        this.isRequired = isRequired;
        if (type == null) {
            type = "java.lang.String";
        }
        this.type = type;
    }

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
     * @param name         the name of the input variable
     * @param type         the type of the input variable
     * @param description  the description of the input variable
     * @param defaultValue the default value of the input variable
     * @param required     whether the input variable is required
     * @return a new instance of {@link InputVariable}
     */
    public static InputVariable build(
        String name,
        Class<?> type,
        @Nullable String description,
        @Nullable String defaultValue,
        boolean required) {
        return new InputVariable(name, type.getName(), description, defaultValue, required);
    }

    /**
     * Gets the name of the input variable.
     *
     * @return the name of the input variable
     */
    public String getName() {
        return name;
    }

    /**
     * Gets the description of the input variable.
     *
     * @return the description of the input variable
     */
    @Nullable
    public String getDescription() {
        return description;
    }

    /**
     * Gets the default value of the input variable.
     *
     * @return the default value of the input variable
     */
    @Nullable
    public String getDefaultValue() {
        return defaultValue;
    }

    /**
     * Gets whether the input variable is required.
     *
     * @return whether the input variable is required
     */
    public boolean isRequired() {
        return isRequired;
    }

    /**
     * Gets the type of the input variable.
     *
     * @return the type of the input variable
     */
    public String getType() {
        return type;
    }

    /**
     * Gets the class of the type of the input variable.
     *
     * @return the class of the type of the input variable
     */
    public Class<?> getTypeClass() {
        return KernelPluginFactory.getTypeForName(type);
    }

    @Override
    public int hashCode() {
        return Objects.hash(name, type, description, defaultValue, isRequired);
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }

        if (!getClass().isInstance(obj)) {
            return false;
        }

        InputVariable other = (InputVariable) obj;
        if (!Objects.equals(name, other.name)) {
            return false;
        }
        if (!Objects.equals(type, other.type)) {
            return false;
        }
        if (!Objects.equals(description, other.description)) {
            return false;
        }
        if (!Objects.equals(defaultValue, other.defaultValue)) {
            return false;
        }
        return isRequired == other.isRequired;
    }

}
