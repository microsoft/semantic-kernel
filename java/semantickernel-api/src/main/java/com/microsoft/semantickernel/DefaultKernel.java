package com.microsoft.semantickernel;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter.NoopConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginCollection;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.services.AIServiceSelector;
import com.microsoft.semantickernel.services.OrderedAIServiceSelector;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class DefaultKernel implements Kernel {

    private static final Logger LOGGER = LoggerFactory.getLogger(DefaultKernel.class);

    private final AIServiceSelector serviceSelector;
    public KernelPluginCollection plugins;

    public DefaultKernel(
        AIServiceSelector serviceSelector,
        @Nullable KernelPluginCollection plugins) {
        this.serviceSelector = serviceSelector;
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
    public AIServiceSelector getServiceSelector() {
        return serviceSelector;
    }

    @Override
    public KernelPluginCollection getPlugins() {
        return plugins;
    }


    public static class Builder implements Kernel.Builder {

        private final Map<Class<? extends AIService>, AIService> services = new HashMap<>();
        private final List<KernelPlugin> plugins = new ArrayList<>();
        private Function<Map<Class<? extends AIService>, AIService>, AIServiceSelector> serviceSelectorProvider;

        @Override
        public <T extends AIService> Builder withAIService(Class<T> clazz, T aiService) {
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
        public Kernel.Builder withServiceSelector(
            Function<Map<Class<? extends AIService>, AIService>, AIServiceSelector> serviceSelector) {
            this.serviceSelectorProvider = serviceSelector;
            return this;
        }

        @Override
        public Kernel build() {

            AIServiceSelector serviceSelector;
            if (serviceSelectorProvider == null) {
                serviceSelector = new OrderedAIServiceSelector(services);
            } else {
                serviceSelector = serviceSelectorProvider.apply(services);
            }

            return new DefaultKernel(
                serviceSelector,
                new KernelPluginCollection(plugins));
        }
    }
}
