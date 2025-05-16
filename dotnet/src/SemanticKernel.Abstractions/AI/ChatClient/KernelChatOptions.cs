// Copyright (c) Microsoft. All rights reserved.

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
    internal KernelChatOptions(Kernel kernel, ChatOptions? options = null, PromptExecutionSettings? settings = null)
    {
        Verify.NotNull(kernel);

        if (options is not null)
        {
            this.AdditionalProperties = options.AdditionalProperties;
            this.AllowMultipleToolCalls = options.AllowMultipleToolCalls;
            this.Tools = options.Tools;
            this.Temperature = options.Temperature;
            this.TopP = options.TopP;
            this.TopK = options.TopK;
            this.Seed = options.Seed;
            this.ResponseFormat = options.ResponseFormat;
            this.MaxOutputTokens = options.MaxOutputTokens;
            this.FrequencyPenalty = options.FrequencyPenalty;
            this.PresencePenalty = options.PresencePenalty;
            this.StopSequences = options.StopSequences;
            this.RawRepresentationFactory = options.RawRepresentationFactory;
            this.ConversationId = options.ConversationId;
            this.Seed = options.Seed;
            this.ToolMode = options.ToolMode;
            this.ModelId = options.ModelId;
        }

        this.ExecutionSettings = settings;
        this.Kernel = kernel;
    }

    [JsonIgnore]
    public ChatMessageContent? ChatMessageContent { get; internal set; }

    [JsonIgnore]
    public Kernel Kernel { get; }

    [JsonIgnore]
    public PromptExecutionSettings? ExecutionSettings { get; internal set; }
}
