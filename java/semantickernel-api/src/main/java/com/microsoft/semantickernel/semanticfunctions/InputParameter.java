// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

/** Input parameter for semantic functions */
public class InputParameter {

    private final String name;
    private final String description;
    private final String defaultValue;

    @JsonCreator
    public InputParameter(
        @JsonProperty("name") String name,
        @JsonProperty("description") String description,
        @JsonProperty("defaultValue") String defaultValue) {
        this.name = name;
        this.description = description;
        this.defaultValue = defaultValue;
    }

    /**
     * Name of the parameter to pass to the function. e.g. when using "{{$input}}" the name is
     * "input", when using "{{$style}}" the name is "style", etc.
     *
     * @return name
     */
    public String getName() {
        return name;
    }

    /**
     * Parameter description for UI apps and planner. Localization is not supported here.
     *
     * @return description
     */
    public String getDescription() {
        return description;
    }

    /**
     * Default value when nothing is provided
     *
     * @return the default value
     */
    public String getDefaultValue() {
        return defaultValue;
    }
}
