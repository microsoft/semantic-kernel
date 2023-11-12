// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Fluent builder for initializing an <see cref="IAssistant"/> instance.
/// </summary>
public interface IAssistantBuilder
{
    /// <summary>
    /// Define the assistant model (required).
    /// </summary>
    /// <param name="model"></param>
    /// <returns><see cref="IAssistantBuilder"/> instance for fluid expression.</returns>
    IAssistantBuilder WithModel(string model);

    /// <summary>
    /// Define the assistant name (optional).
    /// </summary>
    /// <returns><see cref="IAssistantBuilder"/> instance for fluid expression.</returns>
    IAssistantBuilder WithName(string? name);

    /// <summary>
    /// Define the assistant description (optional).
    /// </summary>
    /// <returns><see cref="IAssistantBuilder"/> instance for fluid expression.</returns>
    IAssistantBuilder WithDescription(string? description);

    /// <summary>
    /// Define the assistant instructions (required).
    /// </summary>
    /// <param name="instructions"></param>
    /// <returns><see cref="IAssistantBuilder"/> instance for fluid expression.</returns>
    IAssistantBuilder WithInstructions(string instructions);

    /// <summary>
    /// Create a <see cref="IAssistant"/> instance.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A new <see cref="IAssistant"/> instance.</returns>
    Task<IAssistant> BuildAsync(CancellationToken cancellationToken = default);
}
