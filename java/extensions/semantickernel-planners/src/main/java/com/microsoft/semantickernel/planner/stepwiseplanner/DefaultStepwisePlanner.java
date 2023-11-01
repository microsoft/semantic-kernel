// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.stepwiseplanner;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.Verify;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.planner.PlanningException;
import com.microsoft.semantickernel.planner.PlanningException.ErrorCodes;
import com.microsoft.semantickernel.planner.actionplanner.Plan;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.skilldefinition.FunctionView;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import com.microsoft.semantickernel.textcompletion.CompletionRequestSettings;
import com.microsoft.semantickernel.util.EmbeddedResourceLoader;
import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.BiFunction;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.publisher.SynchronousSink;

/// <summary>
/// A planner that creates a Stepwise plan using Mrkl systems.
/// </summary>
/// <remark>
/// An implementation of a Mrkl system as described in https://arxiv.org/pdf/2205.00445.pdf
/// </remark>

/**
 * A planner that creates a Stepwise plan using Mrkl systems.
 *
 * <p>An implementation of a Mrkl system as described in https://arxiv.org/pdf/2205.00445.pdf
 */
public class DefaultStepwisePlanner implements StepwisePlanner {

    private static final Logger LOGGER = LoggerFactory.getLogger(DefaultStepwisePlanner.class);

    /** The name to use when creating semantic functions that are restricted from plan creation */
    private static final String RESTRICTED_SKILL_NAME = "StepwisePlanner_Excluded";

    /** The prefix used for the scratch pad */
    private static final String SCRATCH_PAD_PREFIX =
            "This was my previous work (but they haven't seen any of it! They only see what I"
                    + " return as final answer):";

    /** The Thought tag */
    private static final String THOUGHT = "[THOUGHT]";

    /** The Observation tag */
    private static final String OBSERVATION = "[OBSERVATION]";

    /** The Action tag */
    private static final String Action = "[ACTION]";

    /** The regex for parsing the final answer response */
    private static final Pattern S_FINAL_ANSWER_REGEX =
            Pattern.compile(
                    "\\[FINAL ANSWER\\](?<finalanswer>.+)", Pattern.MULTILINE | Pattern.DOTALL);

    /** The regex for parsing the thought response */
    private static final Pattern S_THOUGHT_REGEX =
            Pattern.compile("(\\[THOUGHT\\])?(?<thought>.+)", Pattern.MULTILINE | Pattern.DOTALL);

    private static final Pattern s_thoughtActionRemoveRegex =
            Pattern.compile("(.*)^\\[ACTION\\].+", Pattern.MULTILINE | Pattern.DOTALL);

    private static final Pattern S_ACTION_REGEX =
            Pattern.compile(
                    "\\[ACTION\\][^{}]*((?:\\{|\\{\\{)(?:[^{}]*\\{[^{}]*\\})*[^{}]*(?:\\}|\\}\\}))$",
                    Pattern.MULTILINE | Pattern.DOTALL);

    private final Kernel kernel;
    private final StepwisePlannerConfig config;
    private final SKFunction<?> systemStepFunction;
    private final SKContext context;
    private final ReadOnlyFunctionCollection nativeFunctions;

