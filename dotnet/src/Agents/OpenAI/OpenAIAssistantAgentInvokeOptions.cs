// Copyright (c) Microsoft. All rights reserved.

using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Optional parameters for <see cref="OpenAIAssistantAgent"/> invocation.
/// </summary>
public sealed class OpenAIAssistantAgentInvokeOptions : AgentInvokeOptions
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgentInvokeOptions"/> class.
    /// </summary>
    public OpenAIAssistantAgentInvokeOptions()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgentInvokeOptions"/> class by cloning the provided options.
    /// </summary>
    /// <param name="options">The options to clone.</param>
    public OpenAIAssistantAgentInvokeOptions(AgentInvokeOptions options)
        : base(options)
    {
        Verify.NotNull(options);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgentInvokeOptions"/> class by cloning the provided options.
    /// </summary>
    /// <param name="options">The options to clone.</param>
    public OpenAIAssistantAgentInvokeOptions(OpenAIAssistantAgentInvokeOptions options)
        : base(options)
    {
        Verify.NotNull(options);

        this.RunCreationOptions = options.RunCreationOptions;
    }

    /// <summary>
    /// Gets or sets the <see cref="RunCreationOptions"/> to use when creating the new run to execute the invocation.
    /// </summary>
    /// <remarks>
    /// If this property is set, then <see cref="AgentInvokeOptions.AdditionalInstructions"/> will not be used.
    /// Instead, please set the <see cref="RunCreationOptions.AdditionalInstructions"/> property to provide the
    /// additional instructions for the run.
    /// </remarks>
    public RunCreationOptions? RunCreationOptions { get; init; } = null;
}
