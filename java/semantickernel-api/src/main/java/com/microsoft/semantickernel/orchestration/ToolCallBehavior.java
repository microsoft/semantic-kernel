package com.microsoft.semantickernel.orchestration;

import com.azure.ai.openai.models.ChatCompletionsFunctionToolDefinition;
import com.azure.ai.openai.models.ChatCompletionsOptions;
import com.azure.ai.openai.models.FunctionDefinition;
import com.azure.core.util.BinaryData;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Defines the behavior of a tool call. Currently, the only tool available is function calling.
 */
public class ToolCallBehavior {

    private static final int DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS = 5;

    private static class FunctionCallBehavior {

        private final boolean required;
        private final boolean enabled;

        FunctionCallBehavior(KernelFunction function, boolean required, boolean enabled) {
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
            return getKey(function.getPluginName(), function.getName());
        }

        static String getKey(String skillName, String functionName) {
            return String.format("%s-%s", skillName, functionName);
        }
    }

    private final Map<String, Boolean> flags = new HashMap<>();
    private final Map<String, FunctionCallBehavior> functionSettings = new HashMap<>();
    private final Map<String, Integer> settings = new HashMap<>();

    private int maximumAutoInvokeAttempts;

    public ToolCallBehavior() {
        this.maximumAutoInvokeAttempts = 0;
    }

    public ToolCallBehavior(ToolCallBehavior toolCallBehavior) {
        flags.putAll(toolCallBehavior.flags);
        functionSettings.putAll(toolCallBehavior.functionSettings);
        settings.putAll(toolCallBehavior.settings);
        maximumAutoInvokeAttempts = toolCallBehavior.maximumAutoInvokeAttempts;
    }

    public UnmodifiableToolCallBehavior unmodifiableClone() {
        return new UnmodifiableToolCallBehavior(this);
    }

    public ToolCallBehavior kernelFunctions(boolean enable) {
        setFlag("kernelFunctions", enable);
        return this;
    }

    public ToolCallBehavior autoInvoke(boolean enable) {
        this.maximumAutoInvokeAttempts = enable ? DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS : 0;
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

    public ToolCallBehavior setMaximumAutoInvokeAttempts(int maximumAutoInvokeAttempts) {
        this.maximumAutoInvokeAttempts = maximumAutoInvokeAttempts;
        return this;
    }

    public boolean kernelFunctionsEnabled() {
        return getFlag("kernelFunctions");
    }

    public boolean functionRequired(KernelFunction function) {
        if (function != null) {
            return functionRequired(function.getPluginName(), function.getName());
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
            return functionEnabled(function.getPluginName(), function.getName());
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

    public int getMaximumAutoInvokeAttempts() {
        return this.maximumAutoInvokeAttempts;
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

    public void configureOptions(
            ChatCompletionsOptions options,
            List<FunctionDefinition> functions) {
        if (functions.isEmpty()) {
            return;
        }

        options.setTools(functions.stream()
//            .filter(function -> {
//                String[] parts = function.getName().split("_");
//                String pluginName = parts.length > 0 ? parts[0] : "";
//                String fnName = parts.length > 1 ? parts[1] : "";
//                return toolCallBehavior.functionEnabled(pluginName, fnName);
//            })
            .map(ChatCompletionsFunctionToolDefinition::new)
            .collect(Collectors.toList()));

        options.setToolChoice(BinaryData.fromString("auto"));
    }

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
        public final ToolCallBehavior requireFunction(KernelFunction function, boolean require) {
            throw new UnsupportedOperationException("unmodifiable instance of ToolCallBehavior");
        }

        @Override
        public final ToolCallBehavior enableFunction(KernelFunction function, boolean enable) {
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
