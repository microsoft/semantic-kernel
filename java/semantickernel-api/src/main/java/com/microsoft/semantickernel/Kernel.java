// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginCollection;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.services.AIServiceSelector;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
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
        String pluginName,
        String functionName,
        @Nullable KernelArguments arguments,
        ContextVariableType<T> resultType);

    <T> Mono<ContextVariable<T>> invokeAsync(
        KernelFunction function,
        @Nullable KernelArguments arguments,
        Class<T> resultType);

    <T> Flux<T> invokeStreamingAsync(
        KernelFunction function,
        @Nullable KernelArguments arguments,
        ContextVariableType<T> resultType);

    <T> Flux<T> invokeStreamingAsync(
        KernelFunction function,
        @Nullable KernelArguments arguments,
        Class<T> resultType);

    List<KernelFunction> getFunctions();

    AIServiceSelector getServiceSelector();

    KernelPluginCollection getPlugins();

    static Builder builder() {
        return new DefaultKernel.Builder();
    }


    interface Builder extends SemanticKernelBuilder<Kernel> {

        <T extends AIService> Builder withAIService(Class<T> clazz, T aiService);

        Builder withPromptTemplate(PromptTemplate promptTemplate);

        Builder withPlugin(KernelPlugin searchPlugin);

        Builder withServiceSelector(
            Function<Map<Class<? extends AIService>, AIService>, AIServiceSelector> serviceSelector);
    }
}
