// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.Projects;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.AzureAI.Extensions;

namespace Microsoft.SemanticKernel.Agents.Service;

/// <summary>
/// Defines a common contract for a container hosting a <see cref="ServiceAgent"/>
/// to instantiate and utilize an agent regardless of the shape of the constructor
/// on any <see cref="Agent"/> subclasss.
/// </summary>
/// <param name="configuration">The configuration used to initialize the agent.</param>
/// <param name="loggerFactory">The logging services for the agent.</param>
public abstract class ServiceAgentProvider(IConfiguration configuration, ILoggerFactory loggerFactory)
{
    /// <summary>
    /// The active configuration for the agent.
    /// </summary>
    protected IConfiguration Configuration => configuration;

    /// <summary>
    /// The logging services for the agent.
    /// </summary>
    protected ILoggerFactory LoggerFactory => loggerFactory;

    /// <summary>
    /// Instantiates the agent associated with the provider.
    /// </summary>
    /// <param name="id">The service defined identifier of the agent</param>
    /// <param name="name">The service defined name of the agent</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    public abstract ValueTask<Agent> CreateAgentAsync(string id, string? name, CancellationToken cancellationToken = default);

    /// <summary>
    /// Initializes a thread used for invoking the agent.
    /// </summary>
    /// <param name="threadId">The external thread-id</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns></returns>
    public abstract ValueTask<AgentThread> CreateThreadAsync(string threadId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Convenience method to retrieve messages from the specified thread.
    /// </summary>
    /// <param name="client">The foundry agent client</param>
    /// <param name="threadId">The thread identifier.</param>
    /// <param name="limit">The maximum number of messages to be retrieved.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>An enumeration of the thread's messages.</returns>
    protected internal static async IAsyncEnumerable<ChatMessageContent> GetThreadMessagesAsync(
        AgentsClient client,
        string threadId,
        int? limit = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        int messageCount = 0;
        bool hasMore = false;
        do
        {
            PageableList<ThreadMessage> messagePage =
                await client.GetMessagesAsync(
                    threadId,
                    runId: null,
                    limit: 100,
                    order: ListSortOrder.Ascending,
                    after: null,
                    before: null,
                    cancellationToken: cancellationToken).ConfigureAwait(false);

            hasMore = messagePage.HasMore;

            // %%% TODO: AGENT NAME
            foreach (ChatMessageContent message in messagePage.Data.Select(message => message.ToChatMessageContent(agentName: null)))
            {
                // Increment the message count
                messageCount++;

                // Yield each message to the caller
                yield return message;
            }
        }
        while (hasMore && messageCount < limit);
    }
}
