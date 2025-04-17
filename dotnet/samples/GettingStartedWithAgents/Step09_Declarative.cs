// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Plugins;

namespace GettingStarted;

/// <summary>
/// This example demonstrates how to declaratively create instances of <see cref="Agent"/>.
/// </summary>
public class Step09_Declarative(ITestOutputHelper output) : BaseAgentsTest(output)
{
    /// <summary>
    /// Demonstrates creating and using a Chat Completion Agent with a Kernel.
    /// </summary>
    [Fact]
    public async Task ChatCompletionAgentWithKernel()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();

        var text =
            """
            type: chat_completion_agent
            name: StoryAgent
            description: Story Telling Agent
            instructions: Tell a story suitable for children about the topic provided by the user.
            """;
        var agentFactory = new ChatCompletionAgentFactory();

        var agent = await agentFactory.CreateAgentFromYamlAsync(text, new() { Kernel = kernel });

        await foreach (ChatMessageContent response in agent!.InvokeAsync("Cats and Dogs"))
        {
            this.WriteAgentChatMessage(response);
        }
    }

    /// <summary>
    /// Demonstrates creating and using a Chat Completion Agent with functions.
    /// </summary>
    [Fact]
    public async Task ChatCompletionAgentWithFunctions()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        kernel.Plugins.Add(plugin);

        var text =
            """
            type: chat_completion_agent
            name: FunctionCallingAgent
            instructions: Use the provided functions to answer questions about the menu.
            description: This agent uses the provided functions to answer questions about the menu.
            model:
              options:
                temperature: 0.4
            tools:
              - id: MenuPlugin.GetSpecials
                type: function
              - id: MenuPlugin.GetItemPrice
                type: function
            """;
        var agentFactory = new ChatCompletionAgentFactory();

        var agent = await agentFactory.CreateAgentFromYamlAsync(text, new() { Kernel = kernel });

        await foreach (ChatMessageContent response in agent!.InvokeAsync(new ChatMessageContent(AuthorRole.User, "What is the special soup and how much does it cost?")))
        {
            this.WriteAgentChatMessage(response);
        }
    }

    /// <summary>
    /// Demonstrates creating and using a Chat Completion Agent with templated instructions.
    /// </summary>
    [Fact]
    public async Task ChatCompletionAgentWithTemplate()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();

        var text =
            """
            type: chat_completion_agent
            name: StoryAgent
            description: A agent that generates a story about a topic.
            instructions: Tell a story about {{$topic}} that is {{$length}} sentences long.
            inputs:
                topic:
                    description: The topic of the story.
                    required: true
                    default: Cats
                length:
                    description: The number of sentences in the story.
                    required: true
                    default: 2
            outputs:
                output1:
                    description: output1 description
            template:
                format: semantic-kernel
            """;
        var agentFactory = new ChatCompletionAgentFactory();
        var promptTemplateFactory = new KernelPromptTemplateFactory();

        var agent = await agentFactory.CreateAgentFromYamlAsync(text, new() { Kernel = kernel, PromptTemplateFactory = promptTemplateFactory });
        Assert.NotNull(agent);

        var options = new AgentInvokeOptions()
        {
            KernelArguments = new()
            {
                { "topic", "Dogs" },
                { "length", "3" },
            }
        };

        await foreach (ChatMessageContent response in agent.InvokeAsync([], options: options))
        {
            this.WriteAgentChatMessage(response);
        }
    }
}
