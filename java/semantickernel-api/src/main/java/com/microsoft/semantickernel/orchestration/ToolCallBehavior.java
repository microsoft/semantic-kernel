// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import java.util.HashSet;
import java.util.Set;
import javax.annotation.Nullable;

/**
 * Defines the behavior of a tool call. Currently, the only tool available is function calling.
 */
public class ToolCallBehavior {

    private static final int DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS = 5;
    private static final String FUNCTION_NAME_SEPARATOR = "-";
    private final Set<String> enabledFunctions = new HashSet<>();
    private int maximumAutoInvokeAttempts;
    private boolean kernelFunctionsEnabled;

    @Nullable
    private KernelFunction<?> requiredFunction;

    /**
     * Create a new instance of ToolCallBehavior with defaults.
     */
    public ToolCallBehavior() {
        this.maximumAutoInvokeAttempts = 0;
        this.kernelFunctionsEnabled = false;
        this.requiredFunction = null;
    }

    /**
     * Create a copy of the other ToolCallBehavior.
     *
     * @param toolCallBehavior The behavior to copy.
     */
    public ToolCallBehavior(ToolCallBehavior toolCallBehavior) {
        maximumAutoInvokeAttempts = toolCallBehavior.maximumAutoInvokeAttempts;
        kernelFunctionsEnabled = toolCallBehavior.kernelFunctionsEnabled;
        requiredFunction = toolCallBehavior.requiredFunction;
        enabledFunctions.addAll(toolCallBehavior.enabledFunctions);
    }

    public static String formFullFunctionName(@Nullable String pluginName, String functionName) {
        if (pluginName == null) {
            pluginName = "";
        }
        return String.format("%s%s%s", pluginName, FUNCTION_NAME_SEPARATOR, functionName);
    }

    /**
     * Create an unmodifiable copy of this ToolCallBehavior.
     *
     * @return An unmodifiable copy of this ToolCallBehavior.
     */
    public UnmodifiableToolCallBehavior unmodifiableClone() {
        return new UnmodifiableToolCallBehavior(this);
    }

    /**
     * Enable or disable kernel functions. If kernel functions are disabled, they will not be passed
     * to the model. This is the default behavior.
     *
     * @param enable Whether to enable kernel functions.
     * @return This ToolCallBehavior.
     */
    public ToolCallBehavior enableKernelFunctions(boolean enable) {
        this.kernelFunctionsEnabled = enable;
        return this;
    }

    /**
     * Enable or disable auto-invocation. If auto-invocation is enabled, the model may request that
     * the Semantic Kernel invoke functions and return the value to the model. The default behavior
     * is to disable auto-invocation.
     *
     * @param enable Whether to enable auto-invocation.
     * @return This ToolCallBehavior.
     */
    public ToolCallBehavior autoInvoke(boolean enable) {
        setMaximumAutoInvokeAttempts(enable ? DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS : 0);
        return this;
    }

    /**
     * Require or not require a function to be called. If a function is required, it will be called.
     * If it is not required, it may be called if {@code auto-invcation} is enabled. Whether the
     * functions are passed to the model is controlled by whether {@code kernelFunctions} is
     * enabled. By default, no function is required.
     *
     * @param function The function to require or not require.
     * @return This ToolCallBehavior.
     */
    public ToolCallBehavior requireFunction(KernelFunction<?> function) {
        requiredFunction = function;
        setMaximumAutoInvokeAttempts(1);
        return this;
    }

    /**
     * Enable or disable a function. If a function is enabled, it may be called. If it is not
     * enabled, it will not be called. By default, all functions are enabled. Whether the functions
     * are passed to the model is controlled by whether {@code kernelFunctions} is enabled.
     *
     * @param function The function to enable or disable.
     * @param enable   Whether to enable the function.
     * @return This ToolCallBehavior.
     */
    public ToolCallBehavior enableFunction(KernelFunction<?> function, boolean enable) {
        if (function != null) {
            String key = formFullFunctionName(function.getPluginName(), function.getName());
            if (enable) {
                enabledFunctions.add(key);
            } else {
                enabledFunctions.remove(key);
            }
        }
        return this;
    }

    /**
     * Check whether kernel functions are enabled.
     *
     * @return Whether kernel functions are enabled.
     */
    public boolean kernelFunctionsEnabled() {
        return kernelFunctionsEnabled;
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
     * Return the required function, null if it has not been specified.
     *
     * @return The function required.
     */
    @Nullable
    public KernelFunction<?> functionRequired() {
        return requiredFunction;
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
        String key = formFullFunctionName(pluginName, functionName);
        return enabledFunctions.contains(key);
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
     * Set the maximum number of times that auto-invocation will be attempted. If auto-invocation is
     * enabled, the model may request that the Semantic Kernel invoke functions and return the value
     * to the model. If the maximum number of attempts is reached, the model will be notified that
     * the function could not be invoked. The default maximum number of attempts is 5.
     *
     * @param maximumAutoInvokeAttempts The maximum number of attempts.
     * @return This ToolCallBehavior.
     */
    public ToolCallBehavior setMaximumAutoInvokeAttempts(int maximumAutoInvokeAttempts) {
        if (maximumAutoInvokeAttempts < 0) {
            throw new SKException(
                "The maximum auto-invoke attempts should be greater than or equal to zero.");
        }
        if (requiredFunction == null) {
            this.maximumAutoInvokeAttempts = maximumAutoInvokeAttempts;
        } else {
            this.maximumAutoInvokeAttempts = Math.min(1, maximumAutoInvokeAttempts);
        }
        return this;
    }

    /**
     * An unmodifiable instance of ToolCallBehavior.
     */
    public static class UnmodifiableToolCallBehavior extends ToolCallBehavior {

        protected UnmodifiableToolCallBehavior(ToolCallBehavior toolCallBehavior) {
            super(toolCallBehavior);
        }

        @Override
        public final ToolCallBehavior enableKernelFunctions(boolean enable) {
            throw new UnsupportedOperationException("unmodifiable instance of ToolCallBehavior");
        }

        @Override
        public final ToolCallBehavior autoInvoke(boolean enable) {
            throw new UnsupportedOperationException("unmodifiable instance of ToolCallBehavior");
        }

        @Override
        public final ToolCallBehavior requireFunction(KernelFunction<?> function) {
            throw new UnsupportedOperationException("unmodifiable instance of ToolCallBehavior");
        }

        @Override
        public final ToolCallBehavior enableFunction(KernelFunction<?> function, boolean enable) {
            throw new UnsupportedOperationException("unmodifiable instance of ToolCallBehavior");
        }
    }

}
