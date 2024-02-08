// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.orchestration.FunctionInvocation;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginCollection;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.services.AIServiceSelection;
import com.microsoft.semantickernel.services.AIServiceSelector;
import com.microsoft.semantickernel.services.OrderedAIServiceSelector;

import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;

/**
 * Interface for the semantic kernel.
 */
public class Kernel implements Buildable {

    private final AIServiceSelector serviceSelector;
    private final KernelPluginCollection plugins;
    private final KernelHooks globalKernelHooks;

    public Kernel(
        AIServiceSelector serviceSelector,
        @Nullable KernelPluginCollection plugins,
        @Nullable KernelHooks globalKernelHooks) {
        this.serviceSelector = serviceSelector;

        if (plugins != null) {
            this.plugins = new KernelPluginCollection(plugins.getPlugins());
        } else {
            this.plugins = new KernelPluginCollection();
        }

        this.globalKernelHooks = new KernelHooks(globalKernelHooks);
    }

    public <T> FunctionInvocation<T> invokeAsync(
        String pluginName,
        String functionName) {
        KernelFunction function = plugins.getFunction(pluginName, functionName);
        return invokeAsync(function);
    }

    public <T> FunctionInvocation<T> invokeAsync(KernelFunction<T> function) {
        return function.invokeAsync(this);
    }


    public List<KernelFunction<?>> getFunctions() {
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

    /*
    // Add the global hooks to the invocation context hooks.
    private KernelHooks mergeInGlobalHooks(@Nullable KernelHooks invocationContextHooks) {

        KernelHooks mergedHooks = new KernelHooks();

        KernelHooks kernelHooks = this.globalKernelHooks;
        if (kernelHooks != null) {
            mergedHooks = mergedHooks.append(kernelHooks);
        }

        if (invocationContextHooks != null) {
            mergedHooks = mergedHooks.append(invocationContextHooks);
        }

        return mergedHooks;
    }

    // InvocationContext is immutable but it's members are not, so we need to create a new
    // that can be modified (possibly) without affecting the original.
    private InvocationContext updateInvocationContext(InvocationContext invocationContext) {
        KernelFunctionArguments arguments = invocationContext.getKernelFunctionArguments();
        if (arguments == null) {
            arguments = new KernelFunctionArguments();
        }

        // Make a copy of the arguments in case they are modified by a hook later on. 
        KernelFunctionArguments updatedArguments = new KernelFunctionArguments(arguments);
        updatedArguments.putAll(arguments);

        // Add the global hooks to the invocation context hooks.
        KernelHooks updatedHooks = mergeInGlobalHooks(invocationContext.getKernelHooks());

        return new InvocationContext(
            updatedArguments,
            invocationContext.getFunctionReturnType(),
            updatedHooks,
            invocationContext.getPromptExecutionSettings());
    }

    @Nullable
    @SuppressWarnings("unchecked")
    static <T> ContextVariableType<T> getContextVariableType(
        KernelFunction function,
        Class<? extends T> resultType) {

        Class<?> functionReturnType = function.getMetadata().getReturnParameter().getParameterType();

        try {
            // unchecked cast   
            return (ContextVariableType<T>) ContextVariableTypes.getDefaultVariableTypeForClass(
                functionReturnType);
        } catch (Exception e) {
            if (functionReturnType.isAssignableFrom(resultType)) {
                return new ContextVariableType<>(
                        // unchecked cast
                        new NoopConverter<>((Class<T>) functionReturnType),
                        // unchecked cast
                        (Class<T>) functionReturnType);
            } else {
                return null;
            }
        }
    }    
 */

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
