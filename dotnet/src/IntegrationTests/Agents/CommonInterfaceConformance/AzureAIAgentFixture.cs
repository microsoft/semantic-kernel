// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Azure;
using Azure.AI.Agents.Persistent;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using SemanticKernel.IntegrationTests.TestSettings;
using MAAI = Microsoft.Agents.AI;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance;

public class AzureAIAgentFixture : AgentFixture
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<AzureAIAgentFixture>()
            .Build();

    private PersistentAgentsClient? _agentsClient;
    private PersistentAgent? _aiAgent;
    private AzureAIAgent? _agent;
    private AzureAIAgentThread? _thread;
    private AzureAIAgentThread? _createdThread;
    private AzureAIAgentThread? _serviceFailingAgentThread;
    private AzureAIAgentThread? _createdServiceFailingAgentThread;

    public PersistentAgentsClient AgentsClient => this._agentsClient!;

    public override Agent Agent => this._agent!;

    public override MAAI.AIAgent AIAgent => this._agent!.AsAIAgent();

    public override AgentThread AgentThread => this._thread!;

    public override AgentThread CreatedAgentThread => this._createdThread!;

    public override AgentThread ServiceFailingAgentThread => this._serviceFailingAgentThread!;

    public override AgentThread CreatedServiceFailingAgentThread => this._createdServiceFailingAgentThread!;

    public override AgentThread GetNewThread()
    {
        return new AzureAIAgentThread(this._agentsClient!);
    }

    public override async Task<ChatHistory> GetChatHistory()
    {
        var chatHistory = new ChatHistory();
        await foreach (var existingMessage in this._thread!.GetMessagesAsync(ListSortOrder.Ascending).ConfigureAwait(false))
        {
            chatHistory.Add(existingMessage);
        }
        return chatHistory;
    }

    public override Task DeleteThread(AgentThread thread)
    {
        return this._agentsClient!.Threads.DeleteThreadAsync(thread.Id);
    }

    public override async Task DisposeAsync()
    {
        if (this._thread!.Id is not null)
        {
            try
            {
                await this._agentsClient!.Threads.DeleteThreadAsync(this._thread!.Id);
            }
            catch (RequestFailedException ex) when (ex.Status == 404)
            {
            }
        }

        try
        {
            await this._agentsClient!.Threads.DeleteThreadAsync(this._createdThread!.Id);
        }
        catch (RequestFailedException ex) when (ex.Status == 404)
        {
        }

        try
        {
            await this._agentsClient!.Threads.DeleteThreadAsync(this._createdServiceFailingAgentThread!.Id);
        }
        catch (RequestFailedException ex) when (ex.Status == 404)
        {
        }

        await this._agentsClient!.Administration.DeleteAgentAsync(this._aiAgent!.Id);
    }

    public override async Task InitializeAsync()
    {
        AzureAIConfiguration configuration = this._configuration.GetSection("AzureAI").Get<AzureAIConfiguration>()!;
        this._agentsClient = AzureAIAgent.CreateAgentsClient(configuration.Endpoint, new AzureCliCredential());

        this._aiAgent =
            await this._agentsClient.Administration.CreateAgentAsync(
                configuration.ChatModelId,
                name: "HelpfulAssistant",
                description: "Helpful Assistant",
                instructions: "You are a helpful assistant.");

        var kernelBuilder = Kernel.CreateBuilder();
        Kernel kernel = kernelBuilder.Build();

        this._agent = new AzureAIAgent(this._aiAgent, this._agentsClient) { Kernel = kernel };
        this._thread = new AzureAIAgentThread(this._agentsClient);

        this._createdThread = new AzureAIAgentThread(this._agentsClient);
        await this._createdThread.CreateAsync();

        var serviceFailingClient = AzureAIAgent.CreateAgentsClient("https://invalid", new AzureCliCredential());
        this._serviceFailingAgentThread = new AzureAIAgentThread(serviceFailingClient);

        var createdFailingThreadResponse = await this._agentsClient.Threads.CreateThreadAsync();
        this._createdServiceFailingAgentThread = new AzureAIAgentThread(serviceFailingClient, createdFailingThreadResponse.Value.Id);
    }
}
