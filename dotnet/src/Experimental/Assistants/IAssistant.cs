// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Represents an assistant that can call the model and use tools.
/// </summary>
public interface IAssistant
{
    /// <summary>
    /// The assistant identifier (which can be referenced in API endpoints).
    /// </summary>
    string Id { get; }

    /// <summary>
    /// Always "assistant"
    /// </summary>
#pragma warning disable CA1720 // Identifier contains type name - We don't control the schema
#pragma warning disable CA1716 // Identifiers should not match keywords
    string Object { get; }
#pragma warning restore CA1716 // Identifiers should not match keywords
#pragma warning restore CA1720 // Identifier contains type name

    /// <summary>
    /// Unix timestamp (in seconds) for when the assistant was created
    /// </summary>
    long CreatedAt { get; }

    /// <summary>
    /// Name of the assistant
    /// </summary>
    string? Name { get; }

    /// <summary>
    /// The description of the assistant
    /// </summary>
    string? Description { get; }

    /// <summary>
    /// ID of the model to use
    /// </summary>
    string Model { get; }

    /// <summary>
    /// The system instructions that the assistant uses
    /// </summary>
    string Instructions { get; }

    /// <summary>
    /// A semantic-kernel <see cref="IKernel"/> instance associated with the assistant.
    /// </summary>
    internal IKernel Kernel { get; }

    /// <summary>
    /// Tools defined for run execution.
    /// </summary>
    internal IList<ISKFunction> Functions { get; }

    /// <summary>
    /// Creates a new assistant chat thread.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token</param>
    Task<IChatThread> NewThreadAsync(CancellationToken cancellationToken = default);
}
