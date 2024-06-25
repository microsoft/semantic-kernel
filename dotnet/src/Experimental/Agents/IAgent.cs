// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents.Models;

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
    /// Identifies additional agent capabilities.
    /// </summary>
    AgentCapability Capabilities { get; }

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
    /// Identifiers of files associated with agent.
    /// </summary>
    IEnumerable<string> FileIds { get; }

    /// <summary>
    /// Tools defined for run execution.
    /// </summary>
    KernelPluginCollection Plugins { get; }

    /// <summary>
    /// A semantic-kernel <see cref="Kernel"/> instance associated with the agent.
    /// </summary>
    internal Kernel Kernel { get; }

    /// <summary>
    /// Internal tools model.
    /// </summary>
    internal IEnumerable<ToolModel> Tools { get; }

    /// <summary>
    /// Expose the agent as a plugin.
    /// </summary>
    AgentPlugin AsPlugin();

    /// <summary>
    /// Expose the agent internally as a prompt-template
    /// </summary>
    internal IPromptTemplate AsPromptTemplate();

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
    /// Associate uploaded file with the agent, by identifier.
    /// </summary>
    /// <param name="fileId">The identifier of the uploaded file.</param>
    /// <param name="cancellationToken">A cancellation token</param>
    Task AddFileAsync(string fileId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Remove association of uploaded file with the agent, by identifier.
    /// </summary>
    /// <param name="fileId">The identifier of the uploaded file.</param>
    /// <param name="cancellationToken">A cancellation token</param>
    Task RemoveFileAsync(string fileId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete current agent.  Terminal state - Unable to perform any
    /// subsequent actions.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token</param>
    Task DeleteAsync(CancellationToken cancellationToken = default);
}
