// Copyright (c) Microsoft. All rights reserved.

// Remove SIMPLE_OUTPUT definition to simulate active logging services.
// Enabling results in sample output that is easier to review.
#define SIMPLE_OUTPUT

using System.Diagnostics;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Service;
using Microsoft.SemanticKernel.ChatCompletion;
using ServiceAgents;
using ChatTokenUsage = OpenAI.Chat.ChatTokenUsage;

namespace GettingStarted.ServiceAgents;

/// <summary>
/// Base class for exposing four (4) sample executions of a particular <see cref="ServiceAgent"/>.
///
/// 1. UseAgentAsDeveloperAsync: Invoke the agent as an application/service developer (with its own locally managed thread).
/// 2. UseAgentFromHostAsync: Invoke the agent within the context of an externally managed Azure Agent thread.
/// 3. UseStreamingAsDeveloperAsync: Sames as #1, but streaming response.
/// 4. UseStreamingFromHostAsync: Same as #2, but streaming response.
/// </summary>
/// <remarks>
/// For all cases, the agent is created via its provider, but a developer would be expected to use the agent constructor directly.
/// Cases #1 and #3 only use the host to create the agent and nothing else.
/// </remarks>
public abstract class BaseServiceAgentSample<TAgent> : BaseAzureAgentTest
    where TAgent : ServiceAgent
{
    protected BaseServiceAgentSample(ITestOutputHelper output) : base(output)
    {
        this.AgentHost = new ServiceAgentHost<TAgent>(this.Client, this.Configuration, this.LoggerFactory);
    }

#if SIMPLE_OUTPUT
    protected new ILoggerFactory LoggerFactory => NullLoggerFactory.Instance;
#endif

    protected abstract string[] Questions { get; }

    private ServiceAgentHost<TAgent> AgentHost { get; }

    /// <summary>
    /// A task specific agent may be used directly by an application developer.
    /// </summary>
    [Fact]
    public async Task UseAgentAsDeveloperAsync()
    {
        // Define the agent
        Agent agent = await this.AgentHost.CreateAgentAsync();

        // Create a new thread to capture the agent interaction.
        ChatHistory history = [];
        // Invoke the agent with input messages.
        foreach (string question in Questions)
        {
            await InvokeAgentAsync(question);
        }

        // Display the complete thread to audit state
        this.DisplayThreadHistory(history);

        // Local function to invoke agent and display input and response messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatHistoryAgentThread thread = new();

            ChatMessageContent message = new(AuthorRole.User, input);
            this.WriteAgentChatMessage(message);

            // Invoke the agent with an explicit input message.
            TokenCounter counter = new();
            AgentInvokeOptions options = new() { OnIntermediateMessage = counter.ProcessMessage };
            Stopwatch timer = Stopwatch.StartNew();
            await foreach (ChatMessageContent response in agent.InvokeAsync(input, thread, options))
            {
                this.WriteAgentChatMessage(response);
            }
            timer.Stop();
            Console.WriteLine($"Duration: {timer}");
            Console.WriteLine($"Tokens: {counter.TotalTokens}");
            history.AddRange(thread.ChatHistory);
        }
    }

    /// <summary>
    /// A task specific agent may be referenced from the foundry catalog
    /// and invoked via a service host.
    /// </summary>
    [Fact]
    public async Task UseAgentFromHostAsync()
    {
        // Simulate the creation of a foundry thread by an application or service.
        string threadId = await this.AgentHost.SimulateThreadCreationAsync();

        try
        {
            // Invoke the agent via the simulated host
            foreach (string question in Questions)
            {
                await InvokeAgentAsync(question);
            }

            // Display the complete thread to audit state
            this.DisplayThreadHistory(this.AgentHost.GetThreadMessagesAsync(threadId).ToEnumerable());
        }
        finally
        {
            await this.AgentHost.CleanupThreadAsync(threadId);
        }

        // Local function to invoke agent and display response messages.
        async Task InvokeAgentAsync(string input)
        {
            // Simulate the thread being updated by the user or another agent.
            await this.AgentHost.SimulateThreadUpdateAsync(threadId, input);
            this.WriteAgentChatMessage(new ChatMessageContent(AuthorRole.User, input));

            // Invoke the agent via the service host.
            await foreach (ChatMessageContent response in this.AgentHost.InvokeAgentAsync(threadId))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }
    /// <summary>
    /// A task specific agent may be used directly by an application developer.
    /// </summary>
    [Fact]
    public async Task UseStreamingAsDeveloperAsync()
    {
        // Create the agent
        Agent agent = await this.AgentHost.CreateAgentAsync();

        // Create a new thread to capture the agent interaction.
        ChatHistoryAgentThread thread = new();

        // Invoke the agent with input messages.
        foreach (string question in Questions)
        {
            await InvokeAgentAsync(question);
        }

        // Display the complete thread to audit state
        this.DisplayThreadHistory(thread.ChatHistory);

        // Local function to invoke agent and display input and response messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            this.WriteAgentChatMessage(message);

            // Invoke the agent with an explicit input message.
            await foreach (StreamingChatMessageContent response in agent.InvokeStreamingAsync(input, thread))
            {
                Console.WriteLine(response.Content);
            }
        }
    }

    /// <summary>
    /// A task specific agent may be referenced from the foundry catalog
    /// and invoked via a service host.
    /// </summary>
    [Fact]
    public async Task UseStreamingFromHostAsync()
    {
        // Simulate the creation of a foundry thread by an application or service.
        string threadId = await this.AgentHost.SimulateThreadCreationAsync();

        try
        {
            // Invoke the agent via the simulated host
            foreach (string question in Questions)
            {
                await InvokeAgentAsync(question);
            }

            // Display the complete thread to audit state
            this.DisplayThreadHistory(this.AgentHost.GetThreadMessagesAsync(threadId).ToEnumerable());
        }
        finally
        {
            await this.AgentHost.CleanupThreadAsync(threadId);
        }

        // Local function to invoke agent and display response messages.
        async Task InvokeAgentAsync(string input)
        {
            // Simulate the thread being updated by the user or another agent.
            await this.AgentHost.SimulateThreadUpdateAsync(threadId, input);
            this.WriteAgentChatMessage(new ChatMessageContent(AuthorRole.User, input));

            // Invoke the agent via the service host.
            await foreach (StreamingChatMessageContent response in this.AgentHost.InvokeStreamingAsync(threadId))
            {
                Console.WriteLine(response.Content);
            }
        }
    }

    private void DisplayThreadHistory(IEnumerable<ChatMessageContent> history)
    {
        Console.WriteLine("\n--------------------\n--- Chat History ---");
        foreach (ChatMessageContent message in history)
        {
            // Output each message in the thread for review.
            this.WriteAgentChatMessage(message);
        }
    }

    private sealed class TokenCounter
    {
        public int TotalTokens { get; private set; }

        public Task ProcessMessage(ChatMessageContent message)
        {
            if (message.Metadata?.TryGetValue("Usage", out object? usage) ?? false)
            {
                if (usage is ChatTokenUsage chatUsage)
                {
                    this.TotalTokens += chatUsage.TotalTokenCount;
                }
            }
            return Task.CompletedTask;
        }
    }
}
