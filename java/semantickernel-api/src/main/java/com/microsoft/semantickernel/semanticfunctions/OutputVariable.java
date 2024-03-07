// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.microsoft.semantickernel.exceptions.SKException;

import java.util.Objects;

import javax.annotation.Nullable;

/**
 * Metadata for an output variable of a kernel function.
 */
public class OutputVariable {

    @Nullable
    private final String description;

    private final String type;

    /**
     * Constructor.
     * @param type        The type of the output variable.
     * @param description The description of the output variable.
     */
    @JsonCreator
    public OutputVariable(
        @Nullable @JsonProperty(value = "type", defaultValue = "java.lang.String") String type,
        @Nullable @JsonProperty("description") String description) {
        this.description = description;
        if (type == null || type.isEmpty()) {
            type = "java.lang.String";
        }
        this.type = type;
    }

    /**
     * Get the description of the output variable.
     *
     * @return The description of the output variable.
     */
    @Nullable
    public String getDescription() {
        return description;
    }

    /**
     * Get the type of the output variable.
     *
     * @return The type of the output variable.
     */
    public Class<?> getType() {
        try {
            return this.getClass().getClassLoader().loadClass(type);
        } catch (ClassNotFoundException e) {
            throw new SKException("Requested output type could not be found: " + type
                + ". This needs to be a fully qualified class name, e.g. 'java.lang.String'.");
        }
    }

    @Override
    public int hashCode() {
        return Objects.hash(type, description);
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (obj == null || getClass() != obj.getClass()) {
            return false;
        }
        OutputVariable that = (OutputVariable) obj;
        if (!Objects.equals(type, that.type))
            return false;
        return Objects.equals(description, that.description);
    }
}
