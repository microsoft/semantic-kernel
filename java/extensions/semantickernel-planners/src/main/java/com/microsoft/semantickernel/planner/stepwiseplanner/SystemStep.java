// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.stepwiseplanner;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Collections;
import java.util.Map;
import javax.annotation.Nullable;

/// <summary>
/// A step in a Stepwise plan.
/// </summary>
public class SystemStep {

    /// <summary>
    /// Gets or sets the step number.
    /// </summary>
    @Nullable private String thought;

    /// <summary>
    /// Gets or sets the action of the step
    /// </summary>
    @Nullable private String action;

    /// <summary>
    /// Gets or sets the variables for the action
    /// </summary>
    @JsonProperty("action_variables")
    @Nullable
    private Map<String, String> actionVariables;

    /// <summary>
    /// Gets or sets the output of the action
    /// </summary>
    @Nullable private String observation;

    /// <summary>
    /// Gets or sets the output of the system
    /// </summary>
    @JsonProperty("final_answer")
    @Nullable
    private String finalAnswer;

    /// <summary>
    /// The raw response from the action
    /// </summary>
    @JsonProperty("original_response")
    @Nullable
    private String originalResponse;

    public SystemStep() {}

    @JsonCreator
    public SystemStep(
            @JsonProperty("thought") @Nullable String thought,
            @JsonProperty("action") @Nullable String action,
            @JsonProperty("action_variables") @Nullable Map<String, String> actionVariables,
            @JsonProperty("observation") @Nullable String observation,
            @JsonProperty("final_answer") @Nullable String finalAnswer,
            @JsonProperty("original_response") @Nullable String originalResponse) {
        this.thought = thought;
        this.action = action;
        if (actionVariables == null) {
            this.actionVariables = null;
        } else {
            this.actionVariables = Collections.unmodifiableMap(actionVariables);
        }
        this.observation = observation;
        this.finalAnswer = finalAnswer;
        this.originalResponse = originalResponse;
    }

    @Nullable
    public String getThought() {
        return thought;
    }

    @Nullable
    public String getAction() {
        return action;
    }

    @Nullable
    public Map<String, String> getActionVariables() {
        if (actionVariables == null) {
            return null;
        }
        return Collections.unmodifiableMap(actionVariables);
    }

    @Nullable
    public String getObservation() {
        return observation;
    }

    @Nullable
    public String getFinalAnswer() {
        return finalAnswer;
    }

    @Nullable
    public String getOriginalResponse() {
        return originalResponse;
    }

    public void setThought(@Nullable String thought) {
        this.thought = thought;
    }

    public void setAction(@Nullable String action) {
        this.action = action;
    }

    public void setActionVariables(@Nullable Map<String, String> actionVariables) {
        if (actionVariables == null) {
            this.actionVariables = null;
        } else {
            this.actionVariables = Collections.unmodifiableMap(actionVariables);
        }
    }

    public void setFinalAnswer(@Nullable String finalAnswer) {
        this.finalAnswer = finalAnswer;
    }

    public void setObservation(@Nullable String observation) {
        this.observation = observation;
    }

    public void setOriginalResponse(@Nullable String originalResponse) {
        this.originalResponse = originalResponse;
    }
}
