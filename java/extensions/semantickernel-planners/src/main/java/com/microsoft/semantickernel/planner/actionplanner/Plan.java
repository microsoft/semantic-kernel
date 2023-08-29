// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.actionplanner;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.Verify;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.AbstractSkFunction;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.orchestration.WritableContextVariables;
import com.microsoft.semantickernel.skilldefinition.FunctionView;
import com.microsoft.semantickernel.skilldefinition.KernelSkillsSupplier;
import com.microsoft.semantickernel.skilldefinition.ParameterView;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import com.microsoft.semantickernel.textcompletion.CompletionRequestSettings;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import javax.annotation.Nullable;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/** Standard Semantic Kernel callable plan. Plan is used to create trees of SKFunctions. */
public class Plan extends AbstractSkFunction<CompletionRequestSettings> {

    private static final Pattern s_variablesRegex = Pattern.compile("\\$(\\w+)", Pattern.MULTILINE);

    private static final String DefaultResultKey = "PLAN.RESULT";

    // State of the plan
    private ContextVariables state;

    // Steps of the plan
    private final List<Plan> steps = new ArrayList<>();

    // Parameters for the plan, used to pass information to the next step
    @Nullable private ContextVariables parameters;

    // Outputs for the plan, used to pass information to the caller
    private List<String> outputs = new ArrayList<>();

    @Nullable private SKFunction<?> function = null;

    public Plan(
            String goal,
            ContextVariables state,
            @Nullable KernelSkillsSupplier kernelSkillsSupplier) {
        super(new ArrayList<>(), Plan.class.getName(), "", goal, kernelSkillsSupplier);
        this.state = state;
    }

    public Plan(String goal, @Nullable KernelSkillsSupplier kernelSkillsSupplier) {
        this(goal, SKBuilders.variables().build(), kernelSkillsSupplier);
    }

    public Plan(
            SKFunction<?> function,
            ContextVariables state,
            List<String> functionOutputs,
            KernelSkillsSupplier kernelSkillsSupplier) {
        super(
                function.describe().getParameters(),
                function.getSkillName(),
                function.getName(),
                function.getDescription(),
                kernelSkillsSupplier);

        this.parameters = null;
        this.function = function;
        this.outputs = new ArrayList<>(functionOutputs);
        this.state = state;
    }

    public Plan(
            SKFunction<?> function,
            @Nullable ContextVariables parameters,
            ContextVariables state,
            List<String> functionOutputs,
            KernelSkillsSupplier kernelSkillsSupplier) {
        super(
                function.describe().getParameters(),
                function.getSkillName(),
                function.getName(),
                function.getDescription(),
                kernelSkillsSupplier);
        this.parameters = parameters;
        this.function = function;
        this.outputs = new ArrayList<>(functionOutputs);
        this.state = state;
    }

    public Plan(
            SKFunction<?> function,
            List<String> functionOutputs,
            KernelSkillsSupplier kernelSkillsSupplier) {
        this(function, SKBuilders.variables().build(), functionOutputs, kernelSkillsSupplier);
    }

    public Plan(SKFunction<?> function, KernelSkillsSupplier kernelSkillsSupplier) {
        this(function, SKBuilders.variables().build(), new ArrayList<>(), kernelSkillsSupplier);
    }

    public Plan(
            String goal,
            ContextVariables parameters,
            KernelSkillsSupplier kernelSkillsSupplier,
            SKFunction<?>... steps) {
        this(goal, parameters, kernelSkillsSupplier);
        this.addSteps(steps);
    }

    public Plan(String goal, KernelSkillsSupplier kernelSkillsSupplier, SKFunction<?>... steps) {
        this(goal, kernelSkillsSupplier);
        this.addSteps(steps);
    }

    @Override
    public void registerOnKernel(Kernel kernel) {
        kernel.registerSemanticFunction(this);
    }

    @Override
    @Nullable
    public FunctionView describe() {
        if (function == null) {
            return null;
        }
        return function.describe();
    }

