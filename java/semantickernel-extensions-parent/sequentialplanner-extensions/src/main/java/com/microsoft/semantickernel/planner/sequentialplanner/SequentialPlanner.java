// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.sequentialplanner; // Copyright (c) Microsoft. All
// rights reserved.

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.FunctionBuilders;
import com.microsoft.semantickernel.planner.SequentialPlannerRequestSettings;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.textcompletion.CompletionSKContext;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;

import reactor.core.publisher.Mono;

import java.util.ArrayList;

import javax.annotation.Nullable;

/// <summary>
/// A planner that uses semantic function to create a sequential plan.
/// </summary>
public class SequentialPlanner {
    private static final String StopSequence = "<!--";

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    private static final String RestrictedSkillName = "SequentialPlanner_Excluded";

    private final SequentialPlannerRequestSettings config;
    private final CompletionSKContext context;

    /// <summary>
    /// the function flow semantic function, which takes a goal and creates an xml plan that can be
    // executed
    /// </summary>
    private final CompletionSKFunction functionFlowFunction;

    /// <summary>
    /// Initialize a new instance of the <see cref="SequentialPlanner"/> class.
    /// </summary>
    /// <param name="kernel">The semantic kernel instance.</param>
    /// <param name="config">The planner configuration.</param>
    /// <param name="prompt">Optional prompt override</param>
    public SequentialPlanner(
            Kernel kernel,
            @Nullable SequentialPlannerRequestSettings config,
            @Nullable String prompt) {
        // Verify.NotNull(kernel);

        if (config == null) {
            config = new SequentialPlannerRequestSettings();
        }

        this.config = config.addExcludedSkillName(RestrictedSkillName);

        String promptTemplate;
        if (prompt != null) {
            promptTemplate = prompt;
        } else {
            promptTemplate = EmbeddedResource.read("skprompt.txt");
        }

        this.functionFlowFunction =
                FunctionBuilders.getCompletionBuilder(kernel)
                        .createFunction(
                                promptTemplate,
                                null,
                                RestrictedSkillName,
                                "Given a request or command or goal generate a step by step plan to"
                                    + " fulfill the request using functions. This ability is also"
                                    + " known as decision making and function flow",
                                new PromptTemplateConfig.CompletionConfig(
                                        0.0,
                                        0.0,
                                        0.0,
                                        0.0,
                                        this.config.getMaxTokens(),
                                        new ArrayList<>()));

        this.context = functionFlowFunction.buildContext();
    }

    /// <summary>
    /// Create a plan for a goal.
    /// </summary>
    /// <param name="goal">The goal to create a plan for.</param>
    /// <returns>The plan.</returns>
    public Mono<CompletionSKContext> createPlanAsync(String goal) {
        if (goal == null || goal.isEmpty()) {
            // throw new PlanningException(PlanningException.ErrorCodes.InvalidGoal, "The goal
            // specified is empty");
            throw new RuntimeException();
        }

        return new DefaultSequentialPlannerSKContext(context)
                .getFunctionsManualAsync(goal, this.config)
                .flatMap(
                        relevantFunctionsManual -> {
                            CompletionSKContext updatedContext =
                                    context.setVariable(
                                                    "available_functions", relevantFunctionsManual)
                                            .update(goal);

                            return functionFlowFunction.invokeAsync(updatedContext, null);
                        });
    }
}