    /**
     * Initialize a new instance of the {@link StepwisePlanner} class.
     *
     * @param kernel The semantic kernel instance.
     * @param config Optional configuration object
     * @param prompt Optional prompt override
     * @param promptUserConfig Optional prompt config override
     */
    public DefaultStepwisePlanner(
            Kernel kernel,
            @Nullable StepwisePlannerConfig config,
            @Nullable String prompt,
            @Nullable PromptTemplateConfig promptUserConfig) {
        Verify.notNull(kernel);
        this.kernel = kernel;

        if (config == null) {
            config = new StepwisePlannerConfig();
        }

        this.config = config;
        this.config.addExcludedSkills(RESTRICTED_SKILL_NAME);

        PromptTemplateConfig promptConfig;
        if (promptUserConfig == null) {
            String promptConfigString = null;
            try {
                promptConfigString =
                        EmbeddedResourceLoader.readFile(
                                "config.json", DefaultStepwisePlanner.class);
                if (!Verify.isNullOrEmpty(promptConfigString)) {
                    promptConfig =
                            new ObjectMapper()
                                    .readValue(promptConfigString, PromptTemplateConfig.class);
                } else {
                    promptConfig = new PromptTemplateConfig();
                }
            } catch (FileNotFoundException | JsonProcessingException e) {
                throw new PlanningException(
                        PlanningException.ErrorCodes.INVALID_CONFIGURATION,
                        "Could not find or parse config.json",
                        e);
            }
        } else {
            promptConfig = promptUserConfig;
        }

        if (prompt == null) {
            try {
                prompt =
                        EmbeddedResourceLoader.readFile(
                                "skprompt.txt", DefaultStepwisePlanner.class);
            } catch (FileNotFoundException e) {
                throw new PlanningException(
                        PlanningException.ErrorCodes.INVALID_CONFIGURATION,
                        "Could not find skprompt.txt",
                        e);
            }
        }

        promptConfig =
                new PromptTemplateConfig(
                        promptConfig.getSchema(),
                        promptConfig.getDescription(),
                        promptConfig.getType(),
                        promptConfig.getServiceId(),
                        new PromptTemplateConfig.CompletionConfigBuilder(
                                        promptConfig.getCompletionConfig())
                                .maxTokens(this.config.getMaxTokens())
                                .build(),
                        promptConfig.getInput());

        this.systemStepFunction = this.importStepwiseFunction(this.kernel, prompt, promptConfig);

        this.nativeFunctions = this.kernel.importSkill(this, RESTRICTED_SKILL_NAME);

        this.context = SKBuilders.context().withKernel(kernel).build();
    }

    /**
     * Create a plan for the specified goal.
     *
     * @param goal The goal to create a plan for.
     * @return The plan.
     */
    public Plan createPlan(String goal) {
        if (Verify.isNullOrEmpty(goal)) {
            throw new PlanningException(ErrorCodes.INVALID_GOAL, "The goal specified is empty");
        }

        String functionDescriptions = this.getFunctionDescriptions();

        SKFunction<?> planStep = nativeFunctions.getFunction("ExecutePlan", SKFunction.class);

        ContextVariables parameters =
                SKBuilders.variables()
                        .withVariable("functionDescriptions", functionDescriptions)
                        .withVariable("question", goal)
                        .build();
        /*
            planStep.addOutputs(Arrays.asList("agentScratchPad", "stepCount", "skillCount", "stepsTaken"));
        */
        return new Plan(goal, parameters, kernel::getSkills, planStep);
    }

    /**
     * Execute a plan.
     *
     * @param question The question to answer
     * @param functionDescriptions List of tool descriptions
     * @param context The context
     * @return Result of the plan
     */
    @DefineSKFunction(description = "Execute a plan", name = "ExecutePlan")
    public Mono<SKContext> executePlanAsync(
            @SKFunctionParameters(name = "question", description = "The question to answer")
                    String question,
            @SKFunctionParameters(
                            name = "functionDescriptions",
                            description = "List of tool descriptions")
                    String functionDescriptions,
            SKContext context) {

        if (!Verify.isNullOrEmpty(question)) {

            return Flux.generate(
                            () -> Mono.just(new ArrayList<>()), loopThroughStepExecutions(context))
                    .concatMap(it -> it)
                    .filter(
                            stepsTaken -> {
                                return !stepsTaken.isEmpty()
                                        && stepsTaken.get(stepsTaken.size() - 1).getFinalAnswer()
                                                != null;
                            })
                    .take(1)
                    .single()
                    .map(
                            stepsTaken -> {
                                return returnFinalAnswer(
                                        context, stepsTaken.get(stepsTaken.size() - 1), stepsTaken);
                            });
        } else {
            return Mono.just(context.update("Question not found."));
        }
    }

    /**
     * Loops calling executeNextStep until a final answer is found or max iterations hit.
     *
     * @param context The context
     */
    private BiFunction<
                    Mono<ArrayList<SystemStep>>,
                    SynchronousSink<Mono<ArrayList<SystemStep>>>,
                    Mono<ArrayList<SystemStep>>>
            loopThroughStepExecutions(SKContext context) {

        AtomicInteger stepIndex = new AtomicInteger(0);

        return (stepsTakenFlux, sink) -> {
            sink.next(stepsTakenFlux);

            return stepsTakenFlux.flatMap(
                    stepsTaken -> {
                        if (stepIndex.get() > this.config.getMaxIterations()) {
                            return Mono.error(
                                    new PlanningException(
                                            ErrorCodes.PLAN_EXECUTION_PRODUCED_NO_RESULTS,
                                            "Max iterations exceeded"));
                        }

                        // If we have a final answer, we're done, _SHOULD_ not happen
                        if (stepsTaken.size() > 1
                                && !Verify.isNullOrEmpty(
                                        stepsTaken.get(stepsTaken.size() - 1).getFinalAnswer())) {
                            return Mono.just(stepsTaken);
                        }

                        return executeNextStep(context, stepIndex.incrementAndGet(), stepsTaken);
                    });
        };
    }

