// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class with data related to automatic function invocation.
/// </summary>
public class AutoFunctionInvocationContext
{
    private ChatHistory? _chatHistory;
    private KernelFunction? _kernelFunction;
    private readonly Microsoft.Extensions.AI.FunctionInvocationContext _invocationContext = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="AutoFunctionInvocationContext"/> class from an existing <see cref="Microsoft.Extensions.AI.FunctionInvocationContext"/>.
    /// </summary>
    internal AutoFunctionInvocationContext(Microsoft.Extensions.AI.FunctionInvocationContext invocationContext)
    {
        Verify.NotNull(invocationContext);
        Verify.NotNull(invocationContext.Options);

        // the ChatOptions must be provided with AdditionalProperties.
        Verify.NotNull(invocationContext.Options.AdditionalProperties);

        invocationContext.Options.AdditionalProperties.TryGetValue<Kernel>(ChatOptionsExtensions.KernelKey, out var kernel);
        Verify.NotNull(kernel);

        invocationContext.Options.AdditionalProperties.TryGetValue<ChatMessageContent>(ChatOptionsExtensions.ChatMessageContentKey, out var chatMessageContent);
        Verify.NotNull(chatMessageContent);

        invocationContext.Options.AdditionalProperties.TryGetValue<PromptExecutionSettings>(ChatOptionsExtensions.PromptExecutionSettingsKey, out var executionSettings);
        this.ExecutionSettings = executionSettings;
        this._invocationContext = invocationContext;

        this.Result = new FunctionResult(this.Function) { Culture = kernel.Culture };
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

        this._invocationContext.Options = new()
        {
            AdditionalProperties = new()
            {
                [ChatOptionsExtensions.ChatMessageContentKey] = chatMessageContent,
                [ChatOptionsExtensions.KernelKey] = kernel
            }
        };

        this._kernelFunction = function;
        this._chatHistory = chatHistory;
        this._invocationContext.Messages = chatHistory.ToChatMessageList();
        chatHistory.SetChatMessageHandlers(this._invocationContext.Messages);
        this._invocationContext.Function = function;
        this.Result = result;
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
    public KernelArguments? Arguments
    {
        get => this._invocationContext.CallContent.Arguments is KernelArguments kernelArguments ? kernelArguments : null;
        init => this._invocationContext.CallContent.Arguments = value;
    }

    /// <summary>
    /// Request sequence index of automatic function invocation process. Starts from 0.
    /// </summary>
    public int RequestSequenceIndex
    {
        get => this._invocationContext.Iteration;
        init => this._invocationContext.Iteration = value;
    }

    /// <summary>
    /// Function sequence index. Starts from 0.
    /// </summary>
    public int FunctionSequenceIndex
    {
        get => this._invocationContext.FunctionCallIndex;
        init => this._invocationContext.FunctionCallIndex = value;
    }

    /// <summary>Gets or sets the total number of function call requests within the iteration.</summary>
    /// <remarks>
    /// The response from the underlying client might include multiple function call requests.
    /// This count indicates how many there were.
    /// </remarks>
    public int FunctionCount
    {
        get => this._invocationContext.FunctionCount;
        init => this._invocationContext.FunctionCount = value;
    }

    /// <summary>
    /// The ID of the tool call.
    /// </summary>
    public string? ToolCallId
    {
        get => this._invocationContext.CallContent.CallId;
        init
        {
            this._invocationContext.CallContent = new Microsoft.Extensions.AI.FunctionCallContent(
                callId: value ?? string.Empty,
                name: this._invocationContext.CallContent.Name,
                arguments: this._invocationContext.CallContent.Arguments);
        }
    }

    /// <summary>
    /// The chat message content associated with automatic function invocation.
    /// </summary>
    public ChatMessageContent ChatMessageContent
        => (this._invocationContext.Options?.AdditionalProperties?[ChatOptionsExtensions.ChatMessageContentKey] as ChatMessageContent)!;

    /// <summary>
    /// The execution settings associated with the operation.
    /// </summary>
    public PromptExecutionSettings? ExecutionSettings
    {
        get => this._invocationContext.Options?.AdditionalProperties?[ChatOptionsExtensions.PromptExecutionSettingsKey] as PromptExecutionSettings;
        init
        {
            this._invocationContext.Options ??= new();
            this._invocationContext.Options.AdditionalProperties ??= [];
            this._invocationContext.Options.AdditionalProperties[ChatOptionsExtensions.PromptExecutionSettingsKey] = value;
        }
    }

    /// <summary>
    /// Gets the <see cref="Microsoft.SemanticKernel.ChatCompletion.ChatHistory"/> associated with automatic function invocation.
    /// </summary>
    public ChatHistory ChatHistory => this._chatHistory ??= new ChatMessageHistory(this._invocationContext.Messages);

    /// <summary>
    /// Gets the <see cref="KernelFunction"/> with which this filter is associated.
    /// </summary>
    public KernelFunction Function
    {
        get
        {
            if (this._kernelFunction is null
                // If the schemas are different,
                // AIFunction reference potentially was modified and the kernel function should be regenerated.
                || !IsSameSchema(this._kernelFunction, this._invocationContext.Function))
            {
                this._kernelFunction = this._invocationContext.Function.AsKernelFunction();
            }

            return this._kernelFunction;
        }
    }

    /// <summary>
    /// Gets the <see cref="Microsoft.SemanticKernel.Kernel"/> containing services, plugins, and other state for use throughout the operation.
    /// </summary>
    public Kernel Kernel
    {
        get
        {
            Kernel? kernel = null;
            this._invocationContext.Options?.AdditionalProperties?.TryGetValue(ChatOptionsExtensions.KernelKey, out kernel);

            // To avoid exception from properties, when attempting to retrieve a kernel from a non-ready context, it will give a null.
            return kernel!;
        }
    }

    /// <summary>
    /// Gets or sets the result of the function's invocation.
    /// </summary>
    public FunctionResult Result { get; set; }

    /// <summary>Gets or sets a value indicating whether to terminate the request.</summary>
    /// <remarks>
    /// In response to a function call request, the function might be invoked, its result added to the chat contents,
    /// and a new request issued to the wrapped client. If this property is set to <see langword="true"/>, that subsequent request
    /// will not be issued and instead the loop immediately terminated rather than continuing until there are no
    /// more function call requests in responses.
    /// </remarks>
    public bool Terminate
    {
        get => this._invocationContext.Terminate;
        set => this._invocationContext.Terminate = value;
    }

    /// <summary>Gets or sets the function call content information associated with this invocation.</summary>
    internal Microsoft.Extensions.AI.FunctionCallContent CallContent
    {
        get => this._invocationContext.CallContent;
        set => this._invocationContext.CallContent = value;
    }

    internal AIFunction AIFunction
    {
        get => this._invocationContext.Function;
        set => this._invocationContext.Function = value;
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
}
