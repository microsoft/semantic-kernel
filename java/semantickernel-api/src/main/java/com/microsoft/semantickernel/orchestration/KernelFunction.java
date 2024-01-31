// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
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

    /**
     * Invokes this KernelFunction.
     *
     * @param kernel    The Kernel containing services, plugins, and other state for
     *                  use throughout the operation.
     * @param arguments The arguments to pass to the function's invocation
     * @param variableType The type of the {@link ContextVariable} returned in the {@link FunctionResult}
     * @param <T>       The type of the context variable
     * @return The result of the function's execution.
     * @see FunctionResult#getResultVariable()
     */
    <T> Mono<FunctionResult<T>> invokeAsync(
        Kernel kernel,
        @Nullable KernelFunctionArguments arguments,
        ContextVariableType<T> variableType);

    /**
     * Invokes this KernelFunction. The {@link InvocationContext} encapsulates the function arguments 
     * and return type of the function. It also allows for customization of the behavior of
     * the invocation of the function, including the ability to pass in {@link KernelHooks} and
     * {@link PromptExecutionSettings}.
     *
     * @param kernel    The Kernel containing services, plugins, and other state for
     *                  use throughout the operation.
     * @param invocationContext The arguments to pass to the function's invocation
     * @param <T>       The type of the context variable
     * @return The result of the function's execution.
     * @see FunctionResult#getResultVariable()
     */        
    <T> Mono<FunctionResult<T>> invokeAsync(
        Kernel kernel,
        InvocationContext invocationContext);

    @Nullable
    Map<String, PromptExecutionSettings> getExecutionSettings();

    interface FromPromptBuilder {

        FromPromptBuilder withName(String name);

        FromPromptBuilder withInputParameters(List<InputVariable> inputVariables);

        FromPromptBuilder withPromptTemplate(PromptTemplate promptTemplate);

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
