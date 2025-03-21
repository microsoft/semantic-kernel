// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using SemanticKernel.IntegrationTests.TestSettings;
using AAIP = Azure.AI.Projects;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance;

public class AzureAIAgentFixture : AgentFixture
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<AzureAIAgentFixture>()
            .Build();

    private AAIP.AgentsClient? _agentsClient;
    private AAIP.Agent? _aiAgent;
    private AzureAIAgent? _agent;
    private AzureAIAgentThread? _thread;

    public override Agent Agent => this._agent!;

    public override AgentThread AgentThread => this._thread!;

    public override async Task<ChatHistory> GetChatHistory()
    {
        var chatHistory = new ChatHistory();
        await foreach (var existingMessage in this._thread!.GetMessagesAsync().ConfigureAwait(false))
        {
            chatHistory.Add(existingMessage);
        }
        return chatHistory;
    }

    public override Task DeleteThread(AgentThread thread)
    {
        return this._agentsClient!.DeleteThreadAsync(thread.Id);
    }

    public override async Task DisposeAsync()
    {
        if (this._thread!.IsActive)
        {
            await this._agentsClient!.DeleteThreadAsync(this._thread!.Id);
        }

        await this._agentsClient!.DeleteAgentAsync(this._aiAgent!.Id);
    }

    public override async Task InitializeAsync()
    {
        AzureAIConfiguration configuration = this._configuration.GetSection("AzureAI").Get<AzureAIConfiguration>()!;
        var client = AzureAIAgent.CreateAzureAIClient(configuration.ConnectionString, new AzureCliCredential());
        this._agentsClient = client.GetAgentsClient();

        this._aiAgent =
            await this._agentsClient.CreateAgentAsync(
                configuration.ChatModelId,
                name: "HelpfulAssistant",
                description: "Helpful Assistant",
                instructions: "You are a helpful assistant.");

        var kernelBuilder = Kernel.CreateBuilder();
        Kernel kernel = kernelBuilder.Build();

        this._agent = new AzureAIAgent(this._aiAgent, this._agentsClient) { Kernel = kernel };
        this._thread = new AzureAIAgentThread(this._agentsClient);
    }
}
