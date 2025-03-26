// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Plugins;

namespace GettingStarted;

/// <summary>
/// This example demonstrates how to declaratively create instances of <see cref="KernelAgent"/>.
/// </summary>
public class Step08_Declarative(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task ChatCompletionAgentWithKernelAsync()
    {
        Kernel kernel = this.CreateKernelWithChatCompletion();

        var text =
            """
            type: chat_completion_agent
            name: StoryAgent
            description: Store Telling Agent
            instructions: Tell a story suitable for children about the topic provided by the user.
            """;
        var kernelAgentFactory = new ChatCompletionAgentFactory();

        var agent = await kernelAgentFactory.CreateAgentFromYamlAsync(text, kernel) as ChatCompletionAgent;

        await InvokeAgentAsync(agent!, "Cats and Dogs");
    }

    [Fact]
    public async Task ChatCompletionAgentWithFunctionsAsync()
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
        var kernelAgentFactory = new ChatCompletionAgentFactory();

        var agent = await kernelAgentFactory.CreateAgentFromYamlAsync(text, kernel) as ChatCompletionAgent;

        await InvokeAgentAsync(agent!, "What is the special soup and how much does it cost?");
    }

    [Fact]
    public async Task ChatCompletionAgentWithTemplateAsync()
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
                - description: output1 description
            template:
                format: semantic-kernel
            """;
        var kernelAgentFactory = new ChatCompletionAgentFactory();
        var promptTemplateFactory = new KernelPromptTemplateFactory();

        var agent = await kernelAgentFactory.CreateAgentFromYamlAsync(text, kernel, promptTemplateFactory);
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

    #region private
    /// <summary>
    /// Invoke the <see cref="ChatCompletionAgent"/> with the user input.
    /// </summary>
    private async Task InvokeAgentAsync(ChatCompletionAgent agent, string input)
    {
        ChatHistory chat = [];
        ChatMessageContent message = new(AuthorRole.User, input);
        chat.Add(message);
        this.WriteAgentChatMessage(message);

        await foreach (ChatMessageContent response in agent.InvokeAsync(chat))
        {
            chat.Add(response);

            this.WriteAgentChatMessage(response);
        }
    }
    #endregion
}
