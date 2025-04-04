// Copyright (c) Microsoft. All rights reserved.

// Remove SIMPLE_OUTPUT definition to simulate active logging services.
// Enabling results in sample output that is easier to review.
#define SIMPLE_OUTPUT

using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Service;
using Microsoft.SemanticKernel.Agents.Template;
using Microsoft.SemanticKernel.ChatCompletion;
using ServiceAgents;

namespace GettingStarted.ServiceAgents;

/// <summary>
/// Demonstrate invocation of a <see cref="ChatServiceAgent"/>.
/// (A <see cref="ComposedServiceAgent"/> based on a <see cref="ChatCompletionAgent"/>
/// </summary>
public class Step01_ChatAgent(ITestOutputHelper output) : BaseAzureAgentTest(output)
{
#if SIMPLE_OUTPUT
    protected new ILoggerFactory LoggerFactory => NullLoggerFactory.Instance;
#endif

    /// <summary>
    /// A task specific agent may be used directly by an application developer.
    /// </summary>
    [Fact]
    public async Task UseAgentAsDeveloperAsync()
    {
        // Define the agent
        ChatServiceAgent agent =
            new()
            {
                Kernel = this.CreateKernelWithChatCompletion()
            };

        // Create a new thread to capture the agent interaction.
        ChatHistoryAgentThread thread = new();

        // Invoke the agent with input messages.
        await InvokeAgentAsync("Hello");
        await InvokeAgentAsync("Why is the sky blue?");
        await InvokeAgentAsync("How big is a rainbow?");
        await InvokeAgentAsync("Thank you");

        // Display the complete thread to audit state
        this.DisplayThreadHistory(thread.ChatHistory);

        // Local function to invoke agent and display input and response messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            this.WriteAgentChatMessage(message);

            // Invoke the agent with an explicit input message.
            await foreach (ChatMessageContent response in agent.InvokeAsync(input, thread))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }

    /// <summary>
    /// A task specific agent may be referenced from the foundry catalog
    /// and invoked via a service container.
    /// </summary>
    [Fact]
    public async Task UseAgentAsContainerAsync()
    {
        // Create the simulated service container
        AgentServiceContainer serviceContainer = new(this.Client, this.Configuration, this.LoggerFactory);

        // Simulate the creation of a foundry thread by an application or service.
        string threadId = await serviceContainer.SimulateThreadCreationAsync();

        try
        {
            // Invoke the agent via the simulated container
            await InvokeAgentAsync("Hello");
            await InvokeAgentAsync("Why is the sky blue?");
            await InvokeAgentAsync("How big is a rainbow?");
            await InvokeAgentAsync("Thank you");

            // Display the complete thread to audit state
            this.DisplayThreadHistory(serviceContainer.GetThreadMessagesAsync(threadId).ToEnumerable());
        }
        finally
        {
            await serviceContainer.CleanupThreadAsync(threadId);
        }

        // Local function to invoke agent and display response messages.
        async Task InvokeAgentAsync(string input)
        {
            // Simulate the thread being updated by the user or another agent.
            await serviceContainer.SimulateThreadUpdateAsync(threadId, input);
            this.WriteAgentChatMessage(new ChatMessageContent(AuthorRole.User, input));

            // Invoke the agent via the service container.
            await foreach (ChatMessageContent response in serviceContainer.InvokeAgentAsync(typeof(ChatServiceAgent), threadId))
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
        // Define the agent
        ChatServiceAgent agent =
            new()
            {
                Kernel = this.CreateKernelWithChatCompletion()
            };

        // Create a new thread to capture the agent interaction.
        ChatHistoryAgentThread thread = new();

        // Invoke the agent with input messages.
        await InvokeAgentAsync("Hello");
        await InvokeAgentAsync("Why is the sky blue?");
        await InvokeAgentAsync("How big is a rainbow?");
        await InvokeAgentAsync("Thank you");

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
    /// and invoked via a service container.
    /// </summary>
    [Fact]
    public async Task UseStreamingAsContainerAsync()
    {
        // Create the simulated service container
        AgentServiceContainer serviceContainer = new(this.Client, this.Configuration, this.LoggerFactory);

        // Simulate the creation of a foundry thread by an application or service.
        string threadId = await serviceContainer.SimulateThreadCreationAsync();

        try
        {
            // Invoke the agent via the simulated container
            await InvokeAgentAsync("Hello");
            await InvokeAgentAsync("Why is the sky blue?");
            await InvokeAgentAsync("How big is a rainbow?");
            await InvokeAgentAsync("Thank you");

            // Display the complete thread to audit state
            this.DisplayThreadHistory(serviceContainer.GetThreadMessagesAsync(threadId).ToEnumerable());
        }
        finally
        {
            await serviceContainer.CleanupThreadAsync(threadId);
        }

        // Local function to invoke agent and display response messages.
        async Task InvokeAgentAsync(string input)
        {
            // Simulate the thread being updated by the user or another agent.
            await serviceContainer.SimulateThreadUpdateAsync(threadId, input);
            this.WriteAgentChatMessage(new ChatMessageContent(AuthorRole.User, input));

            // Invoke the agent via the service container.
            await foreach (StreamingChatMessageContent response in serviceContainer.InvokeStreamingAsync(typeof(ChatServiceAgent), threadId))
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
}
