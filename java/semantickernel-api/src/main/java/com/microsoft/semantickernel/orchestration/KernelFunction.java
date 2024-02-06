// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.Todo;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.semanticfunctions.InputVariable;
import com.microsoft.semantickernel.semanticfunctions.OutputVariable;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateFactory;

import reactor.core.publisher.Mono;

/**
 * Semantic Kernel callable function interface
 * @param <T> The type of the result of the function
 */
// TODO: add example of using ContextVariableType to class documentation
public abstract class KernelFunction<T> implements Buildable {

        /// <summary>
    /// Gets the metadata describing the function.
    /// </summary>
    /// <returns>An instance of <see cref="KernelFunctionMetadata"/> describing the function</returns>
    private final KernelFunctionMetadata metadata;

    /// <summary>
    /// Gets the prompt execution settings.
    /// </summary>
    @Nullable
    private final Map<String, PromptExecutionSettings> executionSettings;

    protected KernelFunction(
        KernelFunctionMetadata metadata,
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

    public KernelFunctionMetadata getMetadata() {
        return metadata;
    }


    /**
     * Invokes this KernelFunction. This is the most typical use case.
     *
     * @param kernel    The Kernel containing services, plugins, and other state for
     *                  use throughout the operation.
     * @param arguments The arguments to pass to the function's invocation
     * @return The result of the function's execution.
     * @see FunctionResult#getResultVariable()
     */
    public Mono<FunctionResult<T>> invokeAsync(
        Kernel kernel,
        @Nullable KernelFunctionArguments arguments) {
        return invokeAsync(kernel, arguments, null);
    }
    
    /**
     * Invokes this KernelFunction. If the {@code variableType} parameter is provided, 
     * the {@link ContextVarialbeType} is used to convert the result of the function to the
     * the appropriate {@link FunctionResultType}. The {@code variableType} is
     * not required for converting well-known types such as {@link String} and {@link Integer}
     * which have pre-defined {@code ContextVariableType}s. 
     *
     * @param kernel    The Kernel containing services, plugins, and other state for
     *                  use throughout the operation.
     * @param arguments The arguments to pass to the function's invocation
     * @param variableType The type of the {@link ContextVariable} returned in the {@link FunctionResult}
     * @return The result of the function's execution.
     * @see FunctionResult#getResultVariable()
     * @see ContextVariableTypes#getDefaultVariableTypeForClass(Class)
     */
    public Mono<FunctionResult<T>> invokeAsync(
        Kernel kernel,
        @Nullable KernelFunctionArguments arguments,
        @Nullable ContextVariableType<T> variableType) {
        return invokeAsync(kernel, arguments, variableType, null);
    }

    /**
     * Invokes this KernelFunction. 
     * <p>
     * If the {@code variableType} parameter is provided, 
     * the {@link ContextVarialbeType} is used to convert the result of the function to the
     * the appropriate {@link FunctionResultType}. The {@code variableType} is
     * not required for converting well-known types such as {@link String} and {@link Integer}
     * which have pre-defined {@code ContextVariableType}s. 
     * <p> 
     * The {@link InvocationContext} allows for customization of the 
     * behavior of function, including the ability to pass in {@link KernelHooks}
     * {@link PromptExecutionSettings}, and {@link ToolCallBehavior}.
     * <p> 
     * The difference between calling the {@code KernelFunction.invokeAsync} method
     * directly and calling the {@code Kernel.invokeAsync} method is that the latter
     * adds the {@link KernelHooks#getGlobalHooks() global KernelHooks} (if any)
     * to the {@link InvocationContext}. Calling {@code KernelFunction.invokeAsync} 
     * directly does not add the global hooks.
     *
     * @param kernel    The Kernel containing services, plugins, and other state for
     *                  use throughout the operation.
     * @param arguments The arguments to pass to the function's invocation
     * @param variableType The type of the {@link ContextVariable} returned in the {@link FunctionResult}
     * @param invocationContext The arguments to pass to the function's invocation
     * @return The result of the function's execution.
     * @see FunctionResult#getResultVariable()
     */        
    public abstract Mono<FunctionResult<T>> invokeAsync(
        Kernel kernel,
        @Nullable KernelFunctionArguments arguments,
        @Nullable ContextVariableType<T> variableType,
        @Nullable InvocationContext invocationContext);

    public static interface FromPromptBuilder<T> {

        FromPromptBuilder<T> withName(@Nullable String name);

        FromPromptBuilder<T> withInputParameters(
            @Nullable List<InputVariable> inputVariables);

        FromPromptBuilder<T> withPromptTemplate(
            @Nullable PromptTemplate promptTemplate);

        FromPromptBuilder<T> withExecutionSettings(
            @Nullable
            Map<String, PromptExecutionSettings> executionSettings);

        FromPromptBuilder<T> withDefaultExecutionSettings(
            @Nullable
            PromptExecutionSettings executionSettings);

        FromPromptBuilder<T> withDescription(@Nullable String description);

        FromPromptBuilder<T> withTemplate(@Nullable String template);

        KernelFunction<T> build();

        FromPromptBuilder<T> withTemplateFormat(String templateFormat);

        FromPromptBuilder<T> withOutputVariable(@Nullable OutputVariable outputVariable);

        FromPromptBuilder<T> withOutputVariable(@Nullable String description, String type);


        FromPromptBuilder<T> withPromptTemplateFactory(
            @Nullable PromptTemplateFactory promptTemplateFactory);
    }
}
