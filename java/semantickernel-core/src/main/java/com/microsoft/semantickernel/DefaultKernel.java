package com.microsoft.semantickernel;

import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.StreamingContent;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import javax.annotation.Nullable;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class DefaultKernel implements Kernel {

    @Override
    public <T> Mono<ContextVariable<T>> invokeAsync(KernelFunction function,
        @Nullable KernelArguments arguments, ContextVariableType<T> resultType) {
        return function.invokeAsync(this, arguments, resultType);
    }

    @Override
    public <T> Mono<ContextVariable<T>> invokeAsync(KernelFunction function,
        @Nullable KernelArguments arguments, Class<T> resultType) {
        return function.invokeAsync(this, arguments,
            ContextVariableTypes.getDefaultVariableTypeForClass(resultType));
    }

    @Override
    public <T> Flux<StreamingContent<T>> invokeStreamingAsync(KernelFunction function,
        @Nullable KernelArguments arguments, ContextVariableType<T> resultType) {
        return function.invokeStreamingAsync(this, arguments, resultType);
    }

    @Override
    public <T> Flux<StreamingContent<T>> invokeStreamingAsync(KernelFunction function,
        @Nullable KernelArguments arguments, Class<T> resultType) {
        return function.invokeStreamingAsync(this, arguments,
            ContextVariableTypes.getDefaultVariableTypeForClass(resultType));
    }

    public static class Builder implements Kernel.Builder {

        @Override
        public Builder withDefaultAIService(ChatCompletionService gpt35Turbo) {
            return this;
        }

        @Override
        public Builder withPromptTemplateEngine(PromptTemplate promptTemplate) {
            return this;
        }

        @Override
        public Kernel build() {
            return new DefaultKernel();
        }
    }
}