    @Override
    @Nullable
    public Class getType() {
        if (function == null) {
            return null;
        }
        return function.getType();
    }

    /**
     * Adds one or more existing plans to the end of the current plan as steps. When you add a plan
     * as a step to the current plan, the steps of the added plan are executed after the steps of
     * the current plan have completed.
     *
     * @param steps The plans to add as steps to the current plan.
     */
    public void addSteps(Plan... steps) {
        this.steps.addAll(Arrays.asList(steps));
    }

    /**
     * Adds one or more new steps to the end of the current plan. When you add a new step to the
     * current plan, it is executed after the previous step in the plan has completed. Each step can
     * be a function call or another plan.
     *
     * @param steps The steps to add to the current plan.
     */
    public void addSteps(SKFunction<?>... steps) {
        List<Plan> plans =
                Arrays.stream(steps)
                        .map(step -> new Plan(step, getSkillsSupplier()))
                        .collect(Collectors.toList());
        this.steps.addAll(plans);
    }

    public void setParameters(ContextVariables functionVariables) {
        this.parameters = functionVariables;
    }

    public void addOutputs(List<String> outputs) {
        this.outputs.addAll(outputs);
    }

    /**
     * Invoke the next step of the plan
     *
     * @param context Context to use
     * @param settings Settings to use
     * @return The updated plan
     */
    public Mono<SKContext> invokeNextStepAsync(
            SKContext context, @Nullable CompletionRequestSettings settings) {

        // Execute the step
        SKContext initialContext =
                SKBuilders.context()
                        .withVariables(context.getVariables().writableClone())
                        .withMemory(context.getSemanticMemory())
                        .withSkills(context.getSkills())
                        .build();

        return Flux.fromIterable(this.steps)
                .reduce(
                        Mono.just(initialContext),
                        (currentContext, step) ->
                                executeStep(context, settings, currentContext, step))
                .flux()
                .concatMap(it -> it)
                .last(SKBuilders.context().build())
                .map(
                        result -> {
                            if (result.getVariables().get(DefaultResultKey) != null) {
                                result = result.update(result.getVariables().get(DefaultResultKey));
                            }
                            return result;
                        });
    }

    private Mono<SKContext> executeStep(
            SKContext context,
            @Nullable CompletionRequestSettings settings,
            Mono<SKContext> currentContext2,
            Plan step) {
        return currentContext2.flatMap(
                currentContext -> {
                    // Merge the state with the current context variables for step execution
                    ContextVariables functionVariables =
                            this.getNextStepVariables(currentContext.getVariables(), step);

                    // Execute the step
                    SKContext functionContext =
                            SKBuilders.context()
                                    .withVariables(functionVariables)
                                    .withMemory(context.getSemanticMemory())
                                    .withSkills(context.getSkills())
                                    .build();

                    return step.invokeAsync(functionContext, settings)
                            .flatMap(
                                    result -> {
                                        String resultValue = result.getResult();
                                        if (resultValue == null) {
                                            return Mono.error(
                                                    new RuntimeException("No result returned"));
                                        }

                                        resultValue = resultValue.trim();

                                        WritableContextVariables updatedContext =
                                                currentContext.getVariables().writableClone();

                                        String finalResultValue = resultValue;

                                        step.outputs.forEach(
                                                item -> {
                                                    if (result.getVariables()
                                                            .asMap()
                                                            .containsKey(item)) {
                                                        String variable =
                                                                result.getVariables().get(item);
                                                        if (variable != null) {
                                                            updatedContext.setVariable(
                                                                    item, variable);
                                                        }
                                                    } else {
                                                        updatedContext.setVariable(
                                                                item, finalResultValue);
                                                    }
                                                });

                                        // If this function produces an output, don't overwrite the
                                        // current
                                        // result
                                        if (step.outputs.size() > 0) {
                                            updatedContext.setVariable(
                                                    ContextVariables.MAIN_KEY,
                                                    currentContext.getResult());
                                        } else {
                                            updatedContext.update(finalResultValue);
                                        }

                                        updatedContext.setVariable(
                                                DefaultResultKey, finalResultValue);

                                        return Mono.just(
                                                SKBuilders.context()
                                                        .clone(context)
                                                        .withVariables(updatedContext)
                                                        .build());
                                    });
                });
    }

