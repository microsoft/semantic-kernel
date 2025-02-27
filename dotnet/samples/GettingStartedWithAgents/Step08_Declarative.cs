// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using Azure.AI.Projects;
using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI;

namespace GettingStarted;

/// <summary>
/// This example demonstrates how to declaratively create instances of <see cref="KernelAgent"/>.
/// </summary>
public class Step08_Declarative : BaseAgentsTest
{
    public Step08_Declarative(ITestOutputHelper output) : base(output)
    {
        var openaiClient =
           this.UseOpenAIConfig ?
               OpenAIAssistantAgent.CreateOpenAIClient(new ApiKeyCredential(this.ApiKey ?? throw new ConfigurationNotFoundException("OpenAI:ApiKey"))) :
               !string.IsNullOrWhiteSpace(this.ApiKey) ?
                   OpenAIAssistantAgent.CreateAzureOpenAIClient(new ApiKeyCredential(this.ApiKey), new Uri(this.Endpoint!)) :
                   OpenAIAssistantAgent.CreateAzureOpenAIClient(new AzureCliCredential(), new Uri(this.Endpoint!));

        var aiProjectClient = AzureAIAgent.CreateAzureAIClient(TestConfiguration.AzureAI.ConnectionString, new AzureCliCredential());

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<OpenAIClient>(openaiClient);
        builder.Services.AddSingleton<AIProjectClient>(aiProjectClient);
        AddChatCompletionToKernel(builder);
        this._kernel = builder.Build();

        this._kernelAgentFactory = new AggregatorKernelAgentFactory(
            new ChatCompletionAgentFactory(),
            new OpenAIAssistantAgentFactory(),
            new AzureAIAgentFactory()
            );
    }

    [Fact]
    public async Task ChatCompletionAgentWithKernelAsync()
    {
        var text =
            """
            type: chat_completion_agent
            name: StoryAgent
            description: Store Telling Agent
            instructions: Tell a story suitable for children about the topic provided by the user.
            """;

        var agent = await this._kernelAgentFactory.CreateAgentFromYamlAsync(text, this._kernel) as ChatCompletionAgent;

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

        var agent = await this._kernelAgentFactory.CreateAgentFromYamlAsync(text, this._kernel) as OpenAIAssistantAgent;

        await InvokeAgentAsync(agent!, "Cats and Dogs");
    }

    [Fact]
    public async Task AzureAIAgentWithKernelAsync()
    {
        var text =
            """
            type: azureai_agent
            name: StoryAgent
            description: Store Telling Agent
            instructions: Tell a story suitable for children about the topic provided by the user.
            model:
              id: gpt-4o-mini
            """;

        var agent = await this._kernelAgentFactory.CreateAgentFromYamlAsync(text, this._kernel) as AzureAIAgent;

        await InvokeAgentAsync(agent!, "Cats and Dogs");
    }

    #region private
    private readonly Kernel _kernel;
    private readonly KernelAgentFactory _kernelAgentFactory;

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

    /// <summary>
    /// Invoke the <see cref="OpenAIAssistantAgent"/> with the user input.
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

    /// <summary>
    /// Invoke the <see cref="AzureAIAgent"/> with the user input.
    /// </summary>
    private async Task InvokeAgentAsync(AzureAIAgent agent, string input)
    {
        // Create a thread for the agent conversation.
        AgentThread thread = await agent.Client.CreateThreadAsync(metadata: SampleMetadata);

        // Respond to user input
        try
        {
            await InvokeAsync(input);
        }
        finally
        {
            await agent.Client.DeleteThreadAsync(thread.Id);
            await agent.Client.DeleteAgentAsync(agent!.Id);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            await agent!.AddChatMessageAsync(thread.Id, message);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(thread.Id))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }
    #endregion
}
