// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Optional parameters for agent invocation.
/// </summary>
public class AgentCreationOptions
{
    /// <summary>
    /// Gets or sets the <see cref="IPromptTemplateFactory"/>, a factory for prompt templates for one or more prompt template formats.
    /// </summary>
    public IPromptTemplateFactory? PromptTemplateFactory { get; init; } = null;

    /// <summary>
    /// Gets or sets the <see cref="IConfiguration"/>, a set of key/value agent configuration properties.
    /// </summary>
    public IConfiguration? Configuration { get; init; } = null;
}
