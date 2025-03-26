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

        var agent = await factory.CreateAgentFromYamlAsync(text);

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

        var agent = await factory.CreateAgentFromYamlAsync(text, kernel);

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

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel);

        await InvokeAgentAsync(agent!, "Cats and Dogs");
    }

    #region private
    private readonly Kernel _kernel;

    /// <summary>
    /// Invoke the agent with the user input.
    /// </summary>
    private async Task InvokeAgentAsync(KernelAgent agent, string input)
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
