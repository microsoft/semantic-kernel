package com.microsoft.semantickernel.plugin;

public class KernelParameterMetadata {

    /// <summary>The name of the parameter.</summary>
    private final String name;
    /// <summary>The description of the parameter.</summary>
    private final String description;
    private final String defaultValue;
    private final boolean isRequired;
    private Class parameterType;

    public KernelParameterMetadata(
        String name,
        String description,
        String defaultValue,
        boolean isRequired) {
        this.name = name;
        this.description = description;
        this.defaultValue = defaultValue;
        this.isRequired = isRequired;
    }

    public String getName() {
        return name;
    }
    //private KernelJsonSchema schema;
}