    private Mono<ArrayList<SystemStep>> executeNextStep(
            SKContext context, Integer stepIndex, ArrayList<SystemStep> stepsTaken) {
        String scratchPad = this.createScratchPad(stepsTaken);

        context.setVariable("agentScratchPad", scratchPad);

        return systemStepFunction
                .invokeAsync(context)
                .flatMap(
                        llmResponse -> {
                            String actionText =
                                    Objects.requireNonNull(llmResponse.getResult()).trim();
                            LOGGER.trace("Response: " + actionText);

                            SystemStep nextStep = this.parseResult(actionText);

                            stepsTaken.add(nextStep);

                            if (!Verify.isNullOrEmpty(nextStep.getFinalAnswer())) {
                                return Mono.just(stepsTaken);
                            } else {
                                LOGGER.trace("Thought: {}", nextStep.getThought());

                                if (!Verify.isNullOrEmpty(nextStep.getAction())) {
                                    LOGGER.info(
                                            "Action: {}. Iteration: {}.",
                                            nextStep.getAction(),
                                            stepIndex + 1);
                                    try {
                                        LOGGER.trace(
                                                "Action: {}({}). Iteration: {}.",
                                                nextStep.getAction(),
                                                new ObjectMapper()
                                                        .writeValueAsString(
                                                                nextStep.getActionVariables()),
                                                stepIndex + 1);
                                    } catch (JsonProcessingException e) {
                                        return Mono.error(
                                                new PlanningException(
                                                        ErrorCodes.UNKNOWN_ERROR,
                                                        "Could not serialize action variables",
                                                        e));
                                    }

                                    return this.invokeActionAsync(
                                                    nextStep.getAction(),
                                                    nextStep.getActionVariables())
                                            .flatMap(
                                                    result -> {
                                                        if (Verify.isNullOrEmpty(result)) {
                                                            nextStep.setObservation(
                                                                    "Got no result from action");
                                                        } else {
                                                            nextStep.setObservation(result);
                                                        }

                                                        LOGGER.trace(
                                                                "Observation: {}",
                                                                nextStep.getObservation());

                                                        return Mono.just(stepsTaken);
                                                    });

                                } else {
                                    LOGGER.info("Action: No action to take");
                                    return Mono.just(stepsTaken);
                                }
                            }
                        });
    }

    private SKContext returnFinalAnswer(
            SKContext context, SystemStep nextStep, List<SystemStep> stepsTaken) {
        LOGGER.trace("Final Answer: {}", nextStep.getFinalAnswer());

        context = context.update(nextStep.getFinalAnswer());
        String updatedScratchPlan = this.createScratchPad(stepsTaken);
        context.setVariable("agentScratchPad", updatedScratchPlan);

        // Add additional results to the context
        try {
            this.addExecutionStatsToContext(stepsTaken, context);
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }

        return context;
    }

