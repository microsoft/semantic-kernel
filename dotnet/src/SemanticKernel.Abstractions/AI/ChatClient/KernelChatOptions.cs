// Copyright (c) Microsoft. All rights reserved.

#if !UNITY
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel;

namespace Microsoft.Extensions.AI;

/// <summary>
/// This class allows a <see cref="Kernel"/>, <see cref="PromptExecutionSettings"/> and a <see cref="ChatMessageContent"/> to be used
/// for internal <see cref="AutoFunctionInvocationContext"/> creation. This avoids any leaking information in the lower-level ChatOptions
/// during serialization of <see cref="ChatOptions"/> in <see cref="IChatClient"/> calls to AI Models.
/// </summary>
internal class KernelChatOptions : ChatOptions
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelChatOptions"/> class.
    /// </summary>
    /// <param name="kernel">Target kernel.</param>
    /// <param name="options">Original chat options.</param>
    /// <param name="settings">Prompt execution settings.</param>
    internal KernelChatOptions(Kernel kernel, ChatOptions? options = null, PromptExecutionSettings? settings = null) :
        base(options)
    {
        Verify.NotNull(kernel);

        this.ExecutionSettings = settings;
        this.Kernel = kernel;
    }

    [JsonIgnore]
    public ChatMessageContent? ChatMessageContent { get; internal set; }

    [JsonIgnore]
    public Kernel Kernel { get; }

    [JsonIgnore]
    public PromptExecutionSettings? ExecutionSettings { get; internal set; }

    public override ChatOptions Clone() => new KernelChatOptions(this.Kernel, this, this.ExecutionSettings)
    {
        ChatMessageContent = this.ChatMessageContent
    };
}
#endif
