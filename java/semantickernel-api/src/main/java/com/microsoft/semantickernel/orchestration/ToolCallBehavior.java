package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import javax.annotation.Nullable;

/**
 * Defines the behavior of a tool call. Currently, the only tool available is function calling.
 */
public class ToolCallBehavior {
    private static final int DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS = 5;
    private static final String FUNCTION_NAME_SEPARATOR = "-";

    static String getKey(@Nullable String pluginName, String functionName) {
        if (pluginName == null) {
            pluginName = "";
        }
        return String.format("%s%s%s", pluginName, FUNCTION_NAME_SEPARATOR, functionName);
    }

    private final int maximumAutoInvokeAttempts;
    private final boolean kernelFunctionsEnabled;
    @Nullable
    private final KernelFunction<?> requiredFunction;
    private final Set<String> enabledFunctions;

    /**
     * Create a new instance of ToolCallBehavior with defaults.
     */
    public ToolCallBehavior(boolean kernelFunctionsEnabled, int maximumAutoInvokeAttempts,
        @Nullable Set<String> enabledFunctions, @Nullable KernelFunction<?> requiredFunction) {
        this.kernelFunctionsEnabled = kernelFunctionsEnabled;
        this.maximumAutoInvokeAttempts = maximumAutoInvokeAttempts;
        this.requiredFunction = requiredFunction;
        this.enabledFunctions = enabledFunctions != null ? enabledFunctions : new HashSet<>();
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
        String key = getKey(pluginName, functionName);
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
     * Get the fluent builder for creating a new instance of {@code ToolCallBehavior}.
     * @return The fluent builder for creating a new instance of {@code ToolCallBehavior}.
     */
    public static Builder builder() {
        return new Builder();
    }

    public static class Builder implements Buildable {
        private int maximumAutoInvokeAttempts;
        private boolean kernelFunctionsEnabled;

        @Nullable
        private KernelFunction<?> requiredFunction;
        private final Set<String> enabledFunctions = new HashSet<>();

        /**
         * Enable kernel functions. If kernel functions are disabled, they will not be passed
         * to the model unless specific functions have been enabled via {@code enableFunctions}.
         * <p>
         * By default, all kernel functions are disabled.
         *
         * @return This ToolCallBehavior.
         */
        public Builder enableKernelFunctions() {
            kernelFunctionsEnabled = true;
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
        public Builder autoInvoke(boolean enable) {
            return withMaximumAutoInvokeAttempts(enable ? DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS : 0);
        }

        /**
         * Require or not require a function to be called.
         * If a function is required, it will the only function to be passed to the model and be called.
         * By default, no function is required.
         *
         * @param function The function to require or not require.
         * @return This ToolCallBehavior.
         */
        public Builder requireFunction(KernelFunction<?> function) {
            requiredFunction = function;
            return withMaximumAutoInvokeAttempts(1);
        }

        /**
         * Enable a function.
         * If a function is enabled, it may be called. If it is not enabled, it will not be called.
         * By default, all functions are disabled.
         *
         * @param function The function to enable.
         * @return This ToolCallBehavior.
         */
        public Builder enableFunction(KernelFunction<?> function) {
            if (function != null) {
                enabledFunctions.add(getKey(function.getPluginName(), function.getName()));
            }
            return this;
        }

        /**
         * Enable a set of functions.
         * If a function is enabled, it may be called. If it is not enabled, it will not be called.
         * By default, all functions are disabled.
         *
         * @param functions The functions to enable.
         * @return This ToolCallBehavior.
         */
        public Builder enableFunctions(List<KernelFunction<?>> functions) {
            if (functions != null) {
                functions.forEach(this::enableFunction);
            }
            return this;
        }

        /**
         * Enable a set of functions.
         * If a function is enabled, it may be called. If it is not enabled, it will not be called.
         * By default, all functions are disabled.
         *
         * @param functions The functions to enable.
         * @return This ToolCallBehavior.
         */
        public Builder enableFunctions(KernelFunction<?>... functions) {
            return enableFunctions(Arrays.asList(functions));
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
        public Builder withMaximumAutoInvokeAttempts(int maximumAutoInvokeAttempts) {
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
         * Create a new ToolCallBehavior instance from the builder.
         *
         * @return The new ToolCallBehavior instance
         */
        public ToolCallBehavior build() {
            return new ToolCallBehavior(
                kernelFunctionsEnabled,
                maximumAutoInvokeAttempts,
                enabledFunctions,
                requiredFunction);
        }
    }
}
