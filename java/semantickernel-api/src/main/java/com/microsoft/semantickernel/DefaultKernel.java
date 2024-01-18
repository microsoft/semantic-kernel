package com.microsoft.semantickernel;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.annotation.Nullable;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter.NoopConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginCollection;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class DefaultKernel implements Kernel {

    private static final Logger LOGGER = LoggerFactory.getLogger(DefaultKernel.class);

    private final ServiceProvider serviceProvider;
    public KernelPluginCollection plugins;

    public DefaultKernel(
        ServiceProvider serviceProvider,
        @Nullable KernelPluginCollection plugins) {
        this.serviceProvider = serviceProvider;
        if (plugins != null) {
            this.plugins = plugins;
        } else {
            this.plugins = new KernelPluginCollection();
        }
    }

    @Override
    public <T> Mono<ContextVariable<T>> invokeAsync(
        KernelFunction function,
        @Nullable KernelArguments arguments,
        ContextVariableType<T> resultType) {
        return function.invokeAsync(this, arguments, resultType);
    }

    @Override
    public <T> Mono<ContextVariable<T>> invokeAsync(
        String pluginName,
        String functionName,
        @Nullable KernelArguments arguments,
        ContextVariableType<T> resultType) {
        return plugins.getFunction(pluginName, functionName)
            .invokeAsync(this, arguments, resultType);
    }

    @Override
    public <T> Mono<ContextVariable<T>> invokeAsync(
        KernelFunction function,
        @Nullable KernelArguments arguments,
        Class<T> resultType) {

        ContextVariableType<T> contextVariable;

        try {
            contextVariable = ContextVariableTypes.getDefaultVariableTypeForClass(resultType);
        } catch (Exception e) {
            if (resultType.isAssignableFrom(
                function.getMetadata().getReturnParameter().getParameterType())) {
                contextVariable = new ContextVariableType<>(new NoopConverter<>(resultType),
                    resultType);
            } else {
                throw e;
            }
        }
        return function.invokeAsync(this, arguments, contextVariable);
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
    public List<KernelFunction> getFunctions() {
        return null;
    }

    @Override
    public ServiceProvider getServiceSelector() {
        return serviceProvider;
    }

    @Override
    public KernelPluginCollection getPlugins() {
        return plugins;
    }

    public static class DefaultServiceProvider implements ServiceProvider {

        private final Map<Class<?>, AIService> services;

        public DefaultServiceProvider(Map<Class<?>, AIService> services) {
            this.services = services;
        }

        @Nullable
        @Override
        public <T> T getService(Class<T> clazz) {
            T service = (T) services.get(clazz);

            if (service == null) {
                service = (T) services
                    .entrySet()
                    .stream()
                    .filter(it -> clazz.isAssignableFrom(it.getKey()))
                    .map(it -> it.getValue())
                    .findFirst()
                    .orElseGet(() -> null);
            }

            if (service == null &&
                (clazz.equals(TextGenerationService.class) ||
                    clazz.equals(ChatCompletionService.class))) {
                LOGGER.warn(
                    "Requested a non-existent service type of {}. Consider requesting a TextAIService instead.",
                    clazz.getName());
            }

            return service;
        }

    }

    public static class Builder implements Kernel.Builder {

        private AIService defaultAIService;
        private final Map<Class<?>, AIService> services = new HashMap<>();
        private final List<KernelPlugin> plugins = new ArrayList<>();

        @Override
        public <T extends AIService> Builder withDefaultAIService(Class<T> clazz, T aiService) {
            this.defaultAIService = aiService;
            services.put(clazz, aiService);
            return this;
        }

        @Override
        public Builder withPromptTemplate(PromptTemplate promptTemplate) {
            return this;
        }

        @Override
        public Kernel.Builder withPlugin(KernelPlugin plugin) {
            plugins.add(plugin);
            return this;
        }

        @Override
        public Kernel build() {
            return new DefaultKernel(
                new DefaultServiceProvider(services),
                new KernelPluginCollection(plugins));
        }
    }
}
