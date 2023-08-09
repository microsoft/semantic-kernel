// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.azure.core.exception.HttpResponseException;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.skilldefinition.FunctionView;
import com.microsoft.semantickernel.skilldefinition.KernelSkillsSupplier;
import com.microsoft.semantickernel.skilldefinition.ParameterView;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import com.microsoft.semantickernel.textcompletion.CompletionRequestSettings;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.UUID;
import java.util.function.BiFunction;
import java.util.stream.Collectors;

import javax.annotation.Nullable;

/// <summary>
/// Standard Semantic Kernel callable function.
/// SKFunction is used to extend one C# <see cref="Delegate"/>, <see cref="Func{T, TResult}"/>, <see
// cref="Action"/>,
/// with additional methods required by the kernel.
/// </summary>
public class DefaultCompletionSKFunction
        extends DefaultSemanticSKFunction<CompletionRequestSettings>
        implements CompletionSKFunction {
    private static final Logger LOGGER = LoggerFactory.getLogger(DefaultCompletionSKFunction.class);

    private final SemanticFunctionConfig functionConfig;
    private SKSemanticAsyncTask<SKContext> function;
    private final CompletionRequestSettings requestSettings;

    @Nullable private DefaultTextCompletionSupplier aiService;

    public DefaultCompletionSKFunction(
            List<ParameterView> parameters,
            String skillName,
            String functionName,
            String description,
            CompletionRequestSettings requestSettings,
            SemanticFunctionConfig functionConfig,
            @Nullable KernelSkillsSupplier kernelSkillsSupplier) {
        super(parameters, skillName, functionName, description, kernelSkillsSupplier);
        // TODO
        // Verify.NotNull(delegateFunction, "The function delegate is empty");
        // Verify.ValidSkillName(skillName);
        // Verify.ValidFunctionName(functionName);
        // Verify.ParametersUniqueness(parameters);
        this.requestSettings = requestSettings;
        this.functionConfig = functionConfig;
    }

    /*
    /// <inheritdoc/>
    public string Name { get; }

    /// <inheritdoc/>
    public string SkillName { get; }

    /// <inheritdoc/>
    public string Description { get; }

    /// <inheritdoc/>
    public bool IsSemantic { get; }

    /// <inheritdoc/>
    public CompleteRequestSettings RequestSettings
    {
        get { return this._aiRequestSettings; }
    }

    /// <summary>
    /// List of function parameters
    /// </summary>
    public IList<ParameterView> Parameters { get; }

    /// <summary>
    /// Create a native function instance, wrapping a native object method
    /// </summary>
    /// <param name="methodContainerInstance">Object containing the method to invoke</param>
    /// <param name="methodSignature">Signature of the method to invoke</param>
    /// <param name="skillName">SK skill name</param>
    /// <param name="log">Application logger</param>
    /// <returns>SK function instance</returns>
    */

    private SKContext buildContext() {
        assertSkillSupplierRegistered();
        return SKBuilders.context()
                .with(SKBuilders.variables().build())
                .with(getSkillsSupplier() == null ? null : getSkillsSupplier().get())
                .build();
    }

    /**
     * Method to aggregate partitioned results of a semantic function
     *
     * @param partitionedInput Input to aggregate
     * @param contextIn Semantic Kernel context
     * @return Aggregated results
     */
    @Override
    public Mono<SKContext> aggregatePartitionedResultsAsync(
            List<String> partitionedInput, @Nullable SKContext contextIn) {

        SKContext context;
        if (contextIn == null) {
            context = buildContext();
        } else {
            context = contextIn;
        }

        // Function that takes the current context, updates it with the latest input and invokes the
        // function
        BiFunction<Flux<SKContext>, String, Flux<SKContext>> executeNextChunk =
                (contextInput, input) ->
                        contextInput.concatMap(
                                newContext -> {
                                    SKContext updated = newContext.copy().update(input);
                                    return invokeAsync(updated, null);
                                });

        Flux<SKContext> results =
                Flux.fromIterable(partitionedInput)
                        .scanWith(() -> Flux.just(context), executeNextChunk)
                        .skip(1) // Skip the first element, which is the initial context
                        .concatMap(it -> it);

        return results.map(
                        result -> {
                            return result.getResult();
                        })
                .collect(Collectors.joining("\n"))
                .map(context::update);
    }

    // Run the semantic function
    @Override
    protected Mono<SKContext> invokeAsyncInternal(
            SKContext context, @Nullable CompletionRequestSettings settings) {
        // TODO
        // this.VerifyIsSemantic();
        // this.ensureContextHasSkills(context);

        if (function == null) {
            throw new FunctionNotRegisteredException(this.getName());
        }

        if (settings == null) {
            settings = this.requestSettings;
        }

        if (this.aiService.get() == null) {
            throw new IllegalStateException("Failed to initialise aiService");
        }

        CompletionRequestSettings finalSettings = settings;

        return function.run(this.aiService.get(), finalSettings, context)
                .map(
                        result -> {
                            return context.update(result.getVariables());
                        });
    }

    @Override
    public void registerOnKernel(Kernel kernel) {
        this.function =
                (TextCompletion client,
                        CompletionRequestSettings requestSettings,
                        SKContext contextInput) -> {
                    SKContext context = contextInput.copy();
                    // TODO
                    // Verify.NotNull(client, "AI LLM backed is empty");

                    PromptTemplate func = functionConfig.getTemplate();

                    return func.renderAsync(context)
                            .flatMapMany(
                                    prompt -> {
                                        LOGGER.debug("RENDERED PROMPT: \n" + prompt);
                                        return client.completeAsync(prompt, requestSettings);
                                    })
                            .single()
                            .map(
                                    completion -> {
                                        return context.update(completion.get(0));
                                    })
                            .doOnError(
                                    ex -> {
                                        LOGGER.warn(
                                                "Something went wrong while rendering the semantic"
                                                        + " function or while executing the text"
                                                        + " completion. Function: {}.{}. Error: {}",
                                                getSkillName(),
                                                getName(),
                                                ex.getMessage());

                                        // Common message when you attempt to send text completion
                                        // requests to a chat completion model:
                                        //    "logprobs, best_of and echo parameters are not
                                        // available on gpt-35-turbo model"
                                        if (ex instanceof HttpResponseException
                                                && ((HttpResponseException) ex)
                                                                .getResponse()
                                                                .getStatusCode()
                                                        == 400
                                                && ex.getMessage()
                                                        .contains(
                                                                "parameters are not available"
                                                                        + " on")) {
                                            LOGGER.warn(
                                                    "This error indicates that you have attempted"
                                                        + " to use a chat completion model in a"
                                                        + " text completion service. Try using a"
                                                        + " chat completion service instead when"
                                                        + " building your kernel, for instance when"
                                                        + " building your service use"
                                                        + " SKBuilders.chatCompletion() rather than"
                                                        + " SKBuilders.textCompletionService().");
                                        }
                                    });
                };

        this.setSkillsSupplier(kernel::getSkills);
        this.aiService = () -> kernel.getService(null, TextCompletion.class);
    }

    @Override
    public Class<CompletionRequestSettings> getType() {
        return CompletionRequestSettings.class;
    }

    private static String randomFunctionName() {
        return "func" + UUID.randomUUID();
    }

    public static DefaultCompletionSKFunction createFunction(
            String promptTemplate,
            @Nullable String functionName,
            @Nullable String skillName,
            @Nullable String description,
            PromptTemplateConfig.CompletionConfig completion,
            PromptTemplateEngine promptTemplateEngine) {

        if (functionName == null) {
            functionName = randomFunctionName();
        }

        if (description == null) {
            description = "Generic function, unknown purpose";
        }

        PromptTemplateConfig config =
                new PromptTemplateConfig(description, "completion", completion);

        return createFunction(
                promptTemplate, config, functionName, skillName, promptTemplateEngine);
    }

    public static DefaultCompletionSKFunction createFunction(
            String promptTemplate,
            PromptTemplateConfig config,
            String functionName,
            @Nullable String skillName,
            PromptTemplateEngine promptTemplateEngine) {
        if (functionName == null) {
            functionName = randomFunctionName();
        }

        // TODO
        // Verify.ValidFunctionName(functionName);
        // if (!string.IsNullOrEmpty(skillName)) {
        //    Verify.ValidSkillName(skillName);
        // }

        PromptTemplate template =
                SKBuilders.promptTemplate()
                        .withPromptTemplateConfig(config)
                        .withPromptTemplate(promptTemplate)
                        .build(promptTemplateEngine);

        // Prepare lambda wrapping AI logic
        SemanticFunctionConfig functionConfig = new SemanticFunctionConfig(config, template);

        return createFunction(skillName, functionName, functionConfig, promptTemplateEngine);
    }

    public static DefaultCompletionSKFunction createFunction(
            String functionName,
            SemanticFunctionConfig functionConfig,
            PromptTemplateEngine promptTemplateEngine) {
        return createFunction(null, functionName, functionConfig, promptTemplateEngine);
    }

    /// <summary>
    /// Create a native function instance, given a semantic function configuration.
    /// </summary>
    /// <param name="skillName">Name of the skill to which the function to create belongs.</param>
    /// <param name="functionName">Name of the function to create.</param>
    /// <param name="functionConfig">Semantic function configuration.</param>
    /// <param name="log">Optional logger for the function.</param>
    /// <returns>SK function instance.</returns>
    public static DefaultCompletionSKFunction createFunction(
            @Nullable String skillNameFinal,
            String functionName,
            SemanticFunctionConfig functionConfig,
            PromptTemplateEngine promptTemplateEngine) {
        String skillName = skillNameFinal;
        // Verify.NotNull(functionConfig, "Function configuration is empty");
        if (skillName == null) {
            skillName = ReadOnlySkillCollection.GlobalSkill;
        }

        CompletionRequestSettings requestSettings =
                CompletionRequestSettings.fromCompletionConfig(
                        functionConfig.getConfig().getCompletionConfig());

        PromptTemplate promptTemplate = functionConfig.getTemplate();

        return new DefaultCompletionSKFunction(
                promptTemplate.getParameters(),
                skillName,
                functionName,
                functionConfig.getConfig().getDescription(),
                requestSettings,
                functionConfig,
                null);
    }

    @Override
    public FunctionView describe() {
        return new FunctionView(
                super.getName(),
                super.getSkillName(),
                super.getDescription(),
                super.getParametersView(),
                true,
                false);
    }
}
