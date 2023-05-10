// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.sequentialplanner; // Copyright (c) Microsoft. All
// rights reserved.

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.planner.SequentialPlannerRequestSettings;
import com.microsoft.semantickernel.planner.SequentialPlannerSKContext;

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
    private final SequentialPlannerSKContext context;

    /// <summary>
    /// the function flow semantic function, which takes a goal and creates an xml plan that can be
    // executed
    /// </summary>
    private final SKFunction<Void, SequentialPlannerSKContext> functionFlowFunction;

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
                SKBuilders.plannerFunctions()
                        .createFunction(
                                promptTemplate,
                                null,
                                RestrictedSkillName,
                                "Given a request or command or goal generate a step by step plan to"
                                    + " fulfill the request using functions. This ability is also"
                                    + " known as decision making and function flow",
                                this.config.getMaxTokens(),
                                0.0,
                                0.0,
                                0.0,
                                0.0,
                                new ArrayList<>())
                        .registerOnKernel(kernel);

        this.context = functionFlowFunction.buildContext();
    }

    /// <summary>
    /// Create a plan for a goal.
    /// </summary>
    /// <param name="goal">The goal to create a plan for.</param>
    /// <returns>The plan.</returns>
    public Mono<SequentialPlannerSKContext> createPlanAsync(String goal) {
        if (goal == null || goal.isEmpty()) {
            // throw new PlanningException(PlanningException.ErrorCodes.InvalidGoal, "The goal
            // specified is empty");
            throw new RuntimeException();
        }

        return this.context
                .getFunctionsManualAsync(goal, this.config)
                .flatMap(
                        relevantFunctionsManual -> {
                            SequentialPlannerSKContext updatedContext =
                                    context.setVariable(
                                                    "available_functions", relevantFunctionsManual)
                                            .update(goal);

                            return functionFlowFunction.invokeAsync(updatedContext, null);
                        });
    }
    /*
        public void toPlanString(@Nullable String indent) {
            if (indent == null) {
                indent = " ";
            }
            String goalHeader = indent+"Goal: " + + "\n\n{indent}Steps:\n";

            string stepItems = string.Join("\n", originalPlan.Steps.Select(step = >
                    {
            if (step.Steps.Count == 0) {
                string skillName = step.SkillName;
                string stepName = step.Name;

                string parameters = string.Join(" ", step.Parameters.Select(param = > $"{param.Key}='{param.Value}'"));
                if (!string.IsNullOrEmpty(parameters)) {
                    parameters = $ " {parameters}";
                }

                string ? outputs = step.Outputs.FirstOrDefault();
                if (!string.IsNullOrEmpty(outputs)) {
                    outputs = $ " => {outputs}";
                }

                return $ "{indent}{indent}- {string.Join(". ", skillName, stepName)}{parameters}{outputs}";
            } else {
                string nestedSteps = step.ToPlanString(indent + indent);
                return nestedSteps;
            }
            }));

            return goalHeader + stepItems;

        }
    */
    /*

       if (string.IsNullOrEmpty(goal))
       {
           throw new PlanningException(PlanningException.ErrorCodes.InvalidGoal, "The goal specified is empty");
       }

       string relevantFunctionsManual = await this._context.GetFunctionsManualAsync(goal, this.Config).ConfigureAwait(false);
       this._context.Variables.Set("available_functions", relevantFunctionsManual);

       this._context.Variables.Update(goal);

       var planResult = await this._functionFlowFunction.InvokeAsync(this._context).ConfigureAwait(false);

       string planResultString = planResult.Result.Trim();

       try
       {
           var plan = planResultString.ToPlanFromXml(goal, this._context);
           return plan;
       }
       catch (Exception e)
       {
           throw new PlanningException(PlanningException.ErrorCodes.InvalidPlan, "Plan parsing error, invalid XML", e);
       }
    */

}
