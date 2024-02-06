package com.microsoft.semantickernel.semanticfunctions;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.microsoft.semantickernel.exceptions.SKException;
import javax.annotation.Nullable;

public class InputVariable {

    @JsonProperty("name")
    private String name;

    @JsonProperty("type")
    private String type;

    @Nullable
    @JsonProperty("description")
    private String description;

    @JsonProperty("default")
    @Nullable
    private String defaultValue;

    @JsonProperty("is_required")
    private boolean isRequired;

    public InputVariable(String name) {
        this.name = name;
        this.type = String.class.getName();
        this.description = null;
        this.defaultValue = null;
        this.isRequired = true;
    }

    @JsonCreator
    public InputVariable(
        @JsonProperty("name")
        String name,
        @JsonProperty("type")
        String type,
        @JsonProperty("description")
        @Nullable
        String description,
        @JsonProperty("default")
        @Nullable
        String defaultValue,
        @JsonProperty("isRequired")
        boolean isRequired) {
        this.name = name;

        if (type == null) {
            type = "java.lang.String";
        }
        this.type = type;
        this.description = description;
        this.defaultValue = defaultValue;
        this.isRequired = isRequired;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    @Nullable
    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    @Nullable
    public String getDefaultValue() {
        return defaultValue;
    }

    public void setDefaultValue(String defaultValue) {
        this.defaultValue = defaultValue;
    }

    public boolean isRequired() {
        return isRequired;
    }

    public void setRequired(boolean required) {
        isRequired = required;
    }

    public Class<?> getTypeClass() {
        try {
            return Thread.currentThread().getContextClassLoader().loadClass(type);
        } catch (ClassNotFoundException e) {
            throw new SKException(
                "Could not load class for type: " + type + " when for input variable " + name +
                    ", note this needs to be a fully qualified class name, i.e 'java.lang.String'.");
        }
    }
}
