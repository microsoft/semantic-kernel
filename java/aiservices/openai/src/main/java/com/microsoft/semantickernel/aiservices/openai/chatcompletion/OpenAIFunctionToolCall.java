// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import javax.annotation.Nullable;

/**
 * Represents a call to a function in the OpenAI tool.
 */
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

    /**
     * Creates a new instance of the {@link OpenAIFunctionToolCall} class.
     *
     * @param id           The ID of the tool call.
     * @param pluginName   The name of the plugin with which this function is associated, if any.
     * @param functionName The name of the function.
     * @param arguments    A name/value collection of the arguments to the function, if any.
     */
    public OpenAIFunctionToolCall(
        @Nullable String id,
        @Nullable String pluginName,
        String functionName,
        @Nullable KernelFunctionArguments arguments) {
        this.id = id;
        this.pluginName = pluginName;
        this.functionName = functionName;
        if (arguments == null) {
            this.arguments = null;
        } else {
            this.arguments = arguments.copy();
        }
    }

    /**
     * Gets the ID of the tool call.
     *
     * @return The ID of the tool call.
     */
    @Nullable
    public String getId() {
        return id;
    }

    /**
     * Gets the name of the plugin with which this function is associated, if any.
     *
     * @return The name of the plugin with which this function is associated, if any.
     */
    @Nullable
    public String getPluginName() {
        return pluginName;
    }

    /**
     * Gets the name of the function.
     *
     * @return The name of the function.
     */
    public String getFunctionName() {
        return functionName;
    }

    /**
     * Gets a name/value collection of the arguments to the function, if any.
     *
     * @return A name/value collection of the arguments to the function, if any.
     */
    @Nullable
    public KernelFunctionArguments getArguments() {
        if (arguments == null) {
            return null;
        }
        return arguments.copy();
    }
}
