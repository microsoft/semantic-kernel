// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Threading;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class with data related to automatic function invocation.
/// </summary>
[Experimental("SKEXP0001")]
public class AutoFunctionInvocationContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AutoFunctionInvocationContext"/> class.
    /// </summary>
    /// <param name="kernel">The <see cref="Microsoft.SemanticKernel.Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="function">The <see cref="KernelFunction"/> with which this filter is associated.</param>
    /// <param name="result">The result of the function's invocation.</param>
    /// <param name="chatHistory">The chat history associated with automatic function invocation.</param>
    /// <param name="chatMessageContent">The chat message content associated with automatic function invocation.</param>
    public AutoFunctionInvocationContext(
        Kernel kernel,
        KernelFunction function,
        FunctionResult result,
        ChatHistory chatHistory,
        ChatMessageContent chatMessageContent)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(function);
        Verify.NotNull(result);
        Verify.NotNull(chatHistory);
        Verify.NotNull(chatMessageContent);

        this.Kernel = kernel;
        this.Function = function;
        this.Result = result;
        this.ChatHistory = chatHistory;
        this.ChatMessageContent = chatMessageContent;
    }

    /// <summary>
    /// The <see cref="System.Threading.CancellationToken"/> to monitor for cancellation requests.
    /// The default is <see cref="CancellationToken.None"/>.
    /// </summary>
    public CancellationToken CancellationToken { get; init; }

    /// <summary>
    /// Gets the arguments associated with the operation.
    /// </summary>
    public KernelArguments? Arguments { get; init; }

    /// <summary>
    /// Request sequence index of automatic function invocation process. Starts from 0.
    /// </summary>
    public int RequestSequenceIndex { get; init; }

    /// <summary>
    /// Function sequence index. Starts from 0.
    /// </summary>
    public int FunctionSequenceIndex { get; init; }

    /// <summary>
    /// Number of functions that will be invoked during auto function invocation request.
    /// </summary>
    public int FunctionCount { get; init; }

    /// <summary>
    /// The ID of the tool call.
    /// </summary>
    public string? ToolCallId { get; init; }

    /// <summary>
    /// The chat message content associated with automatic function invocation.
    /// </summary>
    public ChatMessageContent ChatMessageContent { get; }

    /// <summary>
    /// Gets the <see cref="Microsoft.SemanticKernel.ChatCompletion.ChatHistory"/> associated with automatic function invocation.
    /// </summary>
    public ChatHistory ChatHistory { get; }

    /// <summary>
    /// Gets the <see cref="KernelFunction"/> with which this filter is associated.
    /// </summary>
    public KernelFunction Function { get; }

    /// <summary>
    /// Gets the <see cref="Microsoft.SemanticKernel.Kernel"/> containing services, plugins, and other state for use throughout the operation.
    /// </summary>
    public Kernel Kernel { get; }

    /// <summary>
    /// Gets or sets the result of the function's invocation.
    /// </summary>
    public FunctionResult Result { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether the operation associated with the filter should be terminated.
    /// By default it's <see langword="false"/>, in this case all functions will be executed.
    /// As soon as it's set to <see langword="true"/>, the remaining functions won't be executed and last request to LLM won't be performed.
    /// Automatic function invocation process will be terminated and result of last executed function will be returned to the caller.
    /// </summary>
    public bool Terminate { get; set; }
}
