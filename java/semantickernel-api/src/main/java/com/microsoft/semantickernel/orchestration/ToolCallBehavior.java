package com.microsoft.semantickernel.orchestration;

import java.util.HashMap;
import java.util.Map;

/**
 * Defines the behavior of a tool call. Currently, the only tool available is function calling.
 */
public class ToolCallBehavior {

    private static final int DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS = 5;

    private static class FunctionCallBehavior {

        private final boolean required;
        private final boolean enabled;

        FunctionCallBehavior(KernelFunction<?> function, boolean required, boolean enabled) {
            this.required = required;
            this.enabled = enabled;
        }

        boolean required() {
            return required;
        }

        boolean enabled() {
            return enabled;
        }

        static String getKey(KernelFunction<?> function) {
            return getKey(function.getPluginName(), function.getName());
        }

        static String getKey(String skillName, String functionName) {
            return String.format("%s-%s", skillName, functionName);
        }
    }

    private final Map<String, Boolean> flags = new HashMap<>();
    private final Map<String, FunctionCallBehavior> functionSettings = new HashMap<>();
    private final Map<String, Integer> settings = new HashMap<>();

    /**
     * Create a new instance of ToolCallBehavior with defaults.
     */
    public ToolCallBehavior() {
    }

    /**
     * Create a copy of the other ToolCallBehavior.
     *
     * @param toolCallBehavior The behavior to copy.
     */
    public ToolCallBehavior(ToolCallBehavior toolCallBehavior) {
        flags.putAll(toolCallBehavior.flags);
        functionSettings.putAll(toolCallBehavior.functionSettings);
        settings.putAll(toolCallBehavior.settings);
    }

    /**
     * Create an unmodifiable copy of this ToolCallBehavior.
     * @return An unmodifiable copy of this ToolCallBehavior.
     */
    public UnmodifiableToolCallBehavior unmodifiableClone() {
        return new UnmodifiableToolCallBehavior(this);
    }

    /**
     * Enable or disable kernel functions. If kernel functions
     * are disabled, they will not be passed to the model. This
     * is the default behavior.
     *
     * @param enable Whether to enable kernel functions.
     * @return This ToolCallBehavior.
     */
    public ToolCallBehavior kernelFunctions(boolean enable) {
        setFlag("kernelFunctions", enable);
        return this;
    }

    /**
     * Enable or disable auto-invocation. If auto-invocation is
     * enabled, the model may request that the Semantic Kernel
     * invoke functions and return the value to the model. The 
     * default behavior is to disable auto-invocation.
     *
     * @param enable Whether to enable auto-invocation.
     * @return This ToolCallBehavior.
     */
    public ToolCallBehavior autoInvoke(boolean enable) {
        setFlag("autoInvoke", enable);
        return this;
    }

    /**
     * Require or not require a function to be called. If a function
     * is required, it will be called. If it is not required, it may
     * be called if {@code auto-invcation} is enabled. Whether the functions
     * are passed to the model is controlled by whether {@code kernelFunctions}
     * is enabled. By default, no functions are required.
     *
     * @param function The function to require or not require.
     * @param require  Whether to require the function.
     * @return This ToolCallBehavior.
     */
    public ToolCallBehavior requireFunction(KernelFunction<?> function, boolean require) {
        if (function != null) {
            String key = FunctionCallBehavior.getKey(function);
            functionSettings.compute(
                key,
                (k, v) -> {
                    if (v == null) {
                        return new FunctionCallBehavior(function, require, false);
                    } else {
                        return new FunctionCallBehavior(function, require, v.enabled());
                    }
                }
            );
        }
        return this;
    }

    /**
     * Enable or disable a function. If a function is enabled, it
     * may be called. If it is not enabled, it will not be called.
     * By default, all functions are enabled. Whether the functions
     * are passed to the model is controlled by whether {@code kernelFunctions}
     * is enabled.
     *
     * @param function The function to enable or disable.
     * @param enable   Whether to enable the function.
     * @return This ToolCallBehavior.
     */
    public ToolCallBehavior enableFunction(KernelFunction<?> function, boolean enable) {
        if (function != null) {
            String key = FunctionCallBehavior.getKey(function);
            functionSettings.compute(
                key,
                (k, v) -> {
                    if (v == null) {
                        return new FunctionCallBehavior(function, false, enable);
                    } else {
                        return new FunctionCallBehavior(function, v.required(), enable);
                    }
                }
            );
        }
        return this;
    }

