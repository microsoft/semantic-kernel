// Copyright (c) Microsoft. All rights reserved.

using System.Collections;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class with data related to automatic function invocation.
/// </summary>
public class AutoFunctionInvocationContext : KernelFunctionInvocationContext
{
    private readonly KernelFunction? _kernelFunction;
    private readonly KernelFunctionInvocationContext? _innerContext;
    /// <summary>
    /// Initializes a new instance of the <see cref="AutoFunctionInvocationContext"/> class from an existing <see cref="KernelFunctionInvocationContext"/>.
    /// </summary>
    public AutoFunctionInvocationContext(KernelFunctionInvocationContext innerContext)
    {
        Verify.NotNull(innerContext);
        Verify.NotNull(innerContext.Options);
        Verify.NotNull(innerContext.Options.AdditionalProperties);

        innerContext.Options.AdditionalProperties.TryGetValue<Kernel>("Kernel", out var kernel);
        Verify.NotNull(kernel);

        innerContext.Options.AdditionalProperties.TryGetValue<ChatMessageContent>("ChatMessageContent", out var chatMessageContent);
        Verify.NotNull(chatMessageContent);

        this._innerContext = innerContext;
        this.ChatHistory = new ChatMessageHistory(innerContext.Messages);
        this.ChatMessageContent = chatMessageContent;
        this.Kernel = kernel;
        this.Result = new FunctionResult(this._kernelFunction!) { Culture = kernel.Culture };
    }

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
        this._kernelFunction = function;
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
    [Experimental("SKEXP0001")]
    public PromptExecutionSettings? ExecutionSettings { get; init; }

    /// <summary>
    /// Gets the <see cref="Microsoft.SemanticKernel.ChatCompletion.ChatHistory"/> associated with automatic function invocation.
    /// </summary>
    public ChatHistory ChatHistory { get; }

    /// <summary>
    /// Gets the <see cref="KernelFunction"/> with which this filter is associated.
    /// </summary>
    public KernelFunction Function
    {
        get => this._innerContext?.AIFunction.AsKernelFunction() ?? this._kernelFunction!;
    }

    /// <summary>
    /// Gets the <see cref="Microsoft.SemanticKernel.Kernel"/> containing services, plugins, and other state for use throughout the operation.
    /// </summary>
    public Kernel Kernel { get; }

    /// <summary>
    /// Gets or sets the result of the function's invocation.
    /// </summary>
    public FunctionResult Result { get; set; }

    /// <summary>
    /// Mutable chat message as chat history.
    /// </summary>
    internal class ChatMessageHistory : ChatHistory, IEnumerable<ChatMessageContent>
    {
        private readonly List<ChatMessage> _messages;

        public ChatMessageHistory(IEnumerable<ChatMessage> messages) : base(messages.ToChatHistory())
        {
            this._messages = new List<ChatMessage>(messages);
        }

        public override void Add(ChatMessageContent item)
        {
            item.GetHashCode();
            base.Add(item);
            this._messages.Add(item.ToChatMessage());
        }

        public override void Clear()
        {
            base.Clear();
            this._messages.Clear();
        }

        public override bool Contains(ChatMessageContent item)
        {
            return base.Contains(item);
        }

        public override bool Remove(ChatMessageContent item)
        {
            var index = base.IndexOf(item);

            if (index < 0)
            {
                return false;
            }

            this._messages.RemoveAt(index);
            base.RemoveAt(index);

            return true;
        }

        public override void Insert(int index, ChatMessageContent item)
        {
            base.Insert(index, item);
            this._messages.Insert(index, item.ToChatMessage());
        }

        public override void RemoveAt(int index)
        {
            this._messages.RemoveAt(index);
            base.RemoveAt(index);
        }

        public override ChatMessageContent this[int index]
        {
            get => this._messages[index].ToChatMessageContent();
            set
            {
                this._messages[index] = value.ToChatMessage();
                base[index] = value;
            }
        }

        public override int Count => this._messages.Count;

        // Explicit implementation of IEnumerable<ChatMessageContent>.GetEnumerator()
        IEnumerator<ChatMessageContent> IEnumerable<ChatMessageContent>.GetEnumerator()
        {
            foreach (var message in this._messages)
            {
                yield return message.ToChatMessageContent(); // Convert and yield each item
            }
        }

        // Explicit implementation of non-generic IEnumerable.GetEnumerator()
        IEnumerator IEnumerable.GetEnumerator()
            => ((IEnumerable<ChatMessageContent>)this).GetEnumerator();
    }
}
