// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.actionplanner;

/// <summary>
/// Plan data structure returned by the basic planner semantic function
/// </summary>
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Map;

public class ActionPlanResponse {

    public static class PlanData {
        /// <summary>
        /// Rationale given by the LLM for choosing the function
        /// </summary>
        public final String rationale;

        /// <summary>
        /// Name of the function chosen
        /// </summary>
        public final String function;

        /// <summary>
        /// Parameter values
        /// </summary>
        public final Map<String, String> parameters;

        @JsonCreator
        public PlanData(
                @JsonProperty("plan") String rationale,
                @JsonProperty("function") String function,
                @JsonProperty("parameters") Map<String, String> parameters) {
            this.rationale = rationale;
            this.function = function;
            this.parameters = parameters;
        }
    }

    public final PlanData plan;

    @JsonCreator
    public ActionPlanResponse(@JsonProperty("plan") PlanData plan) {
        this.plan = plan;
    }
}
