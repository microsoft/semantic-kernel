// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Collections;
import java.util.List;

/** Input configuration (list of all input parameters for a semantic function). */
public class InputConfig {

    public final List<InputParameter> parameters;

    @JsonCreator
    public InputConfig(@JsonProperty("parameters") List<InputParameter> parameters) {
        this.parameters = Collections.unmodifiableList(parameters);
    }

    public List<InputParameter> getParameters() {
        return parameters;
    }
}
