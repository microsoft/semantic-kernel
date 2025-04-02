// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Assistants;
using SemanticKernel.IntegrationTests.TestSettings;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance;

/// <summary>
/// Contains setup and teardown for the <see cref="OpenAIAssistantAgent"/> tests.
/// </summary>
public class OpenAIAssistantAgentFixture : AgentFixture
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OpenAIAssistantAgentFixture>()
            .Build();

    private AssistantClient? _assistantClient;
    private Assistant? _assistant;
    private OpenAIAssistantAgent? _agent;
    private OpenAIAssistantAgentThread? _thread;
    private OpenAIAssistantAgentThread? _createdThread;
    private OpenAIAssistantAgentThread? _serviceFailingAgentThread;
    private OpenAIAssistantAgentThread? _createdServiceFailingAgentThread;

    public override Agent Agent => this._agent!;

    public override AgentThread AgentThread => this._thread!;

    public override AgentThread CreatedAgentThread => this._createdThread!;

    public override AgentThread ServiceFailingAgentThread => this._serviceFailingAgentThread!;

    public override AgentThread CreatedServiceFailingAgentThread => this._createdServiceFailingAgentThread!;

    public override async Task<ChatHistory> GetChatHistory()
    {
        var chatHistory = new ChatHistory();
        await foreach (var existingMessage in this._thread!.GetMessagesAsync(MessageCollectionOrder.Ascending).ConfigureAwait(false))
        {
            chatHistory.Add(existingMessage);
        }
        return chatHistory;
    }

    public override async Task DisposeAsync()
    {
        if (this._thread!.Id is not null)
        {
            try
            {
                await this._assistantClient!.DeleteThreadAsync(this._thread!.Id);
            }
            catch (ClientResultException ex) when (ex.Status == 404)
            {
            }
        }

        try
        {
            await this._assistantClient!.DeleteThreadAsync(this._createdThread!.Id);
        }
        catch (ClientResultException ex) when (ex.Status == 404)
        {
        }

        await this._assistantClient!.DeleteAssistantAsync(this._assistant!.Id);
    }

    public override Task DeleteThread(AgentThread thread)
    {
        return this._assistantClient!.DeleteThreadAsync(thread.Id);
    }

    public override async Task InitializeAsync()
    {
        AzureAIConfiguration configuration = this._configuration.GetSection("AzureAI").Get<AzureAIConfiguration>()!;
        var client = OpenAIAssistantAgent.CreateAzureOpenAIClient(new AzureCliCredential(), new Uri(configuration.Endpoint));
        this._assistantClient = client.GetAssistantClient();

        this._assistant =
            await this._assistantClient.CreateAssistantAsync(
                configuration.ChatModelId,
                name: "HelpfulAssistant",
                instructions: "You are a helpful assistant.");

        var kernelBuilder = Kernel.CreateBuilder();
        Kernel kernel = kernelBuilder.Build();

        this._agent = new OpenAIAssistantAgent(this._assistant, this._assistantClient) { Kernel = kernel };
        this._thread = new OpenAIAssistantAgentThread(this._assistantClient);

        this._createdThread = new OpenAIAssistantAgentThread(this._assistantClient);
        await this._createdThread.CreateAsync();

        var serviceFailingClient = OpenAIAssistantAgent.CreateAzureOpenAIClient(new AzureCliCredential(), new Uri("https://localhost/failingserviceclient"));
        this._serviceFailingAgentThread = new OpenAIAssistantAgentThread(serviceFailingClient.GetAssistantClient());

        var createdFailingThreadResponse = await this._assistantClient.CreateThreadAsync();
        this._createdServiceFailingAgentThread = new OpenAIAssistantAgentThread(serviceFailingClient.GetAssistantClient(), createdFailingThreadResponse.Value.Id);
    }
}
