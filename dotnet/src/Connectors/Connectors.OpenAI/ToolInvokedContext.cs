// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Class with data related to tool after invocation.
/// </summary>
[Experimental("SKEXP0016")]
public sealed class ToolInvokedContext : ToolFilterContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ToolInvokedContext"/> class.
    /// </summary>
    /// <param name="toolCall">The <see cref="OpenAIFunctionToolCall"/> with which this filter is associated.</param>
    /// <param name="result">The result of the tool's invocation.</param>
    /// <param name="chatHistory">The chat history associated with the operation.</param>
    /// <param name="modelIterations">The number of model iterations completed thus far for the request.</param>
    public ToolInvokedContext(OpenAIFunctionToolCall toolCall, object? result, ChatHistory chatHistory, int modelIterations)
        : base(toolCall, chatHistory, modelIterations)
    {
        this.Result = result;
    }

    /// <summary>
    /// Gets the result of the tool's invocation.
    /// </summary>
    public object? Result { get; }
}
