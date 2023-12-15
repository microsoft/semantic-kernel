// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Represents an agent that can call the model and use tools.
/// </summary>
public interface IAgent
{
    /// <summary>
    /// The agent identifier (which can be referenced in API endpoints).
    /// </summary>
    string Id { get; }

    /// <summary>
    /// Always "agent"
    /// </summary>
#pragma warning disable CA1720 // Identifier contains type name - We don't control the schema
#pragma warning disable CA1716 // Identifiers should not match keywords
    string Object { get; }
#pragma warning restore CA1716 // Identifiers should not match keywords
#pragma warning restore CA1720 // Identifier contains type name

    /// <summary>
    /// Unix timestamp (in seconds) for when the agent was created
    /// </summary>
    long CreatedAt { get; }

    /// <summary>
    /// Name of the agent
    /// </summary>
    string? Name { get; }

    /// <summary>
    /// The description of the agent
    /// </summary>
    string? Description { get; }

    /// <summary>
    /// ID of the model to use
    /// </summary>
    string Model { get; }

    /// <summary>
    /// The system instructions that the agent uses
    /// </summary>
    string Instructions { get; }

    /// <summary>
    /// A semantic-kernel <see cref="Kernel"/> instance associated with the agent.
    /// </summary>
    internal Kernel Kernel { get; }

    /// <summary>
    /// Tools defined for run execution.
    /// </summary>
    public KernelPluginCollection Plugins { get; }

    /// <summary>
    /// Expose the agent as a plugin.
    /// </summary>
    public AgentPlugin AsPlugin();

    /// <summary>
    /// Creates a new agent chat thread.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token</param>
    Task<IAgentThread> NewThreadAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets an existing agent chat thread.
    /// </summary>
    /// <param name="id">The id of the existing chat thread.</param>
    /// <param name="cancellationToken">A cancellation token</param>
    Task<IAgentThread> GetThreadAsync(string id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes an existing agent chat thread.
    /// </summary>
    /// <param name="id">The id of the existing chat thread.  Allows for null-fallthrough to simplify caller patterns.</param>
    /// <param name="cancellationToken">A cancellation token</param>
    Task DeleteThreadAsync(string? id, CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete current agent.  Terminal state - Unable to perform any
    /// subsequent actions.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token</param>
    Task DeleteAsync(CancellationToken cancellationToken = default);
}
