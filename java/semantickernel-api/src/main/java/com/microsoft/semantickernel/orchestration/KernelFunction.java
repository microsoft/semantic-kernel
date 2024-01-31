// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.semanticfunctions.InputVariable;
import com.microsoft.semantickernel.semanticfunctions.OutputVariable;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateFactory;
import java.util.List;
import java.util.Map;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

/**
 * Semantic Kernel callable function interface
 *
 * @apiNote Breaking change: s/SKFunction<RequestConfiguration>/SKFunction/
 */
public interface KernelFunction extends Buildable {


    /**
     * @return The name of the skill that this function is within
     */
    String getSkillName();

    /**
     * @return The name of this function
     */
    String getName();

    /**
     * @return A description of the function
     */

    @Nullable
    String getDescription();

    /**
     * Create a string for generating an embedding for a function.
     *
     * @return A string for generating an embedding for a function.
     */
    String toEmbeddingString();

    /**
     * Create a manual-friendly string for a function.
     *
     * @param includeOutputs Whether to include function outputs in the string.
     * @return A manual-friendly string for a function.
     */
    String toManualString(boolean includeOutputs);

    KernelFunctionMetadata getMetadata();

    @Deprecated
    default Class<?> getType() {
        throw new UnsupportedOperationException("Deprecated");
    }

    /**
     * Invokes the <see cref="KernelFunction"/>.
     *
     * @param kernel    The <see cref="Kernel"/> containing services, plugins, and other state for
     *                  use throughout the operation.
     * @param arguments The arguments to pass to the function's invocation, including any
     *                  {@link PromptExecutionSettings}.
     * @param <T>       The type of the context variable
     * @return The result of the function's execution.
     */
    <T> Mono<FunctionResult<T>> invokeAsync(
        Kernel kernel,
        @Nullable KernelArguments arguments,
        @Nullable ContextVariableType<T> variableType);

    <T> Mono<FunctionResult<T>> invokeAsync(
        Kernel kernel,
        @Nullable KernelArguments arguments,
        KernelHooks kernelHooks,
        @Nullable ContextVariableType<T> variableType);

    @Nullable
    Map<String, PromptExecutionSettings> getExecutionSettings();

    interface FromPromptBuilder {

        FromPromptBuilder withName(@Nullable String name);

        FromPromptBuilder withInputParameters(
            @Nullable List<InputVariable> inputVariables);

        FromPromptBuilder withPromptTemplate(
            @Nullable PromptTemplate promptTemplate);

        FromPromptBuilder withExecutionSettings(
            @Nullable
            Map<String, PromptExecutionSettings> executionSettings);

        FromPromptBuilder withDefaultExecutionSettings(
            @Nullable
            PromptExecutionSettings executionSettings);

        FromPromptBuilder withDescription(@Nullable String description);

        FromPromptBuilder withTemplate(@Nullable String template);

        KernelFunction build();

        FromPromptBuilder withTemplateFormat(String templateFormat);

        FromPromptBuilder withOutputVariable(@Nullable OutputVariable outputVariable);

        FromPromptBuilder withPromptTemplateFactory(
            @Nullable PromptTemplateFactory promptTemplateFactory);
    }
}