    public Mono<SKContext> invokeAsync(
            @Nullable String input,
            @Nullable CompletionRequestSettings settings,
            @Nullable SemanticTextMemory memory) {

        WritableContextVariables variables = state.writableClone();

        if (input != null) {
            variables.update(input);
        }

        KernelSkillsSupplier skillsSupplier = getSkillsSupplier();

        SKContext context =
                SKBuilders.context()
                        .withVariables(variables)
                        .withMemory(memory)
                        .withSkills(skillsSupplier == null ? null : skillsSupplier.get())
                        .build();

        return this.invokeAsync(context, settings);
    }

    @Override
    public Mono<SKContext> invokeAsync(
            @Nullable String input,
            @Nullable SKContext context,
            @Nullable CompletionRequestSettings settings) {
        if (input != null) {
            this.state = state.writableClone().update(input);
        }

        if (context == null) {
            context =
                    SKBuilders.context()
                            .withVariables(state)
                            .withSkills(
                                    getSkillsSupplier() == null ? null : getSkillsSupplier().get())
                            .build();
        } else {
            ContextVariables variables = context.getVariables().writableClone().update(state, true);
            context = context.update(variables);
        }

        return super.invokeAsync(input, context, settings);
    }

    @Override
    protected Mono<SKContext> invokeAsyncInternal(
            SKContext contextIn, @Nullable CompletionRequestSettings settings) {
        if (function != null) {
            return ((SKFunction) function).invokeAsync(contextIn, settings);
        } else {
            // loop through steps and execute until completion
            SKContext c = addVariablesToContext(this.state, contextIn);
            return this.invokeNextStepAsync(c, null);
        }
    }

    /**
     * Expand variables in the input string.
     *
     * @param variables Variables to use for expansion.
     * @param input Input string to expand.
     * @return Expanded string.
     */
    private String expandFromVariables(ContextVariables variables, String input) {
        String result = input;
        Matcher matches = s_variablesRegex.matcher(input);
        while (matches.find()) {

            String varName = matches.group(1);

            String value = variables.get(varName);

            if (value == null) {
                value = state.get(varName);
            }

            if (value == null) {
                value = "";
            }

            result = result.replaceAll("\\$" + varName, value);
        }

        return result;
    }

    /** Add any missing variables from a plan state variables to the context. */
    private static SKContext addVariablesToContext(ContextVariables vars, SKContext context) {
        WritableContextVariables clone = context.getVariables().writableClone();
        vars.asMap()
                .forEach(
                        (key, value) -> {
                            if (Verify.isNullOrEmpty(clone.get(key))) {
                                clone.setVariable(key, value);
                            }
                        });

        return SKBuilders.context().clone(context).withVariables(clone).build();
    }

