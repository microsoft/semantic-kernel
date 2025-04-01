// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Optional parameters for <see cref="AzureAIAgent"/> invocation.
/// </summary>
public sealed class AzureAIAgentInvokeOptions : AgentInvokeOptions
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAIAgentInvokeOptions"/> class.
    /// </summary>
    public AzureAIAgentInvokeOptions()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAIAgentInvokeOptions"/> class by cloning the provided options.
    /// </summary>
    /// <param name="options">The options to clone.</param>
    public AzureAIAgentInvokeOptions(AgentInvokeOptions options)
        : base(options)
    {
        Verify.NotNull(options);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAIAgentInvokeOptions"/> class by cloning the provided options.
    /// </summary>
    /// <param name="options">The options to clone.</param>
    public AzureAIAgentInvokeOptions(AzureAIAgentInvokeOptions options)
        : base(options)
    {
        Verify.NotNull(options);

        this.ModelName = options.ModelName;
        this.OverrideInstructions = options.OverrideInstructions;
        this.AdditionalMessages = options.AdditionalMessages;
        this.EnableCodeInterpreter = options.EnableCodeInterpreter;
        this.EnableFileSearch = options.EnableFileSearch;
        this.EnableJsonResponse = options.EnableJsonResponse;
        this.MaxCompletionTokens = options.MaxCompletionTokens;
        this.MaxPromptTokens = options.MaxPromptTokens;
        this.ParallelToolCallsEnabled = options.ParallelToolCallsEnabled;
        this.TruncationMessageCount = options.TruncationMessageCount;
        this.Temperature = options.Temperature;
        this.TopP = options.TopP;
        this.Metadata = options.Metadata;
    }

    /// <summary>
    /// Gets or sets the AI model targeted by the agent.
    /// </summary>
    public string? ModelName { get; init; }

    /// <summary>
    /// Gets or sets the override instructions.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? OverrideInstructions { get; init; }

    /// <summary>
    /// Gets or sets the additional messages to add to the thread.
    /// </summary>
    /// <remarks>
    /// Only supports messages with <see href="https://platform.openai.com/docs/api-reference/runs/createRun#runs-createrun-additional_messages">role = User or Assistant</see>.
    /// </remarks>
    public IReadOnlyList<ChatMessageContent>? AdditionalMessages { get; init; }

    /// <summary>
    /// Gets or sets a value that indicates whether the code_interpreter tool is enabled.
    /// </summary>
    public bool EnableCodeInterpreter { get; init; }

    /// <summary>
    /// Gets or sets a value that indicates whether the file_search tool is enabled.
    /// </summary>
    public bool EnableFileSearch { get; init; }

    /// <summary>
    /// Gets or sets a value that indicates whether the JSON response format is enabled.
    /// </summary>
    public bool? EnableJsonResponse { get; init; }

    /// <summary>
    /// Gets or sets the maximum number of completion tokens that can be used over the course of the run.
    /// </summary>
    public int? MaxCompletionTokens { get; init; }

    /// <summary>
    /// Gets or sets the maximum number of prompt tokens that can be used over the course of the run.
    /// </summary>
    public int? MaxPromptTokens { get; init; }

    /// <summary>
    /// Gets or sets a value that indicates whether the parallel function calling is enabled during tool use.
    /// </summary>
    /// <value>
    /// <see langword="true"/> if parallel function calling is enabled during tool use; otherwise, <see langword="false"/>. The default is <see langword="true"/>.
    /// </value>
    public bool? ParallelToolCallsEnabled { get; init; }

    /// <summary>
    /// Gets or sets the number of recent messages that the thread will be truncated to.
    /// </summary>
    public int? TruncationMessageCount { get; init; }

    /// <summary>
    /// Gets or sets the sampling temperature to use, between 0 and 2.
    /// </summary>
    public float? Temperature { get; init; }

    /// <summary>
    /// Gets or sets the probability mass of tokens whose results are considered in nucleus sampling.
    /// </summary>
    /// <remarks>
    /// It's recommended to set this property or <see cref="Temperature"/>, but not both.
    ///
    /// Nucleus sampling is an alternative to sampling with temperature where the model
    /// considers the results of the tokens with <see cref="TopP"/> probability mass.
    /// For example, 0.1 means only the tokens comprising the top 10% probability mass are considered.
    /// </remarks>
    public float? TopP { get; init; }

    /// <summary>
    /// Gets or sets a set of up to 16 key/value pairs that can be attached to an agent, used for
    /// storing additional information about that object in a structured format.
    /// </summary>
    /// <remarks>
    /// Keys can be up to 64 characters in length, and values can be up to 512 characters in length.
    /// </remarks>
    public IReadOnlyDictionary<string, string>? Metadata { get; init; }

    /// <summary>
    /// Converts the current options to an <see cref="AzureAIInvocationOptions"/> instance.
    /// </summary>
    /// <returns>The converted <see cref="AzureAIInvocationOptions"/> instance.</returns>
    internal AzureAIInvocationOptions ToAzureAIInvocationOptions()
    {
        return new AzureAIInvocationOptions
        {
            ModelName = this.ModelName,
            OverrideInstructions = this.OverrideInstructions,
            AdditionalInstructions = this.AdditionalInstructions,
            AdditionalMessages = this.AdditionalMessages,
            EnableCodeInterpreter = this.EnableCodeInterpreter,
            EnableFileSearch = this.EnableFileSearch,
            EnableJsonResponse = this.EnableJsonResponse,
            MaxCompletionTokens = this.MaxCompletionTokens,
            MaxPromptTokens = this.MaxPromptTokens,
            ParallelToolCallsEnabled = this.ParallelToolCallsEnabled,
            TruncationMessageCount = this.TruncationMessageCount,
            Temperature = this.Temperature,
            TopP = this.TopP,
            Metadata = this.Metadata
        };
    }
}
