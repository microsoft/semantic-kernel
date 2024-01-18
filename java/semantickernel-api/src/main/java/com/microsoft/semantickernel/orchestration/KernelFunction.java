// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import java.util.List;
import java.util.Map;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.semanticfunctions.InputVariable;
import com.microsoft.semantickernel.semanticfunctions.OutputVariable;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateFactory;

import reactor.core.publisher.Flux;
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
     * The function to create a fully qualified name for
     *
     * @return A fully qualified name for a function
     */
    String toFullyQualifiedName();

    /**
     * @return A description of the function
     */
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
     * Invokes the <see cref="KernelFunction"/> and streams its results.
     *
     * @param kernel    The <see cref="Kernel"/> containing services, plugins, and other state for
     *                  use throughout the operation.
     * @param arguments The arguments to pass to the function's invocation, including any
     *                  {@link PromptExecutionSettings}.
     * @param <T>       The type of the context variable
     * @return An {@link Flux} for streaming the results of the function's invocation.
     */
    <T> Flux<StreamingContent<T>> invokeStreamingAsync(
        Kernel kernel,
        @Nullable KernelArguments arguments,
        ContextVariableType<T> variableType);

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
    <T> Mono<ContextVariable<T>> invokeAsync(
        Kernel kernel,
        @Nullable KernelArguments arguments,
        ContextVariableType<T> variableType);

    @Nullable
    Map<String, PromptExecutionSettings> getExecutionSettings();

    interface FromPromptBuilder {

        FromPromptBuilder withName(String name);

        FromPromptBuilder withInputParameters(List<InputVariable> inputVariables);

        FromPromptBuilder withPromptTemplate(PromptTemplate promptTemplate);

        FromPromptBuilder withPluginName(String name);

        FromPromptBuilder withExecutionSettings(
            Map<String, PromptExecutionSettings> executionSettings);

        FromPromptBuilder withDefaultExecutionSettings(
            PromptExecutionSettings executionSettings);

        FromPromptBuilder withDescription(String description);

        FromPromptBuilder withTemplate(String template);

        KernelFunction build();

        FromPromptBuilder withTemplateFormat(String templateFormat);

        FromPromptBuilder withOutputVariable(OutputVariable outputVariable);

        FromPromptBuilder withPromptTemplateFactory(PromptTemplateFactory promptTemplateFactory);
    }
}
