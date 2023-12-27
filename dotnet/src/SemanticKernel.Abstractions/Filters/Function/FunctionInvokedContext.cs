// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel;

public class FunctionInvokedContext : FunctionFilterContext
{
    public FunctionInvokedContext(KernelFunction function, KernelArguments arguments, FunctionResult result)
        : base(function, arguments, (result ?? throw new ArgumentNullException(nameof(result))).Metadata)
    {
        this.Result = result;
        this.ResultValue = result.Value;
    }

    /// <summary>Gets the result of the function's invocation.</summary>
    public FunctionResult Result { get; }

    /// <summary>Gets the raw result of the function's invocation.</summary>
    internal object? ResultValue { get; private set; }

    /// <summary>Sets an object to use as the overridden new result for the function's invocation.</summary>
    /// <param name="value">The value to use as the new result of the function's invocation.</param>
    public void SetResultValue(object? value)
    {
        this.ResultValue = value;
    }
}
