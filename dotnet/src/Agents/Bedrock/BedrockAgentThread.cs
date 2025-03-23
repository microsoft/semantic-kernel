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
    private readonly AmazonBedrockAgentRuntimeClient _runtimeClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="BedrockAgentThread"/> class.
    /// </summary>
    /// <param name="runtimeClient">A client used to interact with the Bedrock Agent runtime service.</param>
    /// <param name="sessionId">An optional session Id to continue an exsting session.</param>
    /// <exception cref="ArgumentNullException"></exception>
    public BedrockAgentThread(AmazonBedrockAgentRuntimeClient runtimeClient, string? sessionId = null)
    {
        this._runtimeClient = runtimeClient ?? throw new ArgumentNullException(nameof(runtimeClient));
        this.Id = sessionId;
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
            var response = await this._runtimeClient.DeleteSessionAsync(
                request: new()
                {
                    SessionIdentifier = this.Id
                },
                cancellationToken: cancellationToken).ConfigureAwait(false);
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
    protected override Task OnNewMessageInternalAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        string message = $"{nameof(BedrockAgentThread)} does not support adding messages directly to the thread.";
        throw new NotImplementedException(message);
    }
}
