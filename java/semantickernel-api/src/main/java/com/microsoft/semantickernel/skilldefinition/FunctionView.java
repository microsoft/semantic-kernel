// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition;

import java.util.Collections;
import java.util.List;

/**
 * Class used to copy and export data from the skill collection. The data is mutable, but changes do
 * not affect the skill collection.
 */
public class FunctionView {

    // Name of the function. The name is used by the skill collection and in prompt templates e.g.
    // {{skillName.functionName}}
    private final String name;

    /// Name of the skill containing the function. The name is used by the skill collection and in
    // prompt templates e.g. {{skillName.functionName}}
    private final String skillName;

    // Function description. The description is used in combination with embeddings when searching
    // relevant functions.
    private final String description;

    // Whether the delegate points to a semantic function
    private final boolean isSemantic;

    // Whether the delegate is an asynchronous function
    private final boolean isAsynchronous;

    // List of function parameters
    private final List<ParameterView> parameters;

    /**
     * Create a function view.
     *
     * @param name Function name
     * @param skillName Skill name, e.g. the function namespace
     * @param description Function description
     * @param parameters List of function parameters provided by the skill developer
     * @param isSemantic Whether the function is a semantic one (or native is False)
     * @param isAsynchronous Whether the function is async. Note: all semantic functions are async
     */
    public FunctionView(
            String name,
            String skillName,
            String description,
            List<ParameterView> parameters,
            boolean isSemantic,
            boolean isAsynchronous) {
        this.name = name;
        this.skillName = skillName;
        this.description = description;
        this.parameters = Collections.unmodifiableList(parameters);
        this.isSemantic = isSemantic;
        this.isAsynchronous = isAsynchronous;
    }

    /**
     * List of function parameters
     *
     * @return the list of function parameters
     */
    public List<ParameterView> getParameters() {
        return parameters;
    }

    public String getDescription() {
        return description;
    }

    public String getSkillName() {
        return skillName;
    }

    public String getName() {
        return name;
    }
}
