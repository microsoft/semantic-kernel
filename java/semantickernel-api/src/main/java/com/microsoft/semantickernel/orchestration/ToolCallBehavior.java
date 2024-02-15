package com.microsoft.semantickernel.orchestration;

import com.azure.ai.openai.models.ChatCompletionsFunctionToolDefinition;
import com.azure.ai.openai.models.ChatCompletionsOptions;
import com.azure.ai.openai.models.FunctionDefinition;
import com.azure.core.util.BinaryData;
import com.microsoft.semantickernel.exceptions.SKException;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Defines the behavior of a tool call. Currently, the only tool available is function calling.
 */
public class ToolCallBehavior {

    private static final int DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS = 5;
    private static final String FUNCTION_NAME_SEPARATOR = "-";

    static String getKey(String pluginName, String functionName) {
        return String.format("%s%s%s", pluginName, FUNCTION_NAME_SEPARATOR, functionName);
    }

    private int maximumAutoInvokeAttempts;
    private boolean kernelFunctionsEnabled;
    private KernelFunction<?> requiredFunction;
    private final Set<String> enabledFunctions = new HashSet<>();

    public ToolCallBehavior() {
        this.maximumAutoInvokeAttempts = 0;
    }

    public ToolCallBehavior(ToolCallBehavior toolCallBehavior) {
        maximumAutoInvokeAttempts = toolCallBehavior.maximumAutoInvokeAttempts;
        kernelFunctionsEnabled = toolCallBehavior.kernelFunctionsEnabled;
        requiredFunction = toolCallBehavior.requiredFunction;
        enabledFunctions.addAll(toolCallBehavior.enabledFunctions);
    }

    public UnmodifiableToolCallBehavior unmodifiableClone() {
        return new UnmodifiableToolCallBehavior(this);
    }

    public ToolCallBehavior kernelFunctions(boolean enable) {
        this.kernelFunctionsEnabled = enable;
        return this;
    }

    public ToolCallBehavior autoInvoke(boolean enable) {
        this.maximumAutoInvokeAttempts = enable ? DEFAULT_MAXIMUM_AUTO_INVOKE_ATTEMPTS : 0;
        return this;
    }

    public ToolCallBehavior requireFunction(KernelFunction<?> function) {
        requiredFunction = function;
        return this;
    }

    public ToolCallBehavior enableFunction(KernelFunction<?> function, boolean enable) {
        if (function != null) {
            String key = getKey(function.getPluginName(), function.getName());
            if (enable) {
                enabledFunctions.add(key);
            } else {
                enabledFunctions.remove(key);
            }
        }
        return this;
    }

    public ToolCallBehavior setMaximumAutoInvokeAttempts(int maximumAutoInvokeAttempts) {
        if (maximumAutoInvokeAttempts < 0) {
            throw new SKException("The maximum auto-invoke attempts should be greater than or equal to zero.");
        }
        this.maximumAutoInvokeAttempts = maximumAutoInvokeAttempts;
        return this;
    }

    public boolean kernelFunctionsEnabled() {
        return kernelFunctionsEnabled;
    }

    public boolean autoInvokeEnabled() {
        return maximumAutoInvokeAttempts > 0;
    }

    public KernelFunction<?> functionRequired() {
        return requiredFunction;
    }

    public boolean functionEnabled(KernelFunction<?> function) {
        return functionEnabled(function.getPluginName(), function.getName());
    }

    public boolean functionEnabled(String pluginName, String functionName) {
        String key = getKey(pluginName, functionName);
        return enabledFunctions.contains(key);
    }

    public int getMaximumAutoInvokeAttempts() {
        return this.maximumAutoInvokeAttempts;
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
        public final ToolCallBehavior requireFunction(KernelFunction<?> function) {
            throw new UnsupportedOperationException("unmodifiable instance of ToolCallBehavior");
        }

        @Override
        public final ToolCallBehavior enableFunction(KernelFunction<?> function, boolean enable) {
            throw new UnsupportedOperationException("unmodifiable instance of ToolCallBehavior");
        }
    }

}
