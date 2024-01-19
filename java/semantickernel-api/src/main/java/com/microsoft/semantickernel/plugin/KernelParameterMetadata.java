package com.microsoft.semantickernel.plugin;

public class KernelParameterMetadata {

    /// <summary>The name of the parameter.</summary>
    private final String name;
    /// <summary>The description of the parameter.</summary>
    private final String description;
    private final String defaultValue;
    private final boolean isRequired;
    private final Class<?> parameterType;

    public KernelParameterMetadata(
        String name,
        String description,
        Class<?> parameterType,
        String defaultValue, boolean isRequired) {
        this.name = name;
        this.description = description;
        this.defaultValue = defaultValue;
        this.isRequired = isRequired;
        this.parameterType = String.class;
    }

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }

    public String getDefaultValue() {
        return defaultValue;
    }

    public boolean isRequired() {
        return isRequired;
    }

    public Class<?> getType() {
        return parameterType;
    }

    //private KernelJsonSchema schema;
}
