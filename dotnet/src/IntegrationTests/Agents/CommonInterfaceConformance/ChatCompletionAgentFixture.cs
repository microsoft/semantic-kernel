// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using SemanticKernel.IntegrationTests.TestSettings;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance;

/// <summary>
/// Contains setup and teardown for the <see cref="ChatCompletionAgent"/> tests.
/// </summary>
public class ChatCompletionAgentFixture : AgentFixture
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<ChatCompletionAgentFixture>()
            .Build();

    private ChatCompletionAgent? _agent;
    private ChatHistoryAgentThread? _thread;
    private ChatHistoryAgentThread? _createdThread;

    public override Agent Agent => this._agent!;

    public override AgentThread AgentThread => this._thread!;

    public override AgentThread CreatedAgentThread => this._createdThread!;

    public override AgentThread ServiceFailingAgentThread => null!;

    public override AgentThread CreatedServiceFailingAgentThread => null!;

    public override async Task<ChatHistory> GetChatHistory()
    {
        var chatHistory = new ChatHistory();
        await foreach (var existingMessage in this._thread!.GetMessagesAsync().ConfigureAwait(false))
        {
            chatHistory.Add(existingMessage);
        }
        return chatHistory;
    }

    public override Task DisposeAsync()
    {
        return Task.CompletedTask;
    }

    public override Task DeleteThread(AgentThread thread)
    {
        return Task.CompletedTask;
    }

    public async override Task InitializeAsync()
    {
        AzureOpenAIConfiguration configuration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>()!;

        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddAzureOpenAIChatCompletion(
            deploymentName: configuration.ChatDeploymentName!,
            endpoint: configuration.Endpoint,
            credentials: new AzureCliCredential());
        Kernel kernel = kernelBuilder.Build();

        this._agent = new ChatCompletionAgent()
        {
            Kernel = kernel,
            Instructions = "You are a helpful assistant.",
        };
        this._thread = new ChatHistoryAgentThread();
        this._createdThread = new ChatHistoryAgentThread();
        await this._createdThread.CreateAsync();
    }
}
