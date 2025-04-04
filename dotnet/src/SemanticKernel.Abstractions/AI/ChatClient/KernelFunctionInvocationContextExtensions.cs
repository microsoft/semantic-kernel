// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;

namespace Microsoft.SemanticKernel.ChatCompletion;

// Slight modified source from
// https://raw.githubusercontent.com/dotnet/extensions/refs/heads/main/src/Libraries/Microsoft.Extensions.AI/ChatCompletion/FunctionInvocationContext.cs

/// <summary>Provides context for an in-flight function invocation.</summary>
internal static class KernelFunctionInvocationContextExtensions
{
    internal static AutoFunctionInvocationContext ToAutoFunctionInvocationContext(this KernelFunctionInvocationContext context)
    {
        if (context is null)
        {
            throw new ArgumentNullException(nameof(context));
        }

        var kernelFunction = context.Function.AsKernelFunction();
        return new AutoFunctionInvocationContext(
            kernel: context.Kernel,
            function: kernelFunction,
            result: context.Result,
            chatHistory: context.Messages.ToChatHistory(),
            chatMessageContent: context.Response!.Messages.Last().ToChatMessageContent())
        {
            Arguments = context.CallContent.Arguments is null ? null : new(context.CallContent.Arguments),
            FunctionCount = context.FunctionCount,
            FunctionSequenceIndex = context.FunctionCallIndex,
            RequestSequenceIndex = context.Iteration,
            IsStreaming = context.IsStreaming,
            ToolCallId = context.CallContent.CallId,
            ExecutionSettings = context.Options.ToPromptExecutionSettings()
        };
    }
}
