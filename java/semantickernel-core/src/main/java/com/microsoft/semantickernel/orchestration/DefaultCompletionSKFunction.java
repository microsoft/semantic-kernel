// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration; // Copyright (c) Microsoft. All rights reserved.

import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.semanticfunctions.DefaultPromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.skilldefinition.ParameterView;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.textcompletion.*;

import reactor.core.publisher.Mono;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.function.Supplier;

import javax.annotation.Nullable;

/// <summary>
/// Standard Semantic Kernel callable function.
/// SKFunction is used to extend one C# <see cref="Delegate"/>, <see cref="Func{T, TResult}"/>, <see
// cref="Action"/>,
/// with additional methods required by the kernel.
/// </summary>
public class DefaultCompletionSKFunction
        extends DefaultSemanticSKFunction<CompletionRequestSettings, CompletionSKContext>
        implements CompletionSKFunction {
    private final SKSemanticAsyncTask<CompletionSKContext> function;
    private final CompletionRequestSettings aiRequestSettings;
    private final Supplier<TextCompletion> aiService;

    public DefaultCompletionSKFunction(
            DelegateTypes delegateType,
            SKSemanticAsyncTask<CompletionSKContext> delegateFunction,
            List<ParameterView> parameters,
            String skillName,
            String functionName,
            String description,
            Supplier<ReadOnlySkillCollection> skillCollection,
            CompletionRequestSettings aiRequestSettings,
            Supplier<TextCompletion> aiService) {
        super(delegateType, parameters, skillName, functionName, description, skillCollection);
        // TODO
        // Verify.NotNull(delegateFunction, "The function delegate is empty");
        // Verify.ValidSkillName(skillName);
        // Verify.ValidFunctionName(functionName);
        // Verify.ParametersUniqueness(parameters);

        this.function = delegateFunction;
        this.aiRequestSettings = aiRequestSettings;
        this.aiService = aiService;
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

    @Override
    public CompletionSKContext buildContext(
            ReadOnlyContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable Supplier<ReadOnlySkillCollection> skills) {
        return new DefaultCompletionSKContext(variables, memory, skills);
    }

    // Run the semantic function
    @Override
    protected Mono<CompletionSKContext> invokeAsyncInternal(
            CompletionSKContext context, @Nullable CompletionRequestSettings settings) {
        // TODO
        // this.VerifyIsSemantic();
        // this.ensureContextHasSkills(context);

        if (settings == null) {
            settings = this.aiRequestSettings;
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
    public Class<CompletionRequestSettings> getType() {
        return CompletionRequestSettings.class;
    }

    private static String randomFunctionName() {
        return "func" + UUID.randomUUID();
    }

    public static CompletionFunctionDefinition createFunction(
            String promptTemplate,
            @Nullable String functionName,
            @Nullable String skillName,
            @Nullable String description,
            int maxTokens,
            double temperature,
            double topP,
            double presencePenalty,
            double frequencyPenalty,
            @Nullable List<String> stopSequences) {

        if (functionName == null) {
            functionName = randomFunctionName();
        }

        if (description == null) {
            description = "Generic function, unknown purpose";
        }

        if (stopSequences == null) {
            stopSequences = new ArrayList<>();
        }

        PromptTemplateConfig.CompletionConfig completion =
                new PromptTemplateConfig.CompletionConfig(
                        temperature,
                        topP,
                        presencePenalty,
                        frequencyPenalty,
                        maxTokens,
                        stopSequences);

        PromptTemplateConfig config =
                new PromptTemplateConfig(description, "completion", completion);

        return createFunction(promptTemplate, config, functionName, skillName);
    }

    public static CompletionFunctionDefinition createFunction(
            String promptTemplate,
            PromptTemplateConfig config,
            String functionName,
            @Nullable String skillName) {
        if (functionName == null) {
            functionName = randomFunctionName();
        }

        // TODO
        // Verify.ValidFunctionName(functionName);
        // if (!string.IsNullOrEmpty(skillName)) {
        //    Verify.ValidSkillName(skillName);
        // }

        PromptTemplate template = new DefaultPromptTemplate(promptTemplate, config);

        // Prepare lambda wrapping AI logic
        SemanticFunctionConfig functionConfig = new SemanticFunctionConfig(config, template);

        return createFunction(skillName, functionName, functionConfig);
    }

    public static CompletionFunctionDefinition createFunction(
            String functionName, SemanticFunctionConfig functionConfig) {
        return createFunction(null, functionName, functionConfig);
    }

    /// <summary>
    /// Create a native function instance, given a semantic function configuration.
    /// </summary>
    /// <param name="skillName">Name of the skill to which the function to create belongs.</param>
    /// <param name="functionName">Name of the function to create.</param>
    /// <param name="functionConfig">Semantic function configuration.</param>
    /// <param name="log">Optional logger for the function.</param>
    /// <returns>SK function instance.</returns>
    public static CompletionFunctionDefinition createFunction(
            @Nullable String skillNameFinal,
            String functionName,
            SemanticFunctionConfig functionConfig) {
        return CompletionFunctionDefinition.of(
                (kernel) -> {
                    String skillName = skillNameFinal;
                    // Verify.NotNull(functionConfig, "Function configuration is empty");
                    if (skillName == null) {
                        skillName = ReadOnlySkillCollection.GlobalSkill;
                    }

                    SKSemanticAsyncTask<CompletionSKContext> localFunc =
                            (TextCompletion client,
                                    CompletionRequestSettings requestSettings,
                                    CompletionSKContext context) -> {
                                // TODO
                                // Verify.NotNull(client, "AI LLM backed is empty");

                                return functionConfig
                                        .getTemplate()
                                        .renderAsync(context, kernel.getPromptTemplateEngine())
                                        .flatMapMany(
                                                prompt -> {
                                                    return client.completeAsync(
                                                            prompt, requestSettings);
                                                })
                                        .single()
                                        .map(
                                                completion -> {
                                                    return context.update(completion.get(0));
                                                })
                                        .doOnError(
                                                ex -> {
                                                    System.err.println(ex.getMessage());
                                                    ex.printStackTrace();
                                                    // TODO
                                                    /*
                                                    log ?.LogWarning(ex,
                                                        "Something went wrong while rendering the semantic function or while executing the text completion. Function: {0}.{1}. Error: {2}",
                                                        skillName, functionName, ex.Message);
                                                    context.Fail(ex.Message, ex);
                                                     */
                                                });
                            };

                    CompletionRequestSettings requestSettings =
                            CompletionRequestSettings.fromCompletionConfig(
                                    functionConfig.getConfig().getCompletionConfig());

                    return new DefaultCompletionSKFunction(
                            DelegateTypes.ContextSwitchInSKContextOutTaskSKContext,
                            localFunc,
                            functionConfig.getTemplate().getParameters(),
                            skillName,
                            functionName,
                            functionConfig.getConfig().getDescription(),
                            kernel::getSkillCollection,
                            requestSettings,
                            () -> kernel.getService(null, TextCompletion.class));
                });
    }
}
