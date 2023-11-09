// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.ChatCompletion;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

public class FunctionCallingStepwisePlannerResult
{
    public string Message { get; } = string.Empty;

    public ChatHistory ChatHistory { get; }

    public FunctionCallingStepwisePlannerResult(string message, ChatHistory history)
    {
        this.Message = message;
        this.ChatHistory = history;
    }
}
