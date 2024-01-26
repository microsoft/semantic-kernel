// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter.NoopConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginCollection;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.services.AIServiceSelection;
import com.microsoft.semantickernel.services.AIServiceSelector;
import com.microsoft.semantickernel.services.OrderedAIServiceSelector;
import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Mono;

/**
 * Interface for the semantic kernel.
 */
public class Kernel implements Buildable {

    private static final Logger LOGGER = LoggerFactory.getLogger(Kernel.class);

    private final AIServiceSelector serviceSelector;
    private final KernelPluginCollection plugins;
    private final KernelHooks kernelHooks;

    public Kernel(
        AIServiceSelector serviceSelector,
        @Nullable KernelPluginCollection plugins,
        @Nullable KernelHooks kernelHooks) {
        this.serviceSelector = serviceSelector;

        if (plugins != null) {
            this.plugins = new KernelPluginCollection(plugins.getPlugins());
        } else {
            this.plugins = new KernelPluginCollection();
        }

        this.kernelHooks = new KernelHooks(kernelHooks);
    }

    public <T> Mono<FunctionResult<T>> invokeAsync(
        KernelFunction function,
        @Nullable KernelArguments arguments,
        @Nullable KernelHooks kernelHooks,
        ContextVariableType<T> resultType) {
        kernelHooks = mergeInGlobalHooks(kernelHooks);
        return function.invokeAsync(this, arguments, kernelHooks, resultType);
    }

    public <T> Mono<FunctionResult<T>> invokeAsync(
        KernelFunction function,
        @Nullable KernelArguments arguments,
        ContextVariableType<T> resultType) {
        return invokeAsync(function, arguments, null, resultType);
    }


    public <T> Mono<FunctionResult<T>> invokeAsync(
        String pluginName,
        String functionName,
        @Nullable KernelArguments arguments,
        @Nullable KernelHooks kernelHooks,
        ContextVariableType<T> resultType) {
        kernelHooks = mergeInGlobalHooks(kernelHooks);
        return plugins.getFunction(pluginName, functionName)
            .invokeAsync(this, arguments, kernelHooks, resultType);
    }

    public <T> Mono<FunctionResult<T>> invokeAsync(
        String pluginName,
        String functionName,
        @Nullable KernelArguments arguments,
        ContextVariableType<T> resultType) {
        return invokeAsync(pluginName, functionName, arguments, null, resultType);
    }

    public <T> Mono<FunctionResult<T>> invokeAsync(
        KernelFunction function,
        @Nullable KernelArguments arguments,
        @Nullable KernelHooks kernelHooks,
        Class<T> resultType) {

        kernelHooks = mergeInGlobalHooks(kernelHooks);

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
        return function.invokeAsync(this, arguments, kernelHooks, contextVariable);
    }

    public <T> Mono<FunctionResult<T>> invokeAsync(
        KernelFunction function,
        @Nullable KernelArguments arguments,
        Class<T> resultType) {
        return invokeAsync(function, arguments, null, resultType);
    }

    private KernelHooks mergeInGlobalHooks(@Nullable KernelHooks kernelHooks) {
        KernelHooks allKernelHooks = this.kernelHooks;
        if (kernelHooks != null) {
            allKernelHooks = allKernelHooks.append(kernelHooks);
        }
        return allKernelHooks;
    }

    public List<KernelFunction> getFunctions() {
        return plugins.getPlugins()
            .stream()
            .map(KernelPlugin::getFunctions)
            .flatMap(m -> m.values().stream())
            .collect(Collectors.toList());
    }

    public AIServiceSelector getServiceSelector() {
        return serviceSelector;
    }

    @SuppressFBWarnings("EI_EXPOSE_REP")
    public KernelPluginCollection getPlugins() {
        return plugins;
    }


    @SuppressFBWarnings("EI_EXPOSE_REP")
    public KernelHooks getHookService() {
        return kernelHooks;
    }

    public <T extends AIService> T getService(Class<T> clazz) throws ServiceNotFoundException {
        AIServiceSelection<T> selector = serviceSelector
            .trySelectAIService(
                clazz,
                null,
                null
            );

        if (selector == null) {
            throw new ServiceNotFoundException("Unable to find service of type " + clazz.getName());
        }

        return selector.getService();
    }

    public static Kernel.Builder builder() {
        return new Kernel.Builder();
    }


    public static class Builder implements SemanticKernelBuilder<Kernel> {

        private final Map<Class<? extends AIService>, AIService> services = new HashMap<>();
        private final List<KernelPlugin> plugins = new ArrayList<>();
        @Nullable
        private Function<Map<Class<? extends AIService>, AIService>, AIServiceSelector> serviceSelectorProvider;

        public <T extends AIService> Builder withAIService(Class<T> clazz, T aiService) {
            services.put(clazz, aiService);
            return this;
        }

        public Builder withPromptTemplate(PromptTemplate promptTemplate) {
            return this;
        }

        public Kernel.Builder withPlugin(KernelPlugin plugin) {
            plugins.add(plugin);
            return this;
        }

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

            return new Kernel(
                serviceSelector,
                new KernelPluginCollection(plugins),
                null);
        }
    }

}
