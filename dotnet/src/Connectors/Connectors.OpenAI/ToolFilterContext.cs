// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

public enum ToolFilterStopBehavior
{
    None,
    Cancel,
    StopTools,
    StopAutoInvoke
};

public abstract class ToolFilterContext // TODO: make experimental?
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ToolFilterContext"/> class.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> with which this filter is associated.</param>
    /// <param name="arguments">The arguments associated with the operation.</param>
    /// <param name="metadata">A dictionary of metadata associated with the operation.</param>
    internal ToolFilterContext(ToolCallBehavior toolCallBehavior, int modelIteration, KernelFunction function, KernelArguments? arguments, IReadOnlyDictionary<string, object?>? metadata, ChatHistory chatHistory)
    {
        Verify.NotNull(function);
        Verify.NotNull(arguments);

        this.Function = function;
        this.Arguments = arguments;
        this.ModelIterations = modelIteration;
        this.Metadata = metadata;

        this.ChatHistory = chatHistory;
        this.ToolCallBehavior = toolCallBehavior;
    }

    /// <summary>
    /// Gets the <see cref="KernelFunction"/> associated with the tool call.
    /// </summary>
    public KernelFunction Function { get; }

    /// <summary>
    /// Gets the arguments associated with the tool call.
    /// </summary>
    public KernelArguments Arguments { get; }

    /// <summary>
    /// Gets the chat history associated with the operation.
    /// </summary>
    public ChatHistory ChatHistory { get; }

    /// <summary>
    /// Gets a dictionary of metadata associated with the operation.
    /// </summary>
    public IReadOnlyDictionary<string, object?>? Metadata { get; }

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
    public bool Cancel { get; set; }

    //public bool AutoInvoke { get; set; } = true;

    //public bool UseTools { get; set; } = true;

    /// <summary>
    /// Gets the number of model iterations that have been completed for the request so far.
    /// </summary>
    public int ModelIterations { get; } // ?

    //public int ToolInvocations { get; } // ?

    /// <summary>
    /// Gets the tool call behavior associated with the operation.
    /// </summary>
    public ToolCallBehavior? ToolCallBehavior { get; set; }



    public ToolFilterStopBehavior StopBehavior { get; set; } = ToolFilterStopBehavior.None;


}

