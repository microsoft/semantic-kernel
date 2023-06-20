// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition;

/// <summary>
/// Class used to copy and export data from
/// <see cref="SKFunctionContextParameterAttribute"/>
/// and <see cref="SKFunctionInputAttribute"/>
/// for planner and related scenarios.
/// </summary>
public class ParameterView {
    private final String name;
    private final String description;
    private final String defaultValue;

    /// <summary>
    /// Create a function parameter view, using information provided by the skill developer.
    /// </summary>
    /// <param name="name">Parameter name. The name must be alphanumeric (underscore is the only
    // special char allowed).</param>
    /// <param name="description">Parameter description</param>
    /// <param name="defaultValue">Default parameter value, if not provided</param>
    public ParameterView(String name, String description, String defaultValue) {
        // TODO
        // Verify.ValidFunctionParamName(name);

        this.name = name;
        this.description = description;
        this.defaultValue = defaultValue;
    }

    public ParameterView(String name) {
        this(name, "", "");
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
}
