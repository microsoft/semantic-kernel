// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class with data related to automatic function invocation.
/// </summary>
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
    /// Boolean flag which indicates whether a filter is invoked within streaming or non-streaming mode.
    /// </summary>
    public bool IsStreaming { get; init; }

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
    /// The execution settings associated with the operation.
    /// </summary>
    public PromptExecutionSettings? ExecutionSettings { get; init; }

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
    ///
    /// By default, this value is <see langword="false"/>, which means all functions will be invoked.
    /// If set to <see langword="true"/>, the behavior depends on how functions are invoked:
    ///
    /// - If functions are invoked sequentially (the default behavior), the remaining functions will not be invoked,
    ///   and the last request to the LLM will not be performed.
    ///
    /// - If functions are invoked concurrently (controlled by the <see cref="FunctionChoiceBehaviorOptions.AllowConcurrentInvocation"/> option),
    ///   other functions will still be invoked, and the last request to the LLM will not be performed.
    ///
    /// In both cases, the automatic function invocation process will be terminated, and the result of the last executed function will be returned to the caller.
    /// </summary>
    public bool Terminate { get; set; }
}
