// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.stepwiseplanner;

import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

/// <summary>
/// Configuration for Stepwise planner instances.
/// </summary>
public class StepwisePlannerConfig {

    /// <summary>
    /// The minimum relevancy score for a function to be considered
    /// </summary>
    /// <remarks>
    /// Depending on the embeddings engine used, the user ask, the step goal
    /// and the functions available, this value may need to be adjusted.
    /// For default, this is set to null to exhibit previous behavior.
    /// </remarks>
    public double relevancyThreshold;

    /// <summary>
    /// The maximum number of relevant functions to include in the plan.
    /// </summary>
    /// <remarks>
    /// Limits the number of relevant functions as result of semantic
    /// search included in the plan creation request.
    /// <see cref="IncludedFunctions"/> will be included
    /// in the plan regardless of this limit.
    /// </remarks>
    private int maxRelevantFunctions = 100;

    /// <summary>
    /// A list of skills to exclude from the plan creation request.
    /// </summary>
    private final Set<String> excludedSkills = new HashSet<>();

    /// <summary>
    /// A list of functions to exclude from the plan creation request.
    /// </summary>
    private final Set<String> excludedFunctions = new HashSet<>();

    /// <summary>
    /// A list of functions to include in the plan creation request.
    /// </summary>
    private Set<String> includedFunctions = new HashSet<>();

    /// <summary>
    /// The maximum number of tokens to allow in a plan.
    /// </summary>
    private int maxTokens = 1024;

    /// <summary>
    /// The maximum number of iterations to allow in a plan.
    /// </summary>
    private int maxIterations = 100;

    /// <summary>
    /// The minimum time to wait between iterations in milliseconds.
    /// </summary>
    private int minIterationTimeMs = 0;

    public void addExcludedSkills(String restrictedSkillName) {
        excludedSkills.add(restrictedSkillName);
    }

    public void addExcludedFunctions(String restrictedFunctionName) {
        excludedFunctions.add(restrictedFunctionName);
    }

    public int getMaxTokens() {
        return maxTokens;
    }

    public int getMaxIterations() {
        return maxIterations;
    }

    public Set<String> getExcludedSkills() {
        return Collections.unmodifiableSet(excludedSkills);
    }

    public Set<String> getExcludedFunctions() {
        return Collections.unmodifiableSet(excludedFunctions);
    }

    public int getMinIterationTimeMs() {
        return minIterationTimeMs;
    }

    public int getMaxRelevantFunctions() {
        return maxRelevantFunctions;
    }

    public double getRelevancyThreshold() {
        return relevancyThreshold;
    }

    public Set<String> getIncludedFunctions() {
        return Collections.unmodifiableSet(includedFunctions);
    }
}
