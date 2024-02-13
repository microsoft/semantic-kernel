// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.orchestration.FunctionInvocation;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.services.AIServiceSelection;
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

import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;

/**
 * Interface for the semantic kernel.
 */
public class Kernel implements Buildable {

    private static final Logger LOGGER = LoggerFactory.getLogger(Kernel.class);

    private final AIServiceSelector serviceSelector;
    private final KernelPluginCollection plugins;
    private final KernelHooks globalKernelHooks;

    public Kernel(
        AIServiceSelector serviceSelector,
        @Nullable List<KernelPlugin> plugins,
        @Nullable KernelHooks globalKernelHooks) {
        this.serviceSelector = serviceSelector;
        if (plugins != null) {
            this.plugins = new KernelPluginCollection(plugins);
        } else {
            this.plugins = new KernelPluginCollection();
        }

        this.globalKernelHooks = new KernelHooks(globalKernelHooks);
    }

    @SuppressWarnings({"rawtypes", "unchecked"})
    public <T> FunctionInvocation<T> invokeAsync(
        String pluginName,
        String functionName) {
        KernelFunction function = getFunction(pluginName, functionName);
        return invokeAsync(function);
    }

    public <T> FunctionInvocation<T> invokeAsync(KernelFunction<T> function) {
        return function.invokeAsync(this);
    }

    public void addPlugin(KernelPlugin plugin) {
        plugins.add(plugin);
    }

    @Nullable
    public KernelPlugin getPlugin(String pluginName) {
        return plugins.getPlugin(pluginName);
    }

    public List<KernelPlugin> getPlugins() {
        return plugins.getPlugins();
    }

    @SuppressWarnings("unchecked")
    public <T> KernelFunction<T> getFunction(String pluginName, String functionName) {
        return (KernelFunction<T>)plugins.getFunction(pluginName, functionName);
    }

    public List<KernelFunction<?>> getFunctions() {
        return plugins.getFunctions();
    }

    public AIServiceSelector getServiceSelector() {
        return serviceSelector;
    }


    @SuppressFBWarnings("EI_EXPOSE_REP")
    public KernelHooks getGlobalKernelHooks() {
        return globalKernelHooks;
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
                plugins,
                null);
        }
    }

}
