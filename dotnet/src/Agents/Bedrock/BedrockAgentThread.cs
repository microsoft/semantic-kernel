// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockAgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Bedrock;
/// <summary>
/// Represents a conversation thread for a Bedrock agent.
/// </summary>
public sealed class BedrockAgentThread : AgentThread
{
    private readonly IAmazonBedrockAgentRuntime _runtimeClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="BedrockAgentThread"/> class.
    /// </summary>
    /// <param name="runtimeClient">A client used to interact with the Bedrock Agent runtime service.</param>
    /// <param name="sessionId">An optional session Id to continue an existing session.</param>
    /// <exception cref="ArgumentNullException"></exception>
    public BedrockAgentThread(IAmazonBedrockAgentRuntime runtimeClient, string? sessionId = null)
    {
        this._runtimeClient = runtimeClient ?? throw new ArgumentNullException(nameof(runtimeClient));
        this.Id = sessionId;
    }

    /// <summary>
    /// Creates the thread and returns the thread id.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the thread has been created.</returns>
    public new Task CreateAsync(CancellationToken cancellationToken = default)
    {
        return base.CreateAsync(cancellationToken);
    }

    /// <inheritdoc />
    protected override async Task<string?> CreateInternalAsync(CancellationToken cancellationToken)
    {
        const string ErrorMessage = "The thread could not be created due to an error response from the service.";

        try
        {
            var response = await this._runtimeClient.CreateSessionAsync(
                request: new(),
                cancellationToken: cancellationToken).ConfigureAwait(false);

            return response.SessionId;
        }
        catch (AmazonBedrockAgentRuntimeException ex)
        {
            throw new AgentThreadOperationException(ErrorMessage, ex);
        }
        catch (AggregateException ex)
        {
            throw new AgentThreadOperationException(ErrorMessage, ex);
        }
    }

    /// <inheritdoc />
    protected override async Task DeleteInternalAsync(CancellationToken cancellationToken)
    {
        const string ErrorMessage = "The thread could not be deleted due to an error response from the service.";

        try
        {
            var endSessionResponse = await this._runtimeClient.EndSessionAsync(
                request: new()
                {
                    SessionIdentifier = this.Id
                },
                cancellationToken: cancellationToken).ConfigureAwait(false);

            var deleteSessionResponse = await this._runtimeClient.DeleteSessionAsync(
                request: new()
                {
                    SessionIdentifier = this.Id
                },
                cancellationToken: cancellationToken).ConfigureAwait(false);

            this.Id = null;
        }
        catch (AmazonBedrockAgentRuntimeException ex)
        {
            throw new AgentThreadOperationException(ErrorMessage, ex);
        }
        catch (AggregateException ex)
        {
            throw new AgentThreadOperationException(ErrorMessage, ex);
        }
    }

    /// <inheritdoc />
    protected override async Task OnNewMessageInternalAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        // Create the thread if it does not exist. Bedrock agents cannot add messages to the thread without invoking so we don't do that here
        await this.CreateAsync(cancellationToken).ConfigureAwait(false);
    }
}
