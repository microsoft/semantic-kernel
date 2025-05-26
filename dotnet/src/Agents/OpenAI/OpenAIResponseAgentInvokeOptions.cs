// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Optional parameters for <see cref="OpenAIAssistantAgent"/> invocation.
/// </summary>
public sealed class OpenAIResponseAgentInvokeOptions : AgentInvokeOptions
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIResponseAgentInvokeOptions"/> class.
    /// </summary>
    public OpenAIResponseAgentInvokeOptions()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIResponseAgentInvokeOptions"/> class by cloning the provided options.
    /// </summary>
    /// <param name="options">The options to clone.</param>
    public OpenAIResponseAgentInvokeOptions(AgentInvokeOptions options)
        : base(options)
    {
        Verify.NotNull(options);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIResponseAgentInvokeOptions"/> class by cloning the provided options.
    /// </summary>
    /// <param name="options">The options to clone.</param>
    public OpenAIResponseAgentInvokeOptions(OpenAIResponseAgentInvokeOptions options)
        : base(options)
    {
        Verify.NotNull(options);
    }
}
