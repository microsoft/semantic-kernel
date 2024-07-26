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
     * Allow all kernel functions. All Kernel functions will be passed to the model.
     *
     * @param autoInvoke Enable or disable auto-invocation.
     *                   If auto-invocation is enabled, the model may request that the Semantic Kernel
     *                   invoke the kernel functions and return the value to the model.
     * @return A new ToolCallBehavior instance with all kernel functions allowed.
     */
    public static ToolCallBehavior allowAllKernelFunctions(boolean autoInvoke) {
        return new AllowedKernelFunctions(true, autoInvoke, null);
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
     * Allow a set of kernel functions.
     * If a function is allowed, it may be called. If it is not allowed, it will not be called.
     * By default, all functions are not allowed.
     *
     * @param autoInvoke Enable or disable auto-invocation.
     *                   If auto-invocation is enabled, the model may request that the Semantic Kernel
     *                   invoke the kernel functions and return the value to the model.
     * @param functions The functions to allow.
     * @return A new ToolCallBehavior instance with the allowed functions.
     */
    public static ToolCallBehavior allowOnlyKernelFunctions(boolean autoInvoke,
        List<KernelFunction<?>> functions) {
        return new AllowedKernelFunctions(false, autoInvoke, functions);
    }

    /**
     * Allow a set of kernel functions.
     * If a function is allowed, it may be called. If it is not allowed, it will not be called.
     * By default, all functions are not allowed.
     *
     * @param autoInvoke Enable or disable auto-invocation.
     *                   If auto-invocation is enabled, the model may request that the Semantic Kernel
     *                   invoke the kernel functions and return the value to the model.
     * @param functions The functions to allow.
     * @return A new ToolCallBehavior instance with the allowed functions.
     */
    public static ToolCallBehavior allowOnlyKernelFunctions(boolean autoInvoke,
        KernelFunction<?>... functions) {
        return allowOnlyKernelFunctions(autoInvoke, Arrays.asList(functions));
    }

    private static final int DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS = 5;
    private static final String FUNCTION_NAME_SEPARATOR = "-";
    private final int maximumAutoInvokeAttempts;

    /**
     * Create a new instance of ToolCallBehavior
     */
    private ToolCallBehavior(int maximumAutoInvokeAttempts) {
        this.maximumAutoInvokeAttempts = maximumAutoInvokeAttempts;
    }

    /**
     * Check whether auto-invocation is enabled.
     *
     * @return Whether auto-invocation is enabled.
     */
    public boolean isAutoInvokeAllowed() {
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
     * Form the full function name.
     *
     * @param pluginName   The name of the plugin that the function is in.
     * @param functionName The name of the function.
     * @return The key for the function.
     */
    public static String formFullFunctionName(@Nullable String pluginName, String functionName) {
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
            super(1);
            this.requiredFunction = requiredFunction;
        }

        /**
         * Get the required function. 
         * @return the required function.
         */
        public KernelFunction<?> getRequiredFunction() {
            return requiredFunction;
        }
    }

    /**
     * A set of allowed kernel functions. All kernel functions are allowed if allKernelFunctionsAllowed is true.
     * Otherwise, only the functions in allowedFunctions are allowed.
     * <p>
     * If a function is allowed, it may be called. If it is not allowed, it will not be called.
     */
    public static class AllowedKernelFunctions extends ToolCallBehavior {
        private final Set<String> allowedFunctions;
        private final boolean allKernelFunctionsAllowed;

        /**
         * Create a new instance of AllowedKernelFunctions.
         *
         * @param allKernelFunctionsAllowed Whether all kernel functions are allowed.
         * @param autoInvoke                Whether auto-invocation is enabled.
         * @param allowedFunctions          A set of functions that are allowed.
         */
        public AllowedKernelFunctions(boolean allKernelFunctionsAllowed, boolean autoInvoke,
            @Nullable List<KernelFunction<?>> allowedFunctions) {
            super(autoInvoke ? DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS : 0);
            this.allKernelFunctionsAllowed = allKernelFunctionsAllowed;
            this.allowedFunctions = new HashSet<>();
            if (allowedFunctions != null) {
                allowedFunctions.stream().filter(Objects::nonNull).forEach(
                    f -> this.allowedFunctions
                        .add(formFullFunctionName(f.getPluginName(), f.getName())));
            }
        }

        /**
         * Check whether the given function is allowed.
         *
         * @param function The function to check.
         * @return Whether the function is allowed.
         */
        public boolean isFunctionAllowed(KernelFunction<?> function) {
            return isFunctionAllowed(function.getPluginName(), function.getName());
        }

        /**
         * Check whether the given function is allowed.
         *
         * @param pluginName   The name of the skill that the function is in.
         * @param functionName The name of the function.
         * @return Whether the function is allowed.
         */
        public boolean isFunctionAllowed(@Nullable String pluginName, String functionName) {
            String key = formFullFunctionName(pluginName, functionName);
            return allowedFunctions.contains(key);
        }

        /**
         * Check whether all kernel functions are allowed.
         *
         * @return Whether all kernel functions are allowed.
         */
        public boolean isAllKernelFunctionsAllowed() {
            return allKernelFunctionsAllowed;
        }
    }
}