    private SystemStep parseResult(String input) {
        SystemStep result = new SystemStep();
        result.setOriginalResponse(input);

        // Extract final answer
        Matcher finalAnswerMatch = S_FINAL_ANSWER_REGEX.matcher(input);

        if (finalAnswerMatch.find()) {
            result.setFinalAnswer(finalAnswerMatch.group(1).trim());
            return result;
        }

        // Extract thought
        Matcher thoughtMatch = S_THOUGHT_REGEX.matcher(input);

        if (thoughtMatch.find()) {
            Matcher actionRemove =
                    s_thoughtActionRemoveRegex.matcher(thoughtMatch.group("thought"));
            if (actionRemove.find()) {
                result.setThought(actionRemove.group(1).trim());
            } else {
                result.setThought(thoughtMatch.group("thought").trim());
            }

        } else if (!input.contains(Action)) {
            result.setThought(input);
        } else {
            throw new IllegalStateException("Unexpected input format");
        }

        result.setThought(Objects.requireNonNull(result.getThought()).replace(THOUGHT, "").trim());

        // Extract action
        Matcher actionMatch = S_ACTION_REGEX.matcher(input);

        if (actionMatch.find()) {
            String json = actionMatch.group(1).trim().replace("`", "");

            // Seen this in some cases, not sure why
            if (json.startsWith("{{")) {
                json = json.replaceAll("^\\{\\{", "{");
                json = json.replaceAll("\\}\\}$", "}");
            }

            try {

                SystemStep systemStepResults = new ObjectMapper().readValue(json, SystemStep.class);

                if (systemStepResults == null) {
                    result.setObservation("System step parsing error, empty JSON: {json}");
                } else {
                    result.setAction(systemStepResults.getAction());
                    result.setActionVariables(systemStepResults.getActionVariables());
                }
            } catch (JsonProcessingException e) {
                result.setObservation("System step parsing error, invalid JSON: " + json);
            }
        }

        if (Verify.isNullOrEmpty(result.getThought()) && Verify.isNullOrEmpty(result.getAction())) {
            result.setObservation(
                    "System step error, no thought or action found. Please give a valid thought"
                            + " and/or action.");
        }

        return result;
    }

    private void addExecutionStatsToContext(List<SystemStep> stepsTaken, SKContext context)
            throws JsonProcessingException {
        context.setVariable("stepCount", Integer.toString(stepsTaken.size()));
        context.setVariable("stepsTaken", new ObjectMapper().writeValueAsString(stepsTaken));

        Map<String, Integer> actionCounts = new HashMap<>();

        stepsTaken.stream()
                .filter(step -> !Verify.isNullOrEmpty(step.getAction()))
                .forEach(
                        step -> {
                            if (!actionCounts.containsKey(step.getAction())) {
                                actionCounts.put(step.getAction(), 0);
                            }

                            actionCounts.put(
                                    step.getAction(), actionCounts.get(step.getAction()) + 1);
                        });

        String skillCallListWithCounts =
                actionCounts.keySet().stream()
                        .map(skill -> skill + "(" + actionCounts.get(skill) + ")")
                        .collect(Collectors.joining(", "));

        String skillCallCountStr =
                actionCounts.values().stream().reduce(0, Integer::sum).toString();

        context.setVariable("skillCount", skillCallCountStr + " (" + skillCallListWithCounts + ")");
    }

    private String createScratchPad(List<SystemStep> stepsTaken) {
        if (stepsTaken.isEmpty()) {
            return "";
        }

        List<String> scratchPadLines = new ArrayList<>();

        // Add the original first thought
        scratchPadLines.add(SCRATCH_PAD_PREFIX);
        scratchPadLines.add(THOUGHT + " " + stepsTaken.get(0).getThought());

        // Keep track of where to insert the next step
        int insertPoint = scratchPadLines.size();

        // Keep the most recent steps in the scratch pad.
        for (int i = stepsTaken.size() - 1; i >= 0; i--) {
            if (scratchPadLines.size() / 4.0 > (this.config.getMaxTokens() * 0.75)) {
                LOGGER.debug("Scratchpad is too long, truncating. Skipping " + (i + 1) + " steps.");
                break;
            }

            SystemStep s = stepsTaken.get(i);

            if (!Verify.isNullOrEmpty(s.getObservation())) {
                scratchPadLines.add(insertPoint, OBSERVATION + " " + s.getObservation());
            }

            if (!Verify.isNullOrEmpty(s.getAction())) {
                try {
                    scratchPadLines.add(
                            insertPoint,
                            Action
                                    + " {{"
                                    + "\"action\": \""
                                    + s.getAction()
                                    + "\","
                                    + "\"action_variables\": "
                                    + new ObjectMapper().writeValueAsString(s.getActionVariables())
                                    + "}}");

                } catch (JsonProcessingException e) {
                    throw new RuntimeException(e);
                }
            }

            if (i != 0) {
                scratchPadLines.add(insertPoint, THOUGHT + " " + s.getThought());
            }
        }

        String scratchPad = String.join("\n", scratchPadLines).trim();

        if (!Verify.isNullOrWhiteSpace(scratchPad)) {
            LOGGER.trace("Scratchpad: " + scratchPad);
        }

        return scratchPad;
    }

