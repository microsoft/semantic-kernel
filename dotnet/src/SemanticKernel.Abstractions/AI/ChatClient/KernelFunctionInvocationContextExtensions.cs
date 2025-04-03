// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.ChatCompletion;

// Slight modified source from
// https://raw.githubusercontent.com/dotnet/extensions/refs/heads/main/src/Libraries/Microsoft.Extensions.AI/ChatCompletion/FunctionInvocationContext.cs

/// <summary>Provides context for an in-flight function invocation.</summary>
internal static class KernelFunctionInvocationContextExtensions
{
    internal static AutoFunctionInvocationContext ToAutoFunctionInvocationContext(this KernelFunctionInvocationContext context, Microsoft.Extensions.AI.FunctionCallContent functionCall, Kernel kernel, ChatMessage message, bool isStreaming)
    {
        if (context is null)
        {
            throw new ArgumentNullException(nameof(context));
        }

        return new AutoFunctionInvocationContext(
            kernel: kernel,
            function: context.Function.AsKernelFunction(),
            result: null,
            chatHistory: context.Messages.ToChatHistory(),
            chatMessageContent: message.ToChatMessageContent())
        {
            Arguments = new(functionCall.Arguments),
            FunctionName = functionCall.Name,
            FunctionCount = context.FunctionCount,
            FunctionSequenceIndex = context.FunctionCallIndex,
            RequestSequenceIndex = context.Iteration,
            IsStreaming = isStreaming,
            ToolCallId = functionCall.CallId,
            ExecutionSettings = context.Options.ToPromptExecutionSettings()
        };
    }
}
