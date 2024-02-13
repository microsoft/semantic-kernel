// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Enum describing the different ways tool calling can be stopped.
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
/// Base class with data related to tool invocation.
/// </summary>
public abstract class ToolFilterContext
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
    /// Gets or sets a value indicating whether subsequent tool calls should be stopped,
    /// and if so, which stop behavior should be followed.
    /// </summary>
    /// <remarks>
    /// If there are multiple filters registered, subsequent filters
    /// may see and change a value set by a previous filter. The final result is what will
    /// be considered by the component that triggers filter.
    /// </remarks>
    public ToolFilterStopBehavior StopBehavior { get; set; } = ToolFilterStopBehavior.None;
}
