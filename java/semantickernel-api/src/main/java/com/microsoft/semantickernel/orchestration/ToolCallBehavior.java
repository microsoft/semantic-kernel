// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.semanticfunctions.KernelFunction;

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import javax.annotation.Nullable;

/**
 * Defines the behavior of a tool call. Currently, the only tool available is function calling.
 */
public class ToolCallBehavior {

    /**
     * Enable all kernel functions. All Kernel functions will be passed to the model.
     *
     * @param autoInvoke Enable or disable auto-invocation.
     *                   If auto-invocation is enabled, the model may request that the Semantic Kernel
     *                   invoke the kernel functions and return the value to the model.
     * @return A new ToolCallBehavior instance with all kernel functions enabled.
     */
    public static ToolCallBehavior enableAllKernelFunctions(boolean autoInvoke) {
        return new EnabledKernelFunctions(true, autoInvoke, null);
    }

    /**
     * Require a function. The required function will be the only function passed to the model
     * and forces the model to call the function. Only one function can be required.
     *
     * @param function The function to require.
     * @return A new ToolCallBehavior instance with the required function.
     */
    public static ToolCallBehavior requireKernelFunction(KernelFunction<?> function) {
        return new RequiredKernelFunction(function);
    }

    /**
     * Enable a set of kernel functions.
     * If a function is enabled, it may be called. If it is not enabled, it will not be called.
     * By default, all functions are disabled.
     *
     * @param functions The functions to enable.
     * @return A new ToolCallBehavior instance with the enabled functions.
     */
    public static ToolCallBehavior enableKernelFunctions(boolean autoInvoke,
                                                   List<KernelFunction<?>> functions) {
        return new EnabledKernelFunctions(false, autoInvoke, functions);
    }

    /**
     * Enable a set of kernel functions.
     * If a function is enabled, it may be called. If it is not enabled, it will not be called.
     * By default, all functions are disabled.
     *
     * @param functions The functions to enable.
     * @return A new ToolCallBehavior instance with the enabled functions.
     */
    public static ToolCallBehavior enableKernelFunctions(boolean autoInvoke,
                                                   KernelFunction<?>... functions) {
        return enableKernelFunctions(autoInvoke, Arrays.asList(functions));
    }

    private static final int DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS = 5;
    private static final String FUNCTION_NAME_SEPARATOR = "-";

    private int maximumAutoInvokeAttempts;

    /**
     * Create a new instance of ToolCallBehavior with defaults.
     */
    private ToolCallBehavior(boolean autoInvoke) {
        setMaximumAutoInvokeAttempts(autoInvoke ? DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS : 0);
    }

    /**
     * Set maximum auto-invoke attempts
     * @param maximumAutoInvokeAttempts Maximum auto-invoke attempts
     */
    protected void setMaximumAutoInvokeAttempts(int maximumAutoInvokeAttempts) {
        this.maximumAutoInvokeAttempts = maximumAutoInvokeAttempts;
    }

    /**
     * Check whether auto-invocation is enabled.
     *
     * @return Whether auto-invocation is enabled.
     */
    public boolean autoInvokeEnabled() {
        return maximumAutoInvokeAttempts > 0;
    }

    /**
     * Get the maximum number of times that auto-invocation will be attempted.
     *
     * @return The maximum number of attempts.
     */
    public int getMaximumAutoInvokeAttempts() {
        return this.maximumAutoInvokeAttempts;
    }

    /**
     * Get the key for a function.
     *
     * @param pluginName   The name of the plugin that the function is in.
     * @param functionName The name of the function.
     * @return The key for the function.
     */
    protected String getKey(@Nullable String pluginName, String functionName) {
        if (pluginName == null) {
            pluginName = "";
        }
        return String.format("%s%s%s", pluginName, FUNCTION_NAME_SEPARATOR, functionName);
    }

    /**
     * A required kernel function.
     * The required function will be the only function passed to the model and forces the model to call the function.
     * Only one function can be required.
     */
    public static class RequiredKernelFunction extends ToolCallBehavior {
        private final KernelFunction<?> requiredFunction;

        /**
         * Create a new instance of RequiredKernelFunction.
         *
         * @param requiredFunction The function that is required.
         */
        public RequiredKernelFunction(KernelFunction<?> requiredFunction) {
            super(true);
            this.requiredFunction = requiredFunction;
            this.setMaximumAutoInvokeAttempts(1);
        }

        public KernelFunction<?> getRequiredFunction() {
            return requiredFunction;
        }
    }

    /**
     * A set of enabled kernel functions. All kernel functions are enabled if allKernelFunctionsEnabled is true.
     * Otherwise, only the functions in enabledFunctions are enabled.
     * <p>
     * If a function is enabled, it may be called. If it is not enabled, it will not be called.
     */
    public static class EnabledKernelFunctions extends ToolCallBehavior {
        private final Set<String> enabledFunctions;
        private final boolean allKernelFunctionsEnabled;

        /**
         * Create a new instance of EnabledKernelFunctions.
         *
         * @param allKernelFunctionsEnabled Whether all kernel functions are enabled.
         * @param autoInvoke                Whether auto-invocation is enabled.
         * @param enabledFunctions          A set of functions that are enabled.
         */
        public EnabledKernelFunctions(boolean allKernelFunctionsEnabled, boolean autoInvoke, @Nullable List<KernelFunction<?>> enabledFunctions) {
            super(autoInvoke);
            this.allKernelFunctionsEnabled = allKernelFunctionsEnabled;
            this.enabledFunctions = new HashSet<>();
            if (enabledFunctions != null) {
                enabledFunctions.stream().filter(Objects::nonNull).forEach(f -> this.enabledFunctions.add(getKey(f.getPluginName(), f.getName())));
            }
        }

        /**
         * Check whether the given function is enabled.
         *
         * @param function The function to check.
         * @return Whether the function is enabled.
         */
        public boolean functionEnabled(KernelFunction<?> function) {
            return functionEnabled(function.getPluginName(), function.getName());
        }

        /**
         * Check whether the given function is enabled.
         *
         * @param pluginName   The name of the skill that the function is in.
         * @param functionName The name of the function.
         * @return Whether the function is enabled.
         */
        public boolean functionEnabled(@Nullable String pluginName, String functionName) {
            String key = getKey(pluginName, functionName);
            return enabledFunctions.contains(key);
        }

        /**
         * Check whether all kernel functions are enabled.
         *
         * @return Whether all kernel functions are enabled.
         */
        public boolean isAllKernelFunctionsEnabled() {
            return allKernelFunctionsEnabled;
        }
    }
}
