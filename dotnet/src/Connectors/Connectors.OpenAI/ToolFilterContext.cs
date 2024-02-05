// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;
public abstract class ToolFilterContext // TODO: make experimental?
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionFilterContext"/> class.
    /// </summary>
    /// <param name="function">The <see cref="KernelFunction"/> with which this filter is associated.</param>
    /// <param name="arguments">The arguments associated with the operation.</param>
    /// <param name="metadata">A dictionary of metadata associated with the operation.</param>
    internal ToolFilterContext(/*KernelFunction function, KernelArguments arguments, IReadOnlyDictionary<string, object?>? metadata*/)
    {
        //Verify.NotNull(function);
        //Verify.NotNull(arguments);

        //this.Function = function;n
        //this.Arguments = arguments;
        //this.Metadata = metadata;
    }

    /// <summary>
    /// Gets the <see cref="OpenAIFunctionToolCall"/> with which this filter is associated.
    /// </summary>
    public OpenAIFunctionToolCall ToolCall { get; } // TODO: how to support other types of tool calls in the future?

    /// <summary>
    /// Gets the chat history associated with the operation.
    /// </summary>
    public ChatHistory ChatHistory { get; }

    /// <summary>
    /// Gets a dictionary of metadata associated with the operation.
    /// </summary>
    //public IReadOnlyDictionary<string, object?>? Metadata { get; }

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

    // invoke subsequent tools / request subsequent tools
    // ToolCallBehavior?
}
