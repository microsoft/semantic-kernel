// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// 
/// </summary>
public enum ToolFilterStopBehavior
{
    /// <summary>
    /// Continue using tools
    /// </summary>
    None,

    /// <summary>
    /// Cancel the current tool call, and don't invoke or request any more tools
    /// </summary>
    Cancel,

    /// <summary>
    /// Invoke the curent tool call(s) but don't request any more tools
    /// </summary>
    StopTools,

    /// <summary>
    /// Continue requesting tools, but turn off auto-invoke
    /// </summary>
    StopAutoInvoke
};

/// <summary>
/// 
/// </summary>
public abstract class ToolFilterContext // TODO: make experimental?
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ToolFilterContext"/> class.
    /// </summary>
    /// <param name="toolCall">The <see cref="OpenAIFunctionToolCall"/> with which this filter is associated.</param>
    /// <param name="chatHistory">The chat history associated with the operation.</param>
    /// <param name="modelIterations">The number of model iterations completed thus far for the request.</param>
    internal ToolFilterContext(OpenAIFunctionToolCall toolCall, ChatHistory chatHistory, int modelIterations)
    {
        Verify.NotNull(toolCall);

        this.ToolCall = toolCall;
        this.ChatHistory = chatHistory;
        this.ModelIterations = modelIterations;
    }

    /// <summary>
    /// Gets the tool call associated with this filter.
    /// </summary>
    public OpenAIFunctionToolCall ToolCall { get; }

    /// <summary>
    /// Gets the chat history associated with the operation.
    /// </summary>
    public ChatHistory ChatHistory { get; }

    /// <summary>
    /// Gets the number of model iterations that have been completed for the request so far.
    /// </summary>
    public int ModelIterations { get; }

    /// <summary>
    /// Gets or sets a value indicating whether the operation associated with
    /// the filter should be canceled.
    /// </summary>
    /// <remarks>
    /// The filter may set <see cref="Cancel"/> to true to indicate that the operation should
    /// be canceled. If there are multiple filters registered, subsequent filters
    /// may see and change a value set by a previous filter. The final result is what will
    /// be considered by the component that triggers filter.
    /// </remarks>
    //public bool Cancel { get; set; }

    //public int ToolInvocations { get; } // ?

    /// <summary>
    /// 
    /// </summary>
    public ToolFilterStopBehavior StopBehavior { get; set; } = ToolFilterStopBehavior.None;
}
