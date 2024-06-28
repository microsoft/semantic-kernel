// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.google.chatcompletion;

import com.google.cloud.vertexai.api.FunctionCall;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

public class GeminiFunctionCall {
    @Nonnull
    private final FunctionCall functionCall;
    @Nullable
    private final FunctionResult<?> functionResult;
    private final String pluginName;
    private final String functionName;

    @SuppressFBWarnings("EI_EXPOSE_REP2")
    public GeminiFunctionCall(
        @Nonnull FunctionCall functionCall,
        @Nullable FunctionResult<?> functionResult) {
        this.functionCall = functionCall;
        this.functionResult = functionResult;

        String[] name = functionCall.getName().split(ToolCallBehavior.FUNCTION_NAME_SEPARATOR);
        this.pluginName = name[0];
        this.functionName = name[1];
    }

    public String getPluginName() {
        return pluginName;
    }

    public String getFunctionName() {
        return functionName;
    }

    @SuppressFBWarnings("EI_EXPOSE_REP")
    public FunctionCall getFunctionCall() {
        return functionCall;
    }

    @Nullable
    public FunctionResult<?> getFunctionResult() {
        return functionResult;
    }
}
