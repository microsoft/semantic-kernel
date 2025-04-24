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
    /// <summary>
    /// Demonstrates creating and using a OpenAI Assistant using configuration.
    /// </summary>
    [Fact]
    public async Task OpenAIAssistantAgentWithConfigurationForOpenAI()
    {
        var text =
            """
            type: openai_assistant
            name: MyAgent
            description: My helpful agent.
            instructions: You are helpful agent.
            model:
              id: ${OpenAI:ChatModelId}
              connection:
                type: openai
                api_key: ${OpenAI:ApiKey}
            """;
        OpenAIAssistantAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text, configuration: TestConfiguration.ConfigurationRoot);

        await InvokeAgentAsync(agent!, "Could you please create a bar chart for the operating profit using the following data and provide the file to me? Company A: $1.2 million, Company B: $2.5 million, Company C: $3.0 million, Company D: $1.8 million");
    }

    /// <summary>
    /// Demonstrates creating and using a OpenAI Assistant using configuration for Azure OpenAI.
    /// </summary>
    [Fact]
    public async Task OpenAIAssistantAgentWithConfigurationForAzureOpenAI()
    {
        var text =
            """
            type: openai_assistant
            name: MyAgent
            description: My helpful agent.
            instructions: You are helpful agent.
            model:
              id: ${AzureOpenAI:ChatModelId}
              connection:
                type: azure_openai
                endpoint: ${AzureOpenAI:Endpoint}
            """;
        OpenAIAssistantAgentFactory factory = new();

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<TokenCredential>(new AzureCliCredential());
        var kernel = builder.Build();

        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = kernel }, TestConfiguration.ConfigurationRoot);

        await InvokeAgentAsync(agent!, "Could you please create a bar chart for the operating profit using the following data and provide the file to me? Company A: $1.2 million, Company B: $2.5 million, Company C: $3.0 million, Company D: $1.8 million");
    }

    /// <summary>
    /// Demonstrates creating and using a OpenAI Assistant using a Kernel.
    /// </summary>
    [Fact]
    public async Task OpenAIAssistantAgentWithKernel()
    {
        var text =
            """
            type: openai_assistant
            name: StoryAgent
            description: Story Telling Agent
            instructions: Tell a story suitable for children about the topic provided by the user.
            model:
              id: ${AzureOpenAI:ChatModelId}
            """;
        OpenAIAssistantAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = this._kernel }, configuration: TestConfiguration.ConfigurationRoot);

        await InvokeAgentAsync(agent!, "Cats and Dogs");
    }

    /// <summary>
    /// Demonstrates creating and using a OpenAI Assistant with templated instructions.
    /// </summary>
    [Fact]
    public async Task OpenAIAssistantAgentWithTemplate()
    {
        var text =
            """
            type: openai_assistant
            name: StoryAgent
            description: A agent that generates a story about a topic.
            instructions: Tell a story about {{$topic}} that is {{$length}} sentences long.
            model:
              id: ${AzureOpenAI:ChatModelId}
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
        OpenAIAssistantAgentFactory factory = new();
        var promptTemplateFactory = new KernelPromptTemplateFactory();

        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = this._kernel, PromptTemplateFactory = promptTemplateFactory }, TestConfiguration.ConfigurationRoot);
        Assert.NotNull(agent);

        var options = new AgentInvokeOptions()
        {
            KernelArguments = new()
            {
                { "topic", "Dogs" },
                { "length", "3" },
            }
        };

        AgentThread? agentThread = null;
        try
        {
            await foreach (var response in agent.InvokeAsync([], agentThread, options))
            {
                agentThread = response.Thread;
                this.WriteAgentChatMessage(response);
            }
        }
        finally
        {
            var openaiAgent = agent as OpenAIAssistantAgent;
            Assert.NotNull(openaiAgent);
            await openaiAgent.Client.DeleteAssistantAsync(openaiAgent.Id);

            if (agentThread is not null)
            {
                await agentThread.DeleteAsync();
            }
        }
    }

    public Step07_Assistant_Declarative(ITestOutputHelper output) : base(output)
    {
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<OpenAIClient>(this.Client);
        this._kernel = builder.Build();
    }

    #region private
    private readonly Kernel _kernel;

    /// <summary>
    /// Invoke the agent with the user input.
    /// </summary>
    private async Task InvokeAgentAsync(Agent agent, string input)
    {
        AgentThread? agentThread = null;
        try
        {
            await foreach (AgentResponseItem<ChatMessageContent> response in agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, input)))
            {
                agentThread = response.Thread;
                WriteAgentChatMessage(response);
            }
        }
        catch (Exception e)
        {
            Console.WriteLine($"Error invoking agent: {e.Message}");
        }
        finally
        {
            var openaiAgent = agent as OpenAIAssistantAgent;
            Assert.NotNull(openaiAgent);
            await openaiAgent.Client.DeleteAssistantAsync(openaiAgent.Id);

            if (agentThread is not null)
            {
                await agentThread.DeleteAsync();
            }
        }
    }
    #endregion
}
