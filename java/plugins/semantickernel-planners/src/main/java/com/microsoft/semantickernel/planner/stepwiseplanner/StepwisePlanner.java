// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.stepwiseplanner;

import com.microsoft.semantickernel.planner.actionplanner.Plan;

/** Interface for planner that creates a Stepwise plan using Mrkl systems. */
public interface StepwisePlanner {

    /**
     * Create a plan for a goal.
     *
     * @param goal The goal to create a plan for.
     * @return The plan.
     */
    Plan createPlan(String goal);
}
