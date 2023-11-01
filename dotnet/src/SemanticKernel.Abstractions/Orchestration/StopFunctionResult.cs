// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Orchestration;

internal sealed class StopFunctionResult : FunctionResult
{
    internal StopReason Reason { get; }

    public StopFunctionResult(string functionName, string pluginName, SKContext context, StopReason stopReason) : this(functionName, pluginName, context, null, stopReason)
    {
    }

    public StopFunctionResult(string functionName, string pluginName, SKContext context, object? value, StopReason stopReason) : base(functionName, pluginName, context, value)
    {
        this.Reason = stopReason;
    }

    internal enum StopReason
    {
        InvokingSkipped = 0,
        InvokingCancelled = 1,
        InvokedCancelled = 2,
    }
}
