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
/// This example demonstrates how to declaratively create instances of <see cref="Microsoft.SemanticKernel.Agents.Agent"/>.
/// </summary>
public class Step10_MultiAgent_Declarative : BaseAgentsTest
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

        var agent = await this._kernelAgentFactory.CreateAgentFromYamlAsync(text, new() { Kernel = kernel });

        await foreach (ChatMessageContent response in agent!.InvokeAsync(new ChatMessageContent(AuthorRole.User, "Cats and Dogs")))
        {
            this.WriteAgentChatMessage(response);
        }
    }

    /// <summary>
    /// Demonstrates creating and using an Azure AI Agent with a Kernel.
    /// </summary>
    [Fact]
    public async Task AzureAIAgentWithKernel()
    {
        var text =
            """
            type: foundry_agent
            name: MyAgent
            description: My helpful agent.
            instructions: You are helpful agent.
            model:
              id: ${AzureAI:ChatModelId}
            """;

        var agent = await this._kernelAgentFactory.CreateAgentFromYamlAsync(text, new() { Kernel = this._kernel }, TestConfiguration.ConfigurationRoot);
        Assert.NotNull(agent);

        var input = "Could you please create a bar chart for the operating profit using the following data and provide the file to me? Company A: $1.2 million, Company B: $2.5 million, Company C: $3.0 million, Company D: $1.8 million";
        Microsoft.SemanticKernel.Agents.AgentThread? agentThread = null;
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
            var azureaiAgent = agent as AzureAIAgent;
            Assert.NotNull(azureaiAgent);
            await azureaiAgent.Client.DeleteAgentAsync(azureaiAgent.Id);

            if (agentThread is not null)
            {
                await agentThread.DeleteAsync();
            }
        }
    }

    public Step10_MultiAgent_Declarative(ITestOutputHelper output) : base(output)
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

    #region private
    private readonly Kernel _kernel;
    private readonly AgentFactory _kernelAgentFactory;
    #endregion
}
