// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Runtime;

/// <summary>
/// A proxy that allows you to use an <see cref="AgentId"/> in place of its associated <see cref="IAgent"/>.
/// </summary>
public class AgentProxy
{
    /// <summary>
    /// The runtime instance used to interact with agents.
    /// </summary>
    private readonly IAgentRuntime _runtime;
    private AgentMetadata? _metadata;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentProxy"/> class.
    /// </summary>
    public AgentProxy(AgentId agentId, IAgentRuntime runtime)
    {
        this.Id = agentId;
        this._runtime = runtime;
    }

    /// <summary>
    /// The target agent for this proxy.
    /// </summary>
    public AgentId Id { get; }

    /// <summary>
    /// Gets the metadata of the agent.
    /// </summary>
    /// <value>
    /// An instance of <see cref="AgentMetadata"/> containing details about the agent.
    /// </value>
    public AgentMetadata Metadata => this._metadata ??= this.QueryMetadataAndUnwrap();

    /// <summary>
    /// Sends a message to the agent and processes the response.
    /// </summary>
    /// <param name="message">The message to send to the agent.</param>
    /// <param name="sender">The agent that is sending the message.</param>
    /// <param name="messageId">
    /// The message ID. If <c>null</c>, a new message ID will be generated.
    /// This message ID must be unique and is recommended to be a UUID.
    /// </param>
    /// <param name="cancellationToken">
    /// A token used to cancel an in-progress operation. Defaults to <c>null</c>.
    /// </param>
    /// <returns>A task representing the asynchronous operation, returning the response from the agent.</returns>
    public ValueTask<object?> SendMessageAsync(object message, AgentId sender, string? messageId = null, CancellationToken cancellationToken = default)
    {
        return this._runtime.SendMessageAsync(message, this.Id, sender, messageId, cancellationToken);
    }

    /// <summary>
    /// Loads the state of the agent from a previously saved state.
    /// </summary>
    /// <param name="state">A dictionary representing the state of the agent. Must be JSON serializable.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    public ValueTask LoadStateAsync(JsonElement state)
    {
        return this._runtime.LoadAgentStateAsync(this.Id, state);
    }

    /// <summary>
    /// Saves the state of the agent. The result must be JSON serializable.
    /// </summary>
    /// <returns>A task representing the asynchronous operation, returning a dictionary containing the saved state.</returns>
    public ValueTask<JsonElement> SaveStateAsync()
    {
        return this._runtime.SaveAgentStateAsync(this.Id);
    }

    private AgentMetadata QueryMetadataAndUnwrap()
    {
#pragma warning disable VSTHRD002 // Avoid problematic synchronous waits
        return this._runtime.GetAgentMetadataAsync(this.Id).AsTask().ConfigureAwait(false).GetAwaiter().GetResult();
#pragma warning restore VSTHRD002 // Avoid problematic synchronous waits
    }
}
