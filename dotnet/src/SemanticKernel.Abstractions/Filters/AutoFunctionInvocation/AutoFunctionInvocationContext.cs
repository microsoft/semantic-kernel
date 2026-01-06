// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
#if !UNITY
using Microsoft.Extensions.AI;
#endif
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class with data related to automatic function invocation.
/// </summary>
#if !UNITY
public class AutoFunctionInvocationContext : Microsoft.Extensions.AI.FunctionInvocationContext
#else
public class AutoFunctionInvocationContext
#endif
{
    private ChatHistory? _chatHistory;

#if !UNITY
    /// <summary>
    /// Initializes a new instance of the <see cref="AutoFunctionInvocationContext"/> class from an existing <see cref="Microsoft.Extensions.AI.FunctionInvocationContext"/>.
    /// </summary>
    internal AutoFunctionInvocationContext(KernelChatOptions autoInvocationChatOptions, AIFunction aiFunction)
    {
        Verify.NotNull(autoInvocationChatOptions);
        Verify.NotNull(aiFunction);
        if (aiFunction is not KernelFunction kernelFunction)
        {
            throw new InvalidOperationException($"The function must be of type {nameof(KernelFunction)}.");
        }
        Verify.NotNull(autoInvocationChatOptions.Kernel);
        Verify.NotNull(autoInvocationChatOptions.ChatMessageContent);

        this.Options = autoInvocationChatOptions;
        this.ExecutionSettings = autoInvocationChatOptions.ExecutionSettings;
        this.AIFunction = aiFunction;
        this.Result = new FunctionResult(kernelFunction) { Culture = autoInvocationChatOptions.Kernel.Culture };
    }
#endif

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

#if !UNITY
        this.Options = new KernelChatOptions(kernel)
        {
            ChatMessageContent = chatMessageContent,
        };

        this._chatHistory = chatHistory;
        this.Messages = chatHistory.ToChatMessageList();
        chatHistory.SetChatMessageHandlers(this.Messages);
        base.Function = function;
#else
        this._chatHistory = chatHistory;
        this._function = function;
        this._kernel = kernel;
        this._chatMessageContent = chatMessageContent;
#endif
        this.Result = result;
    }

#if UNITY
    private readonly KernelFunction _function;
    private readonly Kernel _kernel;
    private readonly ChatMessageContent _chatMessageContent;

    /// <summary>
    /// Gets or sets the number of functions being invoked.
    /// </summary>
    public int FunctionCount { get; init; }

    /// <summary>
    /// Gets or sets a value indicating whether the operation is streaming.
    /// </summary>
    public bool IsStreaming { get; init; }

    /// <summary>
    /// Gets or sets a value indicating whether the function invocation should terminate.
    /// </summary>
    public bool Terminate { get; set; }
#endif

    /// <summary>
    /// The <see cref="System.Threading.CancellationToken"/> to monitor for cancellation requests.
    /// The default is <see cref="CancellationToken.None"/>.
    /// </summary>
    public CancellationToken CancellationToken { get; init; }

#if !UNITY
    /// <summary>
    /// Gets the <see cref="KernelArguments"/> specialized version of <see cref="AIFunctionArguments"/> associated with the operation.
    /// </summary>
    /// <remarks>
    /// Due to a clash with the <see cref="Microsoft.Extensions.AI.FunctionInvocationContext.Arguments"/> as a <see cref="AIFunctionArguments"/> type, this property hides
    /// it to not break existing code that relies on the <see cref="AutoFunctionInvocationContext.Arguments"/> as a <see cref="KernelArguments"/> type.
    /// </remarks>
    /// <exception cref="InvalidOperationException">Attempting to access the property when the arguments is not a <see cref="KernelArguments"/> class.</exception>
    public new KernelArguments? Arguments
    {
        get
        {
            if (base.Arguments is KernelArguments kernelArguments)
            {
                return kernelArguments;
            }

            throw new InvalidOperationException($"The arguments provided in the initialization must be of type {nameof(KernelArguments)}.");
        }
        init => base.Arguments = value ?? [];
    }

    /// <summary>
    /// Request sequence index of automatic function invocation process. Starts from 0.
    /// </summary>
    public int RequestSequenceIndex
    {
        get => this.Iteration;
        init => this.Iteration = value;
    }

    /// <summary>
    /// Function sequence index. Starts from 0.
    /// </summary>
    public int FunctionSequenceIndex
    {
        get => this.FunctionCallIndex;
        init => this.FunctionCallIndex = value;
    }

    /// <summary>
    /// The ID of the tool call.
    /// </summary>
    public string? ToolCallId
    {
        get => this.CallContent.CallId;
        init
        {
            this.CallContent = new Microsoft.Extensions.AI.FunctionCallContent(
                callId: value ?? string.Empty,
                name: this.CallContent.Name,
                arguments: this.CallContent.Arguments);
        }
    }

    /// <summary>
    /// The chat message content associated with automatic function invocation.
    /// </summary>
    public ChatMessageContent ChatMessageContent => (this.Options as KernelChatOptions)!.ChatMessageContent!;

    /// <summary>
    /// The execution settings associated with the operation.
    /// </summary>
    public PromptExecutionSettings? ExecutionSettings
    {
        get => ((KernelChatOptions)this.Options!).ExecutionSettings;
        init
        {
            this.Options ??= new KernelChatOptions(this.Kernel);
            ((KernelChatOptions)this.Options!).ExecutionSettings = value;
        }
    }

    /// <summary>
    /// Gets the <see cref="Microsoft.SemanticKernel.ChatCompletion.ChatHistory"/> associated with automatic function invocation.
    /// </summary>
    public ChatHistory ChatHistory => this._chatHistory ??= new ChatMessageHistory(this.Messages);

    /// <summary>
    /// Gets the <see cref="KernelFunction"/> with which this filter is associated.
    /// </summary>
    /// <para>
    /// Due to a clash with the <see cref="Microsoft.Extensions.AI.FunctionInvocationContext.Function"/> as a <see cref="AIFunction"/> type, this property hides
    /// it to not break existing code that relies on the <see cref="AutoFunctionInvocationContext.Function"/> as a <see cref="KernelFunction"/> type.
    /// </para>
    public new KernelFunction Function
    {
        get
        {
            if (this.AIFunction is KernelFunction kf)
            {
                return kf;
            }

            throw new InvalidOperationException($"The function provided in the initialization must be of type {nameof(KernelFunction)}.");
        }
    }

    /// <summary>
    /// Gets the <see cref="Microsoft.SemanticKernel.Kernel"/> containing services, plugins, and other state for use throughout the operation.
    /// </summary>
    public Kernel Kernel => ((KernelChatOptions)this.Options!).Kernel!;
