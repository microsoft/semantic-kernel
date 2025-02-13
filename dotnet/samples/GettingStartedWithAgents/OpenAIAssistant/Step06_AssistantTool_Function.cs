// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Assistants;
using Plugins;

namespace GettingStarted.OpenAIAssistants;

/// <summary>
/// This example demonstrates how to define function tools for an <see cref="OpenAIAssistantAgent"/>
/// when the assistant is created. This is useful if you want to retrieve the assistant later and
/// then dynamically check what function tools it requires.
/// </summary>
public class Step06_AssistantTool_Function(ITestOutputHelper output) : BaseAgentsTest(output)
{
    private const string HostName = "Host";
    private const string HostInstructions = "Answer questions about the menu.";

    [Fact]
    public async Task UseSingleAssistantWithFunctionToolsAsync()
    {
        // Define the agent
        OpenAIClientProvider provider = this.GetClientProvider();
        AssistantClient client = provider.Client.GetAssistantClient();
        AssistantCreationOptions creationOptions =
            new()
            {
                Name = HostName,
                Instructions = HostInstructions,
                Metadata =
                {
                    { AssistantSampleMetadataKey, bool.TrueString }
                }
            };

        // In this sample the function tools are added to the assistant this is
        // important if you want to retrieve the assistant later and then dynamically check
        // what function tools it requires.
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        plugin.Select(f => f.ToToolDefinition(plugin.Name)).ToList().ForEach(td => creationOptions.Tools.Add(td));

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                clientProvider: this.GetClientProvider(),
                modelId: this.Model,
                creationOptions: creationOptions,
                kernel: new Kernel());

        // Add plugin to the agent's Kernel (same as direct Kernel usage).
        agent.Kernel.Plugins.Add(plugin);

        // Create a thread for the agent conversation.
        string threadId = await agent.CreateThreadAsync(new OpenAIThreadCreationOptions { Metadata = AssistantSampleMetadata });

        // Respond to user input
        try
        {
            await InvokeAgentAsync("Hello");
            await InvokeAgentAsync("What is the special soup and its price?");
            await InvokeAgentAsync("What is the special drink and its price?");
            await InvokeAgentAsync("Thank you");
        }
        finally
        {
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            await agent.AddChatMessageAsync(threadId, message);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(threadId))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }
}
