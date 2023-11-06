// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.sequentialplanner;

import java.util.Collections;
import java.util.HashSet;
import java.util.Set;
import javax.annotation.Nullable;

/// <summary>
/// Common configuration for planner instances.
/// </summary>
public class SequentialPlannerRequestSettings {

    /// <summary>
    /// The minimum relevancy score for a function to be considered
    /// </summary>
    /// <remarks>
    /// Depending on the embeddings engine used, the user ask, the step goal
    /// and the functions available, this value may need to be adjusted.
    /// For default, this is set to null to exhibit previous behavior.
    /// </remarks>
    @Nullable private Float relevancyThreshold = null;

    /*
        /// <summary>
        /// The maximum number of relevant functions to include in the plan.
        /// </summary>
        /// <remarks>
        /// Limits the number of relevant functions as result of semantic
        /// search included in the plan creation request.
        /// <see cref="IncludedFunctions"/> will be included
        /// in the plan regardless of this limit.
        /// </remarks>
    */
    private int maxRelevantFunctions = 100;

    /// <summary>
    /// A list of skills to exclude from the plan creation request.
    /// </summary>
    private Set<String> excludedSkills = new HashSet<>();
    /// <summary>
    /// A list of functions to exclude from the plan creation request.
    /// </summary>
    private Set<String> excludedFunctions = new HashSet<>();

    /// <summary>
    /// A list of functions to include in the plan creation request.
    /// </summary>
    private Set<String> includedFunctions = new HashSet<>();

    /// <summary>
    /// The maximum number of tokens to allow in a plan.
    /// </summary>
    private int maxTokens = 1024;

    public SequentialPlannerRequestSettings(
            @Nullable Float relevancyThreshold,
            int maxRelevantFunctions,
            Set<String> excludedSkills,
            Set<String> excludedFunctions,
            Set<String> includedFunctions,
            int maxTokens) {
        this.relevancyThreshold = relevancyThreshold;
        this.maxRelevantFunctions = maxRelevantFunctions;
        this.excludedSkills = Collections.unmodifiableSet(excludedSkills);
        this.excludedFunctions = Collections.unmodifiableSet(excludedFunctions);
        this.includedFunctions = Collections.unmodifiableSet(includedFunctions);
        this.maxTokens = maxTokens;
    }

    public SequentialPlannerRequestSettings() {}

    @Nullable
    public Float getRelevancyThreshold() {
        return relevancyThreshold;
    }

    public int getMaxRelevantFunctions() {
        return maxRelevantFunctions;
    }

    public Set<String> getExcludedSkills() {
        return Collections.unmodifiableSet(excludedSkills);
    }

    public Set<String> getExcludedFunctions() {
        return Collections.unmodifiableSet(excludedFunctions);
    }

    public Set<String> getIncludedFunctions() {
        return Collections.unmodifiableSet(includedFunctions);
    }

    public int getMaxTokens() {
        return maxTokens;
    }

    public SequentialPlannerRequestSettings addExcludedFunctions(String function) {
        HashSet<String> ex = new HashSet<>(excludedFunctions);
        ex.add(function);
        return new SequentialPlannerRequestSettings(
                relevancyThreshold,
                maxRelevantFunctions,
                excludedSkills,
                ex,
                includedFunctions,
                maxTokens);
    }

    public SequentialPlannerRequestSettings addExcludedSkillName(String skillName) {
        HashSet<String> ex = new HashSet<>(excludedSkills);
        ex.add(skillName);
        return new SequentialPlannerRequestSettings(
                relevancyThreshold,
                maxRelevantFunctions,
                ex,
                excludedFunctions,
                includedFunctions,
                maxTokens);
    }
}
