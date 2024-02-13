// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.Todo;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.semanticfunctions.InputVariable;
import com.microsoft.semantickernel.semanticfunctions.OutputVariable;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateFactory;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.annotation.Nullable;

import reactor.core.publisher.Mono;

/**
 * Semantic Kernel callable function interface. The Semantic Kernel creates 
 * {@code KernelFunction}s from prompts, templates, or plugin methods.  
 *
 * @param <T> The type of the result of the function
 * @see com.microsoft.semantickernel.semanticfunctions
 * @see com.microsoft.semantickernel.plugin
 * @see com.microsoft.semantickernel.plugin.annotations
 */
public abstract class KernelFunction<T> implements Buildable {

    private final KernelFunctionMetadata<?> metadata;

    @Nullable
    private final Map<String, PromptExecutionSettings> executionSettings;

    /**
     * Create a new instance of KernelFunction.
     *
     * @param metadata          The metadata for the function
     * @param executionSettings The execution settings for the function
     * @see com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt
     * @see com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromMethod
     */
    protected KernelFunction(
        KernelFunctionMetadata<?> metadata,
        @Nullable
        Map<String, PromptExecutionSettings> executionSettings) {
        this.metadata = metadata;
        this.executionSettings = new HashMap<>();
        if (executionSettings != null) {
            this.executionSettings.putAll(executionSettings);
        }
    }

    /**
     * @return The name of the skill that this function is within
     */
    public String getSkillName() {
        return metadata.getName();
    }

    /**
     * @return The name of this function
     */
    public String getName() {
        return metadata.getName();
    }

    /**
     * @return A description of the function
     */
    @Nullable
    public String getDescription() {
        return metadata.getDescription();
    }

    /**
     * Create a string for generating an embedding for a function.
     *
     * @return A string for generating an embedding for a function.
     */
    public String toEmbeddingString() {
        throw new Todo();
    }

    /**
     * Create a manual-friendly string for a function.
     *
     * @param includeOutputs Whether to include function outputs in the string.
     * @return A manual-friendly string for a function.
     */
    public String toManualString(boolean includeOutputs) {
        throw new Todo();
    }

    public Map<String, PromptExecutionSettings> getExecutionSettings() {
        return Collections.unmodifiableMap(executionSettings);
    }

    public KernelFunctionMetadata<?> getMetadata() {
        return metadata;
    }

    /**
     * Invokes this KernelFunction.
     * <p>
     * If the {@code variableType} parameter is provided, the {@link ContextVarialbeType} is used to
     * convert the result of the function to the the appropriate {@link FunctionResultType}. The
     * {@code variableType} is not required for converting well-known types such as {@link String}
     * and {@link Integer} which have pre-defined {@code ContextVariableType}s.
     * <p>
     * The {@link InvocationContext} allows for customization of the behavior of function, including
     * the ability to pass in {@link KernelHooks} {@link PromptExecutionSettings}, and
     * {@link ToolCallBehavior}.
     * <p>
     * The difference between calling the {@code KernelFunction.invokeAsync} method directly and
     * calling the {@code Kernel.invokeAsync} method is that the latter adds the
     * {@link KernelHooks#getGlobalHooks() global KernelHooks} (if any) to the
     * {@link InvocationContext}. Calling {@code KernelFunction.invokeAsync} directly does not add
     * the global hooks.
     *
     * @param kernel            The Kernel containing services, plugins, and other state for use
     *                          throughout the operation.
     * @param arguments         The arguments to pass to the function's invocation
     * @param variableType      The type of the {@link ContextVariable} returned in the
     *                          {@link FunctionResult}
     * @param invocationContext The arguments to pass to the function's invocation
     * @return The result of the function's execution.
     * @see FunctionResult#getResultVariable()
     */
    protected abstract Mono<FunctionResult<T>> invokeAsync(
        Kernel kernel,
        @Nullable KernelFunctionArguments arguments,
        @Nullable ContextVariableType<T> variableType,
        @Nullable InvocationContext invocationContext);

    public FunctionInvocation<T> invokeAsync(Kernel kernel) {
        return new FunctionInvocation<>(kernel, this);
    }

    /**
     * Builder for creating a {@link KernelFunction} from a prompt.
     *
     * @param <T> The type of the result of the function
     * @see com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt.Builder
     */
    public interface FromPromptBuilder<T> {

        /**
         * Set the name of the function.
         *
         * @param name The name of the function
         * @return The builder
         */
        FromPromptBuilder<T> withName(@Nullable String name);

        /**
         * Set the input parameters for the function.
         *
         * @param inputVariables The input parameters for the function
         * @return The builder
         */
        FromPromptBuilder<T> withInputParameters(
            @Nullable List<InputVariable> inputVariables);

        /**
         * Set the prompt template for the function.
         * @param promptTemplate The prompt template for the function
         * @return The builder
         */
        FromPromptBuilder<T> withPromptTemplate(
            @Nullable PromptTemplate promptTemplate);

        /**
         * Set the execution settings for the function.
         * @param executionSettings The execution settings for the function
         * @return The builder
         */
        FromPromptBuilder<T> withExecutionSettings(
            @Nullable
            Map<String, PromptExecutionSettings> executionSettings);

        /**
         * Set the default execution settings for the function.
         * 
         * @param executionSettings The default execution settings for the function
         * @return The builder
         */
        FromPromptBuilder<T> withDefaultExecutionSettings(
            @Nullable
            PromptExecutionSettings executionSettings);

        /**
         * Set the description of the function.
         * 
         * @param description The description of the function
         * @return The builder
         */
        FromPromptBuilder<T> withDescription(@Nullable String description);

        /**
         * Set the template for the function.
         * 
         * @param template The template for the function
         * @return The builder
         */
        FromPromptBuilder<T> withTemplate(@Nullable String template);

        /**
         * Create a new KernelFunction instance from the builder.
         * @return The new KernelFunction instance
         */
        KernelFunction<T> build();

        /**
         * Set the template format for the function.
         * @param templateFormat The template format for the function
         * @return The builder
         */
        FromPromptBuilder<T> withTemplateFormat(String templateFormat);

        /**
         * Set the output variable for the function.
         * @param outputVariable The output variable for the function
         * @return The builder
         */
        FromPromptBuilder<T> withOutputVariable(@Nullable OutputVariable outputVariable);

        /**
         * Set the output variable for the function.
         * @param description The description of the output variable
         * @param type The type of the output variable
         * @return The builder
         */
        FromPromptBuilder<T> withOutputVariable(@Nullable String description, String type);

        /**
         * Set the prompt template factory used to build the function.
         * @param promptTemplateFactory The prompt template factory for the function
         * @return The builder
         */
        FromPromptBuilder<T> withPromptTemplateFactory(
            @Nullable PromptTemplateFactory promptTemplateFactory);

        /**
         * Set the prompt template config used to build the function.
         * @param promptTemplateConfig The prompt template config for the function
         * @return The builder
         */
        FromPromptBuilder<T> withPromptTemplateConfig(
            @Nullable PromptTemplateConfig promptTemplateConfig);

    }
}
