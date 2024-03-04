// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import javax.annotation.Nullable;

public class OpenAIFunctionToolCall {

    /// <summary>Gets the ID of the tool call.</summary>
    @Nullable
    private final String id;

    /// <summary>Gets the name of the plugin with which this function is associated, if any.</summary>

    @Nullable
    private final String pluginName;

    /// <summary>Gets the name of the function.</summary>
    private final String functionName;

    /// <summary>Gets a name/value collection of the arguments to the function, if any.</summary>
    @Nullable
    private final KernelFunctionArguments arguments;

    public OpenAIFunctionToolCall(
        @Nullable String id,
        @Nullable String pluginName,
        String functionName,
        @Nullable KernelFunctionArguments arguments) {
        this.id = id;
        this.pluginName = pluginName;
        this.functionName = functionName;
        this.arguments = arguments;
    }

    @Nullable
    public String getId() {
        return id;
    }

    @Nullable
    public String getPluginName() {
        return pluginName;
    }

    public String getFunctionName() {
        return functionName;
    }

    @Nullable
    public KernelFunctionArguments getArguments() {
        return arguments;
    }
}
