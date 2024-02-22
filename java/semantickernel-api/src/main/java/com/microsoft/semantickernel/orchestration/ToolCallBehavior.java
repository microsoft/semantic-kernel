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
    private static final int DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS = 5;
    private static final String FUNCTION_NAME_SEPARATOR = "-";

    private static String getKey(@Nullable String pluginName, String functionName) {
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
    private ToolCallBehavior(boolean kernelFunctionsEnabled, int maximumAutoInvokeAttempts,
        @Nullable List<KernelFunction<?>> enabledFunctions, @Nullable KernelFunction<?> requiredFunction) {
        this.kernelFunctionsEnabled = kernelFunctionsEnabled;
        this.maximumAutoInvokeAttempts = maximumAutoInvokeAttempts;
        this.requiredFunction = requiredFunction;
        this.enabledFunctions = new HashSet<>();
        if (enabledFunctions != null) {
            enabledFunctions.stream()
                .filter(Objects::nonNull)
                .forEach(f -> this.enabledFunctions.add(getKey(f.getPluginName(), f.getName())));
        }
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
     * Get the maximum number of times that auto-invocation will be attempted.
     *
     * @param autoInvoke Whether auto-invocation is enabled or not
     * @return The maximum number of attempts.
     */
    private static int getAutoInvokeAttempts(boolean autoInvoke) {
        return autoInvoke ? DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS : 0;
    }


    /**
     * Enable kernel functions. All Kernel functions will be passed to the model.
     *
     * @param autoInvoke Enable or disable auto-invocation.
     *                   If auto-invocation is enabled, the model may request that the Semantic Kernel
     *                   invoke the kernel functions and return the value to the model.
     * @return A new ToolCallBehavior instance with kernel functions enabled.
     */
    public static ToolCallBehavior enableKernelFunctions(boolean autoInvoke) {
        return new ToolCallBehavior(true, getAutoInvokeAttempts(autoInvoke), null, null);
    }

    /**
     * Require a function. It will the only function to be passed to the model and be called.
     * <p>
     *
     * @param function The function to require.
     * @return A new ToolCallBehavior instance with the required function.
     */
    public static ToolCallBehavior requireFunction(KernelFunction<?> function) {
        return new ToolCallBehavior(false, 1, null, function);
    }

    /**
     * Enable a set of functions.
     * If a function is enabled, it may be called. If it is not enabled, it will not be called.
     * By default, all functions are disabled.
     *
     * @param functions The functions to enable.
     * @return A new ToolCallBehavior instance with the enabled functions.
     */
    public static ToolCallBehavior enableFunctions(boolean autoInvoke, List<KernelFunction<?>> functions) {
        return new ToolCallBehavior(false, getAutoInvokeAttempts(autoInvoke), functions, null);
    }

    /**
     * Enable a set of functions.
     * If a function is enabled, it may be called. If it is not enabled, it will not be called.
     * By default, all functions are disabled.
     *
     * @param functions The functions to enable.
     * @return A new ToolCallBehavior instance with the enabled functions.
     */
    public static ToolCallBehavior enableFunctions(boolean autoInvoke, KernelFunction<?>... functions) {
        return enableFunctions(autoInvoke, Arrays.asList(functions));
    }
}