#else
    /// <summary>
    /// Gets the <see cref="KernelArguments"/> associated with the operation.
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
    public ChatMessageContent ChatMessageContent => this._chatMessageContent;

    /// <summary>
    /// The execution settings associated with the operation.
    /// </summary>
    public PromptExecutionSettings? ExecutionSettings { get; init; }

    /// <summary>
    /// Gets the <see cref="Microsoft.SemanticKernel.ChatCompletion.ChatHistory"/> associated with automatic function invocation.
    /// </summary>
    public ChatHistory ChatHistory => this._chatHistory!;

    /// <summary>
    /// Gets the <see cref="KernelFunction"/> with which this filter is associated.
    /// </summary>
    public KernelFunction Function => this._function;

    /// <summary>
    /// Gets the <see cref="Microsoft.SemanticKernel.Kernel"/> containing services, plugins, and other state for use throughout the operation.
    /// </summary>
    public Kernel Kernel => this._kernel;
#endif

    /// <summary>
    /// Gets or sets the result of the function's invocation.
    /// </summary>
    public FunctionResult Result { get; set; }

#if !UNITY
    /// <summary>
    /// Gets or sets the <see cref="Microsoft.Extensions.AI.AIFunction"/> with which this filter is associated.
    /// </summary>
    internal AIFunction AIFunction
    {
        get => base.Function;
        set => base.Function = value;
    }

    private static bool IsSameSchema(KernelFunction kernelFunction, AIFunction aiFunction)
    {
        // Compares the schemas, should be similar.
        return string.Equals(
            kernelFunction.JsonSchema.ToString(),
            aiFunction.JsonSchema.ToString(),
            StringComparison.OrdinalIgnoreCase);

        // TODO: Later can be improved by comparing the underlying methods.
        // return kernelFunction.UnderlyingMethod == aiFunction.UnderlyingMethod;
    }

    /// <summary>
    /// Mutable IEnumerable of chat message as chat history.
    /// </summary>
    private class ChatMessageHistory : ChatHistory, IEnumerable<ChatMessageContent>
    {
        private readonly List<ChatMessage> _messages;

        internal ChatMessageHistory(IEnumerable<ChatMessage> messages) : base(messages.ToChatHistory())
        {
            this._messages = new List<ChatMessage>(messages);
        }

        public override void Add(ChatMessageContent item)
        {
            base.Add(item);
            this._messages.Add(item.ToChatMessage());
        }

        public override void Clear()
        {
            base.Clear();
            this._messages.Clear();
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

        public override void RemoveRange(int index, int count)
        {
            this._messages.RemoveRange(index, count);
            base.RemoveRange(index, count);
        }

        public override void CopyTo(ChatMessageContent[] array, int arrayIndex)
        {
            for (int i = 0; i < this._messages.Count; i++)
            {
                array[arrayIndex + i] = this._messages[i].ToChatMessageContent();
            }
        }

        public override bool Contains(ChatMessageContent item) => base.Contains(item);

        public override int IndexOf(ChatMessageContent item) => base.IndexOf(item);

        public override void AddRange(IEnumerable<ChatMessageContent> items)
        {
            base.AddRange(items);
            this._messages.AddRange(items.Select(i => i.ToChatMessage()));
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

    /// <summary>Destructor to clear the chat history overrides.</summary>
    ~AutoFunctionInvocationContext()
    {
        // The moment this class is destroyed, we need to clear the update message overrides
        this._chatHistory?.ClearOverrides();
    }
#endif
}
