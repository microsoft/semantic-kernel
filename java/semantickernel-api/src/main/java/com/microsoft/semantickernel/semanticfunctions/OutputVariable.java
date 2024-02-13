package com.microsoft.semantickernel.semanticfunctions;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.microsoft.semantickernel.exceptions.SKException;
import javax.annotation.Nullable;

public class OutputVariable {

    @Nullable
    private final String description;

    private final String type;

    @JsonCreator
    public OutputVariable(
        @Nullable
        @JsonProperty("description")
        String description,

        @JsonProperty("type")
        String type) {
        this.description = description;
        this.type = type;
    }

    @Nullable
    public String getDescription() {
        return description;
    }

    public Class<?> getType() {
        try {
            return this.getClass().getClassLoader().loadClass(type);
        } catch (ClassNotFoundException e) {
            throw new SKException("Requested output type could not be found: " + type
                + ", note this needs to be a fully qualified class name, i.e 'java.lang.String'.");
        }
    }
}
