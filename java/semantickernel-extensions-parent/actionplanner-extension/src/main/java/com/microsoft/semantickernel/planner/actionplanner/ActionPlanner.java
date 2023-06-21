// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.actionplanner;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.planner.PlanningException;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import com.microsoft.semantickernel.textcompletion.CompletionRequestSettings;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import reactor.core.publisher.Mono;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

import javax.annotation.Nullable;

/// <summary>
/// Action Planner allows to select one function out of many, to achieve a given goal.
/// The planner implement the Intent Detection pattern, uses the functions registered
/// in the kernel to see if there's a relevant one, providing instructions to call the
/// function and the rationale used to select it. The planner can also return
/// "no function" is nothing relevant is available.
/// The rationale is currently available only in the prompt, we might include it in
/// the Plan object in future.
/// </summary>
public class ActionPlanner {
    private static final Logger LOGGER = LoggerFactory.getLogger(ActionPlanner.class);

    private static final String StopSequence = "#END-OF-PLAN";
    private static final String SkillName = "this";

    // Planner semantic function
    private final CompletionSKFunction plannerFunction;

    // Context used to access the list of functions in the kernel
    private SKContext context;
    private Kernel kernel;

    // TODO: allow to inject skill store
    /// <summary>
    /// Initialize a new instance of the <see cref="ActionPlanner"/> class.
    /// </summary>
    /// <param name="kernel">The semantic kernel instance.</param>
    /// <param name="prompt">Optional prompt override</param>
    /// <param name="logger">Optional logger</param>
    public ActionPlanner(Kernel kernel, @Nullable String prompt) {
        // Verify.NotNull(kernel);
        String promptTemplate;
        if (prompt == null) {
            promptTemplate = read("skprompt.txt");
        } else {
            promptTemplate = prompt;
        }

        this.plannerFunction =
                SKBuilders.completionFunctions(kernel)
                        .createFunction(
                                promptTemplate,
                                null,
                                SkillName,
                                null,
                                new PromptTemplateConfig.CompletionConfig(
                                        0.0, 0.0, 0.0, 0.0, 1024, new ArrayList<>()));

        kernel.importSkill(this, SkillName);

        this.kernel = kernel;
        this.context = plannerFunction.buildContext();
    }

