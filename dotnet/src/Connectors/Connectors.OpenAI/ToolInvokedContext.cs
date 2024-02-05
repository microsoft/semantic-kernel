// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;
public sealed class ToolInvokedContext : ToolFilterContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ToolInvokedContext"/> class.
    /// </summary>
    /// <param name="arguments">The arguments associated with the operation.</param>
    /// <param name="result">The result of the function's invocation.</param>
    public ToolInvokedContext(KernelArguments arguments, FunctionResult result, int iteration)
        : base(result.Function, arguments, iteration, (result ?? throw new ArgumentNullException(nameof(result))).Metadata)
    {
        this.Result = result;
        //this.ResultValue = result.Value;
    }

    /// <summary>
    /// Gets the result of the function's invocation.
    /// </summary>
    public FunctionResult Result { get; }

    /// <summary>
    /// Gets the raw result of the function's invocation.
    /// </summary>
    //internal object? ResultValue { get; private set; }

    /// <summary>
    /// Sets an object to use as the overridden new result for the function's invocation.
    /// </summary>
    /// <param name="value">The value to use as the new result of the function's invocation.</param>
    /*public void SetResultValue(object? value)
    {
        this.ResultValue = value;
    }*/
}
