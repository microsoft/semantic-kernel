// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using A2A;

namespace Microsoft.SemanticKernel.Agents.A2A;

/// <summary>
/// Represents a conversation thread for an A2A agent.
/// </summary>
public sealed class A2AAgentThread : AgentThread
{
    /// <summary>
    /// Initializes a new instance of the <see cref="A2AAgentThread"/> class that resumes an existing thread.
    /// </summary>
    /// <param name="client">The agents client to use for interacting with threads.</param>
    /// <param name="id">The ID of an existing thread to resume.</param>
    public A2AAgentThread(A2AClient client, string? id = null)
    {
        Verify.NotNull(client);

        this._client = client;
        this.Id = id ?? Guid.NewGuid().ToString("N");
    }

    /// <inheritdoc />
    protected override Task<string?> CreateInternalAsync(CancellationToken cancellationToken)
    {
        return Task.FromResult<string?>(Guid.NewGuid().ToString("N"));
    }

    /// <inheritdoc />
    protected override Task DeleteInternalAsync(CancellationToken cancellationToken)
    {
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    protected override Task OnNewMessageInternalAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        return Task.CompletedTask;
    }

    #region private
    private readonly A2AClient _client;
    #endregion
}
