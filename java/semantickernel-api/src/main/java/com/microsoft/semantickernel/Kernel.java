// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.StreamingContent;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import javax.annotation.Nullable;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * Interface for the semantic kernel.
 */
public interface Kernel extends Buildable {

    /**
     * Invokes the {@link KernelFunction}.
     *
     * @param <T>       the type of the result value of the function.
     * @param function  the {@link KernelFunction} to invoke.
     * @param arguments the arguments to pass to the function's invocation, including any
     *                  {@link com.microsoft.semantickernel.orchestration.PromptExecutionSettings}.
     * @return the result of the function's execution, cast to {@link T}.
     */
    <T> Mono<ContextVariable<T>> invokeAsync(
        KernelFunction function,
        @Nullable KernelArguments arguments,
        ContextVariableType<T> resultType);

    <T> Mono<ContextVariable<T>> invokeAsync(
        KernelFunction function,
        @Nullable KernelArguments arguments,
        Class<T> resultType);

    <T> Flux<StreamingContent<T>> invokeStreamingAsync(
        KernelFunction function,
        @Nullable KernelArguments arguments,
        ContextVariableType<T> resultType);

    <T> Flux<StreamingContent<T>> invokeStreamingAsync(
        KernelFunction function,
        @Nullable KernelArguments arguments,
        Class<T> resultType);

    interface Builder extends SemanticKernelBuilder<Kernel> {

        Builder withDefaultAIService(
            ChatCompletionService gpt35Turbo);

        Builder withPromptTemplateEngine(PromptTemplate promptTemplate);

    }
}
