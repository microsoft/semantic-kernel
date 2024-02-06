// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;
import java.util.stream.Collectors;

import javax.annotation.Nullable;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginCollection;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.services.AIServiceSelection;
import com.microsoft.semantickernel.services.AIServiceSelector;
import com.microsoft.semantickernel.services.OrderedAIServiceSelector;

import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;
import reactor.core.publisher.Mono;

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

    public <T> Mono<FunctionResult<T>> invokeAsync(
        KernelFunction<T> function,
        @Nullable KernelFunctionArguments arguments) {
        return invokeAsync(function, arguments, null);
    }

    public <T> Mono<FunctionResult<T>> invokeAsync(
        KernelFunction<T> function,
        @Nullable KernelFunctionArguments arguments,
        @Nullable ContextVariableType<T> variableType) {
        return invokeAsync(function, arguments, variableType, null);
    }

    public <T> Mono<FunctionResult<T>> invokeAsync(
        KernelFunction<T> function,
        @Nullable KernelFunctionArguments arguments,
        @Nullable ContextVariableType<T> variableType,
        @Nullable InvocationContext invocationContext) {
       
        Objects.requireNonNull(function, "function");

        // Ever other invokeAsync call should end up here... 

        // If there are hooks added to the global kernel hooks, create a new invocation context
        // with the global hooks and the invocation context hooks merged together.
        KernelHooks hooks = new KernelHooks(getGlobalKernelHooks());
        if (!hooks.isEmpty()) {
            if (invocationContext != null) {
                hooks.append(invocationContext.getKernelHooks());
            }

            InvocationContext.Builder builder = InvocationContext.builder()
                .withKernelHooks(hooks);
            
            if (invocationContext != null) {
                builder = builder
                    .withPromptExecutionSettings(invocationContext.getPromptExecutionSettings())
                    .withToolCallBehavior(invocationContext.getToolCallBehavior());
            } 
                
            invocationContext = builder.build();
        }

        return function.invokeAsync(this, arguments, variableType, invocationContext);
    }

    public <T> Mono<FunctionResult<T>> invokeAsync(
        String pluginName,
        String functionName,
        @Nullable KernelFunctionArguments arguments) {
        return invokeAsync(pluginName, functionName, arguments, null);
    }

    public <T> Mono<FunctionResult<T>> invokeAsync(
        String pluginName,
        String functionName,
        @Nullable KernelFunctionArguments arguments,
        @Nullable ContextVariableType<T> resultType) {
            return invokeAsync(pluginName, functionName, arguments, resultType, null);
        }

    public <T> Mono<FunctionResult<T>> invokeAsync(
        String pluginName,
        String functionName,
        @Nullable KernelFunctionArguments arguments,
        @Nullable ContextVariableType<T> variableType,
        @Nullable InvocationContext invocationContext) {
        KernelFunction function = plugins.getFunction(pluginName, functionName);
        return invokeAsync(function, arguments, variableType, invocationContext);
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
