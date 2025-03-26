// Copyright (c) Microsoft. All rights reserved.
using Azure.Core;
using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI;

namespace GettingStarted.OpenAIAssistants;

/// <summary>
/// This example demonstrates how to declaratively create instances of <see cref="OpenAIAssistantAgent"/>.
/// </summary>
public class Step07_Assistant_Declarative : BaseAssistantTest
{
    public Step07_Assistant_Declarative(ITestOutputHelper output) : base(output)
    {
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<OpenAIClient>(this.Client);
        this._kernel = builder.Build();
    }

    [Fact]
    public async Task OpenAIAssistantAgentWithConfigurationForOpenAIAsync()
    {
        var text =
            $"""
            type: openai_assistant
            name: StoryAgent
            description: Store Telling Agent
            instructions: Tell a story suitable for children about the topic provided by the user.
            model:
              id: gpt-4o-mini
              connection:
                type: openai
                api_key: {TestConfiguration.OpenAI.ApiKey}
            """;
        OpenAIAssistantAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text) as OpenAIAssistantAgent;

        await InvokeAgentAsync(agent!, "Cats and Dogs");
    }

    [Fact]
    public async Task OpenAIAssistantAgentWithConfigurationForAzureOpenAIAsync()
    {
        var text =
            $"""
            type: openai_assistant
            name: StoryAgent
            description: Store Telling Agent
            instructions: Tell a story suitable for children about the topic provided by the user.
            model:
              id: gpt-4o-mini
              connection:
                type: azure_openai
                endpoint: {TestConfiguration.AzureOpenAI.Endpoint}
            """;
        OpenAIAssistantAgentFactory factory = new();

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<TokenCredential>(new AzureCliCredential());
        var kernel = builder.Build();

        var agent = await factory.CreateAgentFromYamlAsync(text, kernel) as OpenAIAssistantAgent;

        await InvokeAgentAsync(agent!, "Cats and Dogs");
    }

    [Fact]
    public async Task OpenAIAssistantAgentWithKernelAsync()
    {
        var text =
            """
            type: openai_assistant
            name: StoryAgent
            description: Store Telling Agent
            instructions: Tell a story suitable for children about the topic provided by the user.
            model:
              id: gpt-4o-mini
            """;
        OpenAIAssistantAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel) as OpenAIAssistantAgent;

        await InvokeAgentAsync(agent!, "Cats and Dogs");
    }

    [Fact]
    public async Task OpenAIAssistantAgentWithTemplateAsync()
    {
        var text =
            """
            type: openai_assistant
            name: StoryAgent
            description: A agent that generates a story about a topic.
            instructions: Tell a story about {{$topic}} that is {{$length}} sentences long.
            model:
              id: gpt-4o-mini
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
        OpenAIAssistantAgentFactory factory = new();
        var promptTemplateFactory = new KernelPromptTemplateFactory();

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel) as OpenAIAssistantAgent;
        Assert.NotNull(agent);

        var options = new AgentInvokeOptions()
        {
            KernelArguments = new()
            {
                { "topic", "Dogs" },
                { "length", "3" },
            }
        };

        string threadId = await agent.Client.CreateThreadAsync(metadata: SampleMetadata);
        var agentThread = new OpenAIAssistantAgentThread(agent.Client, threadId);

        try
        {
            await foreach (ChatMessageContent response in agent.InvokeAsync([], agentThread, options))
            {
                this.WriteAgentChatMessage(response);
            }
        }
        finally
        {
            await agent.Client.DeleteThreadAsync(threadId);
            await agent.Client.DeleteAssistantAsync(agent.Id);
        }
    }

    #region private
    private readonly Kernel _kernel;

    /// <summary>
    /// Invoke the agent with the user input.
    /// </summary>
    private async Task InvokeAgentAsync(OpenAIAssistantAgent agent, string input)
    {
        // Create a thread for the agent conversation.
        string threadId = await agent.Client.CreateThreadAsync(metadata: SampleMetadata);

        try
        {
            await InvokeAgentAsync(input);
        }
        finally
        {
            await agent.Client.DeleteThreadAsync(threadId);
            await agent.Client.DeleteAssistantAsync(agent.Id);
        }

        // Local function to invoke agent and display the response.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            await agent.AddChatMessageAsync(threadId, message);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(threadId))
            {
                WriteAgentChatMessage(response);
            }
        }
    }
    #endregion
}
