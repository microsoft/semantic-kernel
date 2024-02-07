// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;
public sealed class ToolInvokedContext : ToolFilterContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ToolInvokedContext"/> class.
    /// </summary>
    /// <param name="arguments">The arguments associated with the operation.</param>
    /// <param name="result">The result of the function's invocation.</param>
    public ToolInvokedContext(ToolCallBehavior toolCallBehavior, int modelIteration, KernelArguments? arguments, FunctionResult result, ChatHistory chatHistory)
        : base(toolCallBehavior, modelIteration, result.Function, arguments, (result ?? throw new ArgumentNullException(nameof(result))).Metadata, chatHistory)
    {
        this.Result = result;
    }

    /// <summary>
    /// Gets the result of the function's invocation.
    /// </summary>
    public FunctionResult Result { get; }
}
