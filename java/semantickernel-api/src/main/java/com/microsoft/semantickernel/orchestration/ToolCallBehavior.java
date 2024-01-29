package com.microsoft.semantickernel.orchestration;

import java.util.HashMap;
import java.util.Map;

/**
 * Defines the behavior of a tool call. Currently, the only tool available is function calling.
 */
public class ToolCallBehavior {

    private static final int DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS = 5;

    private static class FunctionCallBehavior {

        private final String key;
        private final boolean required;
        private final boolean enabled;

        FunctionCallBehavior(KernelFunction function, boolean required, boolean enabled) {
            this.key = getKey(function);
            this.required = required;
            this.enabled = enabled;
        }

        boolean required() {
            return required;
        }

        boolean enabled() {
            return enabled;
        }

        static String getKey(KernelFunction function) {
            return getKey(function.getSkillName(), function.getName());
        }

        static String getKey(String skillName, String functionName) {
            return String.format("%s-%s", skillName, functionName);
        }
    }

    private final Map<String, Boolean> flags = new HashMap<>();
    private final Map<String, FunctionCallBehavior> functionSettings = new HashMap<>();
    private final Map<String, Integer> settings = new HashMap<>();

    public ToolCallBehavior() {
    }

    public ToolCallBehavior(ToolCallBehavior toolCallBehavior) {
        flags.putAll(toolCallBehavior.flags);
        functionSettings.putAll(toolCallBehavior.functionSettings);
        settings.putAll(toolCallBehavior.settings);
    }

    public ToolCallBehavior kernelFunctions(boolean enable) {
        setFlag("kernelFunctions", enable);
        return this;
    }

    public ToolCallBehavior autoInvoke(boolean enable) {
        setFlag("autoInvoke", true);
        return this;
    }

    public ToolCallBehavior requireFunction(KernelFunction function, boolean require) {
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

    public ToolCallBehavior enableFunction(KernelFunction function, boolean enable) {
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

    public ToolCallBehavior maximumAutoInvokeAttempts(int maximumAutoInvokeAttempts) {
        setSetting("maximumAutoInvokeAttempts", maximumAutoInvokeAttempts);
        return this;
    }

    public boolean kernelFunctionsEnabled() {
        return getFlag("kernelFunctions");
    }

    public boolean autoInvokeEnabled() {
        return getFlag("autoInvoke");
    }

    public boolean functionRequired(KernelFunction function) {
        if (function != null) {
            return functionRequired(function.getSkillName(), function.getName());
        }
        return false;
    }

    public boolean functionRequired(String pluginName, String functionName) {
        String key = FunctionCallBehavior.getKey(pluginName, functionName);
        if (functionSettings.containsKey(key)) {
            return functionSettings.get(key).required();
        }
        return false;
    }

    public boolean functionEnabled(KernelFunction function) {

        if (function != null) {
            return functionEnabled(function.getSkillName(), function.getName());
        }
        return functionSettings.isEmpty();
    }

    public boolean functionEnabled(String pluginName, String functionName) {

        String key = FunctionCallBehavior.getKey(pluginName, functionName);
        if (functionSettings.containsKey(key)) {
            return functionSettings.get(key).enabled();
        }
        return functionSettings.isEmpty();
    }

    public int maximumAutoInvokeAttempts() {
        return getSetting("maximumAutoInvokeAttempts", DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS);
    }

    protected void setFlag(String key, boolean value) {
        flags.put(key, value);
    }

    protected void setSetting(String key, int value) {
        settings.put(key, value);
    }

    protected boolean getFlag(String key) {
        return flags.getOrDefault(key, false);
    }

    protected int getSetting(String key, int defaultValue) {
        return settings.getOrDefault(key, defaultValue);
    }

}