    public static String read(String file) {
        try (InputStream stream = ActionPlanner.class.getResourceAsStream(file)) {
            byte[] buffer = new byte[stream.available()];
            stream.read(buffer);
            return new String(buffer, StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    public Mono<Plan> createPlanAsync(String goal) {
        if (goal == null || goal.isEmpty()) {
            throw new PlanningException(
                    PlanningException.ErrorCodes.InvalidGoal, "The goal specified is empty");
        }

        context = this.context.update(goal);

        return this.plannerFunction
                .invokeAsync(
                        this.context,
                        new CompletionRequestSettings(0, 0, 0, 0, 2048, new ArrayList<>()))
                .handle(
                        (result, sink) -> {
                            ActionPlanResponse planData;

                            try {
                                planData =
                                        new ObjectMapper()
                                                .readValue(
                                                        result.getResult(),
                                                        ActionPlanResponse.class);
                            } catch (Exception e) {
                                sink.error(
                                        new PlanningException(
                                                PlanningException.ErrorCodes.InvalidPlan,
                                                "Plan parsing error, invalid JSON",
                                                e));
                                return;
                            }

                            if (planData == null) {
                                sink.error(
                                        new PlanningException(
                                                PlanningException.ErrorCodes.InvalidPlan,
                                                "The plan deserialized to a null object"));
                                return;
                            }

                            // Build and return plan
                            Plan plan;
                            if (planData.plan.function.contains(".")) {
                                String[] parts = planData.plan.function.split("\\.", -1);
                                CompletionSKFunction skill =
                                        context.getSkills()
                                                .getFunction(
                                                        parts[0],
                                                        parts[1],
                                                        CompletionSKFunction.class);

                                if (skill == null) {
                                    sink.error(
                                            new PlanningException(
                                                    PlanningException.ErrorCodes.InvalidPlan,
                                                    "Unknown skill " + planData.plan.function));
                                    return;
                                }
                                plan = new Plan(goal, () -> kernel.getSkills(), skill);

                            } else if (!planData.plan.function.isEmpty()) {
                                CompletionSKFunction function =
                                        context.getSkills()
                                                .getFunction(
                                                        planData.plan.function,
                                                        CompletionSKFunction.class);

                                if (function == null) {
                                    sink.error(
                                            new PlanningException(
                                                    PlanningException.ErrorCodes.InvalidPlan,
                                                    "Unknown skill " + planData.plan.function));
                                    return;
                                }

                                plan = new Plan(goal, () -> kernel.getSkills(), function);
                            } else {
                                // No function was found - return a plan with no steps.
                                plan = new Plan(goal, () -> kernel.getSkills());
                            }

                            sink.next(plan);
                        });
    }

    // TODO: use goal to find relevant functions in a skill store
    /// <summary>
    /// Native function returning a list of all the functions in the current context,
    /// excluding functions in the planner itself.
    /// </summary>
    /// <param name="goal">Currently unused. Will be used to handle long lists of functions.</param>
    /// <param name="context">Function execution context</param>
    /// <returns>List of functions, formatted accordingly to the prompt</returns>

    @DefineSKFunction(
            name = "listOfFunctions",
            description = "List all functions available in the kernel")
    @Nullable
    public String listOfFunctions(
            @SKFunctionParameters(
                            name = "goal",
                            description = "The current goal processed by the planner",
                            defaultValue = "")
                    String goal,
            SKContext context) {
        // Verify.NotNull(context.Skills);
        ReadOnlySkillCollection skills = context.getSkills();

        return this.populateList(skills);
    }

    // TODO: generate string programmatically
    // TODO: use goal to find relevant examples
    @DefineSKFunction(
            name = "GoodExamples",
            description = "List a few good examples of plans to generate")
    public String goodExamples(
            @SKFunctionParameters(
                            name = "goal",
                            description = "The current goal processed by the planner",
                            defaultValue = "")
                    String goal,
            SKContext context) {

        return "\n"
                + "[EXAMPLE]\n"
                + "- List of functions:\n"
                + "// Read a file.\n"
                + "FileIOSkill.ReadAsync\n"
                + "Parameter \"path\": Source file.\n"
                + "// Write a file.\n"
                + "FileIOSkill.WriteAsync\n"
                + "Parameter \"path\": Destination file. (default value: sample.txt)\n"
                + "Parameter \"content\": File content.\n"
                + "// Get the current time.\n"
                + "TimeSkill.Time\n"
                + "No parameters.\n"
                + "// Makes a POST request to a uri.\n"
                + "HttpSkill.PostAsync\n"
                + "Parameter \"body\": The body of the request.\n"
                + "- End list of functions.\n"
                + "Goal: create a file called \"something.txt\".\n"
                + "{\"plan\":{\n"
                + "\"rationale\": \"the list contains a function that allows to create files\",\n"
                + "\"function\": \"FileIOSkill.WriteAsync\",\n"
                + "\"parameters\": {\n"
                + "\"path\": \"something.txt\",\n"
                + "\"content\": null\n"
                + "}}}\n"
                + "#END-OF-PLAN\n";
    }

    @DefineSKFunction(
            name = "EdgeCaseExamples",
            description = "List a few edge case examples of plans to handle")
    public String edgeCaseExamples(
            @SKFunctionParameters(
                            name = "goal",
                            description = "The current goal processed by the planner",
                            defaultValue = "")
                    String goal,
            SKContext context) {
        return "\n"
                + "[EXAMPLE]\n"
                + "- List of functions:\n"
                + "// Get the current time.\n"
                + "TimeSkill.Time\n"
                + "No parameters.\n"
                + "// Write a file.\n"
                + "FileIOSkill.WriteAsync\n"
                + "Parameter \"path\": Destination file. (default value: sample.txt)\n"
                + "Parameter \"content\": File content.\n"
                + "// Makes a POST request to a uri.\n"
                + "HttpSkill.PostAsync\n"
                + "Parameter \"body\": The body of the request.\n"
                + "// Read a file.\n"
                + "FileIOSkill.ReadAsync\n"
                + "Parameter \"path\": Source file.\n"
                + "- End list of functions.\n"
                + "Goal: tell me a joke.\n"
                + "{\"plan\":{\n"
                + "\"rationale\": \"the list does not contain functions to tell jokes or"
                + " something funny\",\n"
                + "\"function\": \"\",\n"
                + "\"parameters\": {\n"
                + "}}}\n"
                + "#END-OF-PLAN\n";
    }

    private String populateList(ReadOnlySkillCollection skills) {
        return skills.getAllFunctions().getAll().stream()
                .filter(skill -> !SkillName.equalsIgnoreCase(skill.getSkillName()))
                .map(
                        func -> {
                            StringBuilder result = new StringBuilder();
                            // Function description
                            if (func.getDescription() != null) {
                                result.append("// " + addPeriod(func.getDescription()) + "\n");
                            } else {
                                LOGGER.warn(
                                        "{0}.{1} is missing a description",
                                        func.getSkillName(), func.getName());
                                result.append(
                                        "// Function "
                                                + func.getSkillName()
                                                + "."
                                                + func.getName()
                                                + ".\n");
                            }

                            // Function name
                            result.append(func.getSkillName() + "." + func.getName() + "\n");

                            func.describe()
                                    .getParameters()
                                    .forEach(
                                            parameter -> {
                                                String description;
                                                if (parameter.getDescription() == null
                                                        || parameter.getDefaultValue().isEmpty()) {
                                                    description = parameter.getName();
                                                } else {
                                                    description = parameter.getDescription();
                                                }

                                                String defaultValueString;
                                                if (parameter.getDefaultValue() == null
                                                        || parameter.getDefaultValue().isEmpty()) {
                                                    defaultValueString = "";
                                                } else {
                                                    defaultValueString =
                                                            " (default value: "
                                                                    + parameter.getDefaultValue()
                                                                    + ")";
                                                }

                                                result.append(
                                                        "Parameter \""
                                                                + parameter.getName()
                                                                + "\": "
                                                                + addPeriod(description)
                                                                + " "
                                                                + defaultValueString
                                                                + "\n");
                                            });

                            return result.toString();
                        })
                .reduce("", (a, b) -> a + b, (a, b) -> a + b);
    }

    private static String addPeriod(String x) {
        return x.endsWith(".") ? x : x + ".";
    }
}
