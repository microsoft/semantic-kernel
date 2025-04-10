// Copyright (c) Microsoft. All rights reserved.
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Optional parameters for agent creation used when create an <see cref="Agent"/>
/// using an instance of <see cref="AgentFactory"/>.
/// <remarks>
/// Implementors of <see cref="AgentFactory"/> can extend this class to provide
/// agent specific creation options.
/// </remarks>
/// </summary>
[Experimental("SKEXP0110")]
public class AgentCreationOptions
{
    /// <summary>
    /// Gets or sets the <see cref="Kernel"/>, a kernel instance to resolve services.
    /// </summary>
    public Kernel? Kernel { get; init; } = null;

    /// <summary>
    /// Gets or sets the <see cref="IPromptTemplateFactory"/>, a factory for prompt templates for one or more prompt template formats.
    /// </summary>
    public IPromptTemplateFactory? PromptTemplateFactory { get; init; } = null;
}