    /**
     * Set the maximum number of times that auto-invocation will be attempted.
     * If auto-invocation is enabled, the model may request that the Semantic Kernel
     * invoke functions and return the value to the model. If the maximum number of
     * attempts is reached, the model will be notified that the function could not be
     * invoked. The default maximum number of attempts is 5.
     *
     * @param maximumAutoInvokeAttempts The maximum number of attempts.
     * @return This ToolCallBehavior.
     */
    public ToolCallBehavior maximumAutoInvokeAttempts(int maximumAutoInvokeAttempts) {
        setSetting("maximumAutoInvokeAttempts", maximumAutoInvokeAttempts);
        return this;
    }

    /**
     * Check whether kernel functions are enabled.
     * @return Whether kernel functions are enabled.
     */
    public boolean kernelFunctionsEnabled() {
        return getFlag("kernelFunctions");
    }

    /**
     * Check whether auto-invocation is enabled.
     * @return Whether auto-invocation is enabled.
     */
    public boolean autoInvokeEnabled() {
        return getFlag("autoInvoke");
    }

    /**
     * Check whether the given function is required.
     * @param function The function to check.
     * @return Whether the function is required.
     */
    public boolean functionRequired(KernelFunction<?> function) {
        if (function != null) {
            return functionRequired(function.getPluginName(), function.getName());
        }
        return false;
    }

    /**
     * Check whether the given function is required.
     * @param pluginName   The name of the skill that the function is in.
     * @param functionName The name of the function.
     * @return Whether the function is required.
     */
    public boolean functionRequired(String pluginName, String functionName) {
        String key = FunctionCallBehavior.getKey(pluginName, functionName);
        if (functionSettings.containsKey(key)) {
            return functionSettings.get(key).required();
        }
        return false;
    }

    /**
     * Check whether the given function is enabled.
     * @param function The function to check.
     * @return Whether the function is enabled.
     */
    public boolean functionEnabled(KernelFunction<?> function) {

        if (function != null) {
            return functionEnabled(function.getPluginName(), function.getName());
        }
        return functionSettings.isEmpty();
    }

    /**
     * Check whether the given function is enabled.
     * @param pluginName   The name of the skill that the function is in.
     * @param functionName The name of the function.
     * @return Whether the function is enabled.
     */
    public boolean functionEnabled(String pluginName, String functionName) {

        String key = FunctionCallBehavior.getKey(pluginName, functionName);
        if (functionSettings.containsKey(key)) {
            return functionSettings.get(key).enabled();
        }
        return functionSettings.isEmpty();
    }

    /**
     * Get the maximum number of times that auto-invocation will be attempted.
     * @return The maximum number of attempts.
     */
    public int maximumAutoInvokeAttempts() {
        return getSetting("maximumAutoInvokeAttempts", DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS);
    }

    /**
     * Set a flag.
     * @param key The key for the flag
     * @param value The value for the flag
     */
    protected void setFlag(String key, boolean value) {
        flags.put(key, value);
    }

    /**
     * Set a setting.
     * @param key The key for the setting
     * @param value The value for the setting
     */
    protected void setSetting(String key, int value) {
        settings.put(key, value);
    }

    /**
     * Get a flag.
     * @param key The key for the flag
     * @return The value for the flag
     */
    protected boolean getFlag(String key) {
        return flags.getOrDefault(key, false);
    }

    /**
     * Get a setting.
     * @param key The key for the setting
     * @param defaultValue The default value for the setting
     * @return The value for the setting
     */
    protected int getSetting(String key, int defaultValue) {
        return settings.getOrDefault(key, defaultValue);
    }

    /**
     * An unmodifiable instance of ToolCallBehavior.
     */
    public static class UnmodifiableToolCallBehavior extends ToolCallBehavior {

        protected UnmodifiableToolCallBehavior(ToolCallBehavior toolCallBehavior) {
            super(toolCallBehavior);
        }

        @Override
        public final ToolCallBehavior kernelFunctions(boolean enable) {
            throw new UnsupportedOperationException("unmodifiable instance of ToolCallBehavior");
        }

        @Override
        public final ToolCallBehavior autoInvoke(boolean enable) {
            throw new UnsupportedOperationException("unmodifiable instance of ToolCallBehavior");
        }

        @Override
        public final ToolCallBehavior requireFunction(KernelFunction<?> function, boolean require) {
            throw new UnsupportedOperationException("unmodifiable instance of ToolCallBehavior");
        }

        @Override
        public final ToolCallBehavior enableFunction(KernelFunction<?> function, boolean enable) {
            throw new UnsupportedOperationException("unmodifiable instance of ToolCallBehavior");
        }

        @Override 
        protected final void setFlag(String key, boolean value) {
            throw new UnsupportedOperationException("unmodifiable instance of ToolCallBehavior");
        }

        @Override
        protected final void setSetting(String key, int value) {
            throw new UnsupportedOperationException("unmodifiable instance of ToolCallBehavior");
        }   

    }    

}