    private Mono<String> invokeActionAsync(String actionName, Map<String, String> actionVariables) {
        List<SKFunction<?>> availableFunctions = this.getAvailableFunctions();
        Optional<SKFunction<?>> targetFunction =
                availableFunctions.stream()
                        .filter(
                                f -> {
                                    return f.toFullyQualifiedName().equals(actionName)
                                            || f.toFullyQualifiedName()
                                                    .equals(
                                                            ReadOnlySkillCollection.GlobalSkill
                                                                    + "."
                                                                    + actionName)
                                            || f.toFullyQualifiedName()
                                                    .equals("GLOBAL_FUNCTIONS." + actionName);
                                })
                        .findFirst();

        if (!targetFunction.isPresent()) {
            throw new PlanningException(
                    ErrorCodes.UNKNOWN_ERROR, "The function '" + actionName + "' was not found.");
        }

        SKFunction<?> function =
                kernel.getFunction(
                        targetFunction.get().getSkillName(), targetFunction.get().getName());

        SKContext actionContext = this.createActionContext(actionVariables);

        return function.invokeAsync(actionContext)
                .mapNotNull(
                        result -> {
                            LOGGER.trace(
                                    "Invoked {}. Result: {}",
                                    targetFunction.get().getName(),
                                    result.getResult());
                            return result.getResult();
                        });
    }

    private SKContext createActionContext(Map<String, String> actionVariables) {
        SKContext actionContext = SKBuilders.context().withKernel(this.kernel).build();

        if (actionVariables != null) {
            actionVariables.forEach(actionContext::setVariable);
        }

        return actionContext;
    }

    private List<SKFunction<?>> getAvailableFunctions() {
        return this.context.getSkills().getAllFunctions().getAll().stream()
                .filter(
                        fun ->
                                !this.config.getExcludedSkills().contains(fun.getSkillName())
                                        && !this.config
                                                .getExcludedFunctions()
                                                .contains(fun.getName()))
                .sorted(
                        (a, b) ->
                                Comparator.<SKFunction<?>, String>comparing(
                                                SKFunction::getSkillName)
                                        .thenComparing(SKFunction::getName)
                                        .compare(a, b))
                .collect(Collectors.toList());
    }

    private String getFunctionDescriptions() {
        List<SKFunction<?>> availableFunctions = this.getAvailableFunctions();

        return availableFunctions.stream()
                .map(x -> toManualString(Objects.requireNonNull(x.describe())))
                .collect(Collectors.joining("\n"));
    }

    private SKFunction<CompletionRequestSettings> importStepwiseFunction(
            Kernel kernel, String promptTemplate, PromptTemplateConfig config) {
        PromptTemplate template =
                SKBuilders.promptTemplate()
                        .withPromptTemplate(promptTemplate)
                        .withPromptTemplateConfig(config)
                        .withPromptTemplateEngine(kernel.getPromptTemplateEngine())
                        .build();

        SemanticFunctionConfig functionConfig = new SemanticFunctionConfig(config, template);

        return kernel.registerSemanticFunction(
                RESTRICTED_SKILL_NAME, "StepwiseStep", functionConfig);
    }

    private static String toManualString(FunctionView function) {
        String inputs =
                function.getParameters().stream()
                        .map(
                                parameter -> {
                                    String defaultValueString = "";

                                    if (!Verify.isNullOrEmpty(parameter.getDefaultValue())
                                            && !parameter
                                                    .getDefaultValue()
                                                    .equals(
                                                            SKFunctionParameters
                                                                    .NO_DEFAULT_VALUE)) {
                                        defaultValueString =
                                                "(default='" + parameter.getDefaultValue() + "')";
                                    }

                                    return "  - "
                                            + parameter.getName()
                                            + ": "
                                            + parameter.getDescription()
                                            + " "
                                            + defaultValueString;
                                })
                        .collect(Collectors.joining("\n"));

        String functionDescription = function.getDescription().trim();

        if (Verify.isNullOrEmpty(inputs)) {
            return toFullyQualifiedName(function) + ": " + functionDescription + "\n";
        }

        return toFullyQualifiedName(function) + ": " + functionDescription + "\n" + inputs + "\n";
    }

    private static String toFullyQualifiedName(FunctionView function) {
        return function.getSkillName() + "." + function.getName();
    }
}
