package com.microsoft.semantickernel;

import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.annotation.Nullable;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class DefaultKernel implements Kernel {

    private final ServiceProvider serviceProvider;

    public DefaultKernel(ServiceProvider serviceProvider) {
        this.serviceProvider = serviceProvider;
    }

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
    public <T> Flux<T> invokeStreamingAsync(KernelFunction function,
        @Nullable KernelArguments arguments, ContextVariableType<T> resultType) {
        return function.invokeStreamingAsync(this, arguments, resultType)
            .map(x -> x.innerContent);
    }

    @Override
    public <T> Flux<T> invokeStreamingAsync(KernelFunction function,
        @Nullable KernelArguments arguments, Class<T> resultType) {
        return function.invokeStreamingAsync(this, arguments,
                ContextVariableTypes.getDefaultVariableTypeForClass(resultType))
            .map(x -> x.innerContent);
    }

    @Override
    public ServiceProvider getServiceSelector() {
        return serviceProvider;
    }

    static class DefaultServiceProvider implements ServiceProvider {

        private final Map<Class, AIService> services;

        public DefaultServiceProvider(Map<Class, AIService> services) {
            this.services = services;
        }

        @Nullable
        @Override
        public <T> T getService(Class<T> clazz) {
            T service = (T) services.get(clazz);

            if (service == null && clazz.equals(TextGenerationService.class)) {
                service = (T) services.get(ChatCompletionService.class);
            }

            return service;
        }
    }

    public static class Builder implements Kernel.Builder {

        private AIService defaultAIService;
        private final Map<Class, AIService> services = new HashMap<>();
        private final List<KernelPlugin> plugins = new ArrayList<>();

        @Override
        public <T extends AIService> Builder withDefaultAIService(Class<T> clazz, T aiService) {
            this.defaultAIService = aiService;
            services.put(clazz, aiService);
            return this;
        }

        @Override
        public Builder withPromptTemplateEngine(PromptTemplate promptTemplate) {
            return this;
        }

        @Override
        public Kernel.Builder withPlugins(KernelPlugin plugin) {
            plugins.add(plugin);
            return this;
        }

        @Override
        public Kernel build() {
            return new DefaultKernel(new DefaultServiceProvider(services));
        }
    }
}
