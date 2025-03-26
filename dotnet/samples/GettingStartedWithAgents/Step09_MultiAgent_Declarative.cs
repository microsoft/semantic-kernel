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
public class Step09_MultiAgent_Declarative : BaseAgentsTest
{
    public Step09_MultiAgent_Declarative(ITestOutputHelper output) : base(output)
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
        Kernel kernel = this.CreateKernelWithChatCompletion();

        var text =
            """
            type: chat_completion_agent
            name: StoryAgent
            description: Store Telling Agent
            instructions: Tell a story suitable for children about the topic provided by the user.
            """;

        var agent = await this._kernelAgentFactory.CreateAgentFromYamlAsync(text, kernel);

        await foreach (ChatMessageContent response in agent!.InvokeAsync(new ChatMessageContent(AuthorRole.User, "Cats and Dogs")))
        {
            this.WriteAgentChatMessage(response);
        }
    }

    #region private
    private readonly Kernel _kernel;
    private readonly KernelAgentFactory _kernelAgentFactory;
    #endregion
}
