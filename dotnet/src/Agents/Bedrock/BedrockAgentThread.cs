// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockAgentRuntime;
using Amazon.BedrockAgentRuntime.Model;

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

    /// <summary>
    /// Creates the thread and returns the thread id.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the thread has been created.</returns>
    public new Task CreateAsync(CancellationToken cancellationToken = default)
    {
        return this.CreateInternalAsync(cancellationToken);
    }

    /// <summary>
    /// Asynchronously retrieves all messages in the thread.
    /// </summary>
    /// <param name="maxResults">The maximum number of results to return in the response.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The messages in the thread.</returns>
    /// <exception cref="InvalidOperationException">The thread has been deleted.</exception>
    [Experimental("SKEXP0110")]
    public async IAsyncEnumerable<ChatMessageContent> GetMessagesAsync(int maxResults = 100, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (this.IsDeleted)
        {
            throw new InvalidOperationException("This thread has been deleted and cannot be used anymore.");
        }

        if (this.Id is null)
        {
            await this.CreateAsync(cancellationToken).ConfigureAwait(false);
        }

        var invocationSteps = await this._runtimeClient.ListInvocationStepsAsync(new ListInvocationStepsRequest() { SessionIdentifier = this.Id, MaxResults = maxResults }, cancellationToken).ConfigureAwait(false);
        var invocationStepTasks = invocationSteps.InvocationStepSummaries.Select(s => this._runtimeClient.GetInvocationStepAsync(new GetInvocationStepRequest { InvocationIdentifier = s.InvocationId }));
        await Task.WhenAll(invocationStepTasks).ConfigureAwait(false);

        foreach (var invocationStep in invocationStepTasks)
        {
            var response = await invocationStep.ConfigureAwait(false);
            if (response.InvocationStep?.Payload is not null)
            {
                foreach (BedrockSessionContentBlock? block in response.InvocationStep.Payload.ContentBlocks)
                {
                    yield return new ChatMessageContent
                    {
                        Content = block.Text
                    };
                }
            }
        }
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
