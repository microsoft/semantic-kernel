// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI.Extensions;
using Microsoft.SemanticKernel.Agents.Service;
using Foundry = Azure.AI.Projects;

namespace ServiceAgents;

/// <summary>
/// A local mock of the Agent Host needed to run SK Agents in the cloud.
/// </summary>
/// <remarks>
/// This isn't intended for inform or resemble the shape of a real agent host.
/// Its only purpose is to interact with the Service Agents using generalized
/// factory/provider pattern.  That is, it doesn't have any specific knowledge
/// of the actual agent implementation (other than its .NET type).
/// </remarks>
internal sealed class ServiceAgentHost<TAgent>(
    Foundry.AIProjectClient client,
    IConfiguration configuration,
    ILoggerFactory loggerFactory)
    where TAgent : ServiceAgent
{
    private Foundry.AgentsClient Client { get; } = client.GetAgentsClient();

    public async Task<Agent> CreateAgentAsync()
    {
        return (await this.InitializeAgentAsync()).Agent;
    }

    /// <summary>
    /// Simulate the primary ability of service container to invoke the agent with the current thread state.
    /// </summary>
    public async IAsyncEnumerable<ChatMessageContent> InvokeAgentAsync(string threadId)
    {
        // Initialize the agent with container supplied parameters.
        (ServiceAgentProvider serviceProvider, Agent agent) = await this.InitializeAgentAsync();

        // Create a agent thread based on a foundry thread.
        AgentThread thread = await serviceProvider.CreateThreadAsync(threadId);

        AgentInvokeOptions options =
            new()
            {
                // Sample Only: Container expected to manage adding agent response to the foundry thread
                OnIntermediateMessage = HandleNewMessage
            };

        // Invoke the agent with the current thread state.
        Stopwatch timer = Stopwatch.StartNew();
        await foreach (ChatMessageContent response in agent.InvokeAsync([], thread, options))
        {
            // Yield the response back to the sample for display.
            // Not expected functionality for the service container.
            yield return response;
        }
        timer.Stop();
        Console.WriteLine($"Duration: {timer}");

        // Callback to handle new messages from the agent
        async Task HandleNewMessage(ChatMessageContent message)
        {
            // Updating the external thread with the agent response, including function calls and reslts.
            // The agent is expected to _not_ mutate the external thread.
            await this.Client.CreateMessageAsync(threadId, Foundry.MessageRole.Agent, message.Content).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Simulate the primary ability of service container to invoke the agent with the current thread state.
    /// </summary>
    public async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(string threadId)
    {
        // Initialize the agent with container supplied parameters.
        (ServiceAgentProvider serviceProvider, Agent agent) = await this.InitializeAgentAsync();

        // Create a agent thread based on a foundry thread.
        AgentThread thread = await serviceProvider.CreateThreadAsync(threadId);

        AgentInvokeOptions options =
            new()
            {
                // Sample Only: Container expected to manage adding agent response to the foundry thread
                OnIntermediateMessage = HandleNewMessage
            };

        // Invoke the agent with the current thread state.
        await foreach (StreamingChatMessageContent response in agent.InvokeStreamingAsync([], thread, options))
        {
            // Yield the response back to the sample for display.
            // Not expected functionality for the service container.
            yield return response;
        }

        // Callback to handle new messages from the agent
        async Task HandleNewMessage(ChatMessageContent message)
        {
            // Updating the external thread with the agent response, including function calls and reslts.
            // The agent is expected to _not_ mutate the external thread.
            await this.Client.CreateMessageAsync(threadId, Foundry.MessageRole.Agent, message.Content).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Simulate the thread being created outside of the the scope of the service container.
    /// </summary>
    public async Task<string> SimulateThreadCreationAsync()
    {
        Foundry.AgentThread thread = await this.Client.CreateThreadAsync();
        return thread.Id;
    }

    /// <summary>
    /// Simulate the thread being updated outside of the the scope of the service container.
    /// </summary>
    public async Task SimulateThreadUpdateAsync(string threadId, string input)
    {
        await this.Client.CreateMessageAsync(threadId, Foundry.MessageRole.User, input);
    }

    /// <summary>
    /// Simulate the thread being deleted outside of the the scope of the service container.
    /// </summary>
    public async Task CleanupThreadAsync(string threadId)
    {
        await this.Client.DeleteThreadAsync(threadId);
    }

    /// <summary>
    /// Utility to retrieve all messages from the thread for the sample to access
    /// so the sample might display the entire history of the thread.
    /// </summary>
    public async IAsyncEnumerable<ChatMessageContent> GetThreadMessagesAsync(string threadId)
    {
        int messageCount = 0;
        bool hasMore = false;
        do
        {
            Foundry.PageableList<Foundry.ThreadMessage> messagePage =
                await this.Client.GetMessagesAsync(
                    threadId,
                    runId: null,
                    limit: 100,
                    order: Foundry.ListSortOrder.Ascending,
                    after: null,
                    before: null).ConfigureAwait(false);

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
        while (hasMore);
    }

    private async Task<(ServiceAgentProvider Provider, Agent Agent)> InitializeAgentAsync()
    {
        ServiceAgentProvider provider = ServiceAgentProviderFactory.CreateServicesProvider(typeof(TAgent), configuration, loggerFactory);
        Agent agent = await provider.CreateAgentAsync(Guid.NewGuid().ToString(), "TestAgent");
        return (provider, agent);
    }
}