    /**
     * Get the variables for the next step in the plan.
     *
     * @param variables The current context variables.
     * @param step The next step in the plan.
     * @return The context variables for the next step in the plan.
     */
    private ContextVariables getNextStepVariables(ContextVariables variables, Plan step) {
        // Priority for Input
        // - Parameters (expand from variables if needed)
        // - SKContext.Variables
        // - Plan.State
        // - Empty if sending to another plan
        // - Plan.Description

        String input = "";
        if (step.parameters != null
                && !Verify.isNullOrEmpty(step.parameters.getInput())
                && !step.parameters.getInput().equals(SKFunctionParameters.NO_DEFAULT_VALUE)) {
            input =
                    this.expandFromVariables(
                            variables, Objects.requireNonNull(step.parameters.getInput()));
        } else if (!Verify.isNullOrEmpty(variables.getInput())) {
            input = Objects.requireNonNull(variables.getInput());
        } else if (!Verify.isNullOrEmpty(this.state.getInput())) {
            input = Objects.requireNonNull(this.state.getInput());
        } else if (steps.size() > 0) {
            input = "";
        } else if (!Verify.isNullOrEmpty(this.getDescription())) {
            input = this.getDescription();
        }

        WritableContextVariables stepVariables =
                SKBuilders.variables()
                        .withInput(Objects.requireNonNull(input))
                        .build()
                        .writableClone();

        // Priority for remaining stepVariables is:
        // - Function Parameters (pull from variables or state by a key value)
        // - Step Parameters (pull from variables or state by a key value)
        FunctionView functionParameters = step.describe();
        if (functionParameters != null) {
            for (ParameterView param : functionParameters.getParameters()) {
                if (param.getName().equals(ContextVariables.MAIN_KEY)) {
                    continue;
                }

                if (!Verify.isNullOrEmpty(variables.get(param.getName()))) {
                    String variable = Objects.requireNonNull(variables.get(param.getName()));
                    stepVariables.setVariable(param.getName(), variable);
                } else if (!Verify.isNullOrEmpty(this.state.get(param.getName()))) {
                    String variable = Objects.requireNonNull(this.state.get(param.getName()));
                    stepVariables.setVariable(param.getName(), variable);
                }
            }
        }

        if (step.parameters != null) {
            step.parameters
                    .asMap()
                    .forEach(
                            (key, value) -> {
                                // Don't overwrite variable values that are already set
                                if (!Verify.isNullOrEmpty(stepVariables.get(key))) {
                                    return;
                                }

                                String expandedValue = this.expandFromVariables(variables, value);
                                if (expandedValue != null
                                        && !expandedValue.equalsIgnoreCase(value)) {
                                    stepVariables.setVariable(key, expandedValue);
                                } else if (!Verify.isNullOrEmpty(variables.get(key))) {
                                    String variable = variables.get(key);
                                    if (variable != null) {
                                        stepVariables.setVariable(key, variable);
                                    }
                                } else if (!Verify.isNullOrEmpty(state.get(key))) {
                                    String variable = state.get(key);
                                    if (variable != null) {
                                        stepVariables.setVariable(key, variable);
                                    }
                                } else {
                                    if (expandedValue != null) {
                                        stepVariables.setVariable(key, expandedValue);
                                    }
                                }
                            });
        }

        return stepVariables;
    }

    public String toPlanString() {
        return toPlanString("  ");
    }

    private String toPlanString(String indent) {
        String goalHeader = indent + "Goal: " + getDescription() + "\n\n" + indent + "Steps:\n";

        String stepItems =
                steps.stream()
                        .map(step -> stepToString(indent, step))
                        .collect(Collectors.joining("\n"));

        return goalHeader + stepItems;
    }

    private static String stepToString(String indent, Plan step) {
        if (step.steps.size() == 0) {
            String skillName = step.getSkillName();
            String stepName = step.getName();

            String parameters =
                    step.getParametersView().stream()
                            .map(
                                    param -> {
                                        String value = param.getDefaultValue();
                                        if (step.getParameters() != null
                                                && step.getParameters().get(param.getName())
                                                        != null) {
                                            value = step.getParameters().get(param.getName());
                                        }
                                        return "\t" + param.getName() + ": \"" + value + "\"";
                                    })
                            .collect(Collectors.joining(" "));

            if (!Verify.isNullOrEmpty(parameters)) {
                parameters = " " + parameters;
            }

            String outputs = step.outputs.stream().findFirst().orElse("");
            if (!Verify.isNullOrEmpty(outputs)) {
                outputs = " => " + outputs;
            }

            return indent
                    + indent
                    + "- "
                    + String.join(".", skillName, stepName)
                    + "\t\t\t"
                    + parameters
                    + outputs;
        }

        return step.toPlanString(indent + indent);
    }

    @Nullable
    private ContextVariables getParameters() {
        return parameters;
    }
}
