// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Fluent builder for initializing an <see cref="IAssistant"/> instance.
/// </summary>
public interface IAssistantBuilder
{
    /// <summary>
    /// Assigns a semantic-kernel to the assistant (for function calling).
    /// </summary>
    /// <param name="kernel">The semantic-kernel associated with the assistant.</param>
    /// <returns><see cref="IAssistantBuilder"/> instance for fluid expression.</returns>
    IAssistantBuilder WithKernel(IKernel kernel);

    /// <summary>
    /// Define the chat model assocaited with the assistant (required).
    /// </summary>
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
    /// <param name="instructions">The assistant instructions (system prompt)</param>
    /// <returns><see cref="IAssistantBuilder"/> instance for fluid expression.</returns>
    IAssistantBuilder WithInstructions(string instructions);

    /// <summary>
    /// Adds an assistant tool.
    /// </summary>
    /// <param name="tool">A SK function view</param>
    /// <returns><see cref="IAssistantBuilder"/> instance for fluid expression.</returns>
    IAssistantBuilder WithTool(FunctionView tool);

    /// <summary>
    /// Adds assistant tools.
    /// </summary>
    /// <param name="tools">A list of SK function views</param>
    /// <returns><see cref="IAssistantBuilder"/> instance for fluid expression.</returns>
    IAssistantBuilder WithTools(IEnumerable<FunctionView> tools);

    /// <summary>
    /// Adds all the functions in the associated kernel as the assistant tools.
    /// </summary>
    /// <returns><see cref="IAssistantBuilder"/> instance for fluid expression.</returns>
    IAssistantBuilder WithTools();

    /// <summary>
    /// Stores metadata whose keys can be a maximum of 64 characters long and values can be a maxium of 512 characters long.
    /// </summary>
    /// <param name="key">The metadata key</param>
    /// <param name="value">The metadata value</param>
    /// <returns><see cref="IAssistantBuilder"/> instance for fluid expression.</returns>
    IAssistantBuilder WithMetadata(string key, object value);

    /// <summary>
    /// Stores metadata whose keys can be a maximum of 64 characters long and values can be a maxium of 512 characters long.
    /// </summary>
    /// <param name="metadata">A set of metadata</param>
    /// <returns><see cref="IAssistantBuilder"/> instance for fluid expression.</returns>
    IAssistantBuilder WithMetadata(IDictionary<string, object> metadata);

    /// <summary>
    /// Create a <see cref="IAssistant"/> instance.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>A new <see cref="IAssistant"/> instance.</returns>
    Task<IAssistant> BuildAsync(CancellationToken cancellationToken = default);
}
