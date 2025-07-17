// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ClientModel;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI;
using OpenAI.Responses;
using SemanticKernel.IntegrationTests.TestSettings;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance;

/// <summary>
/// Contains setup and teardown for the <see cref="OpenAIResponseAgent"/> tests.
/// </summary>
public class OpenAIResponseAgentFixture(bool storeEnabled) : AgentFixture
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OpenAIResponseAgentFixture>()
        .Build();

    private OpenAIResponseClient? _responseClient;
    private OpenAIResponseAgent? _agent;
    private AgentThread? _thread;
    private OpenAIResponseAgentThread? _createdThread;
    private OpenAIResponseAgentThread? _serviceFailingAgentThread;
    private OpenAIResponseAgentThread? _createdServiceFailingAgentThread;

    public OpenAIResponseClient ResponseClient => this._responseClient!;

    public override Agent Agent => this._agent!;

    public override AgentThread AgentThread => this._thread!;

    public override AgentThread CreatedAgentThread => this._createdThread!;

    public override AgentThread ServiceFailingAgentThread => this._serviceFailingAgentThread!;

    public override AgentThread CreatedServiceFailingAgentThread => this._createdServiceFailingAgentThread!;

    public override AgentThread GetNewThread()
    {
        return storeEnabled ? new OpenAIResponseAgentThread(this._responseClient!) : new ChatHistoryAgentThread();
    }

    public override async Task<ChatHistory> GetChatHistory()
    {
        var chatHistory = new ChatHistory();

        if (this._thread is ChatHistoryAgentThread chatHistoryAgentThread)
        {
            await foreach (var existingMessage in chatHistoryAgentThread.GetMessagesAsync().ConfigureAwait(false))
            {
                chatHistory.Add(existingMessage);
            }
            return chatHistory;
        }

        if (this._thread is not OpenAIResponseAgentThread openAIResponseAgentThread)
        {
            throw new InvalidOperationException("The thread is not an OpenAIResponseAgentThread or a ChatHistoryAgentThread.");
        }

        await foreach (var existingMessage in openAIResponseAgentThread.GetMessagesAsync().ConfigureAwait(false))
        {
            chatHistory.Add(existingMessage);
        }

        return chatHistory;
    }

    public override async Task DisposeAsync()
    {
        if (storeEnabled)
        {
            if (this._thread!.Id is not null)
            {
                try
                {
                    await this._responseClient!.DeleteResponseAsync(this._thread!.Id);
                }
                catch (ClientResultException ex) when (ex.Status == 404)
                {
                }
            }

            if (this._createdThread!.Id is not null)
            {
                try
                {
                    await this._responseClient!.DeleteResponseAsync(this._createdThread!.Id);
                }
                catch (ClientResultException ex) when (ex.Status == 404)
                {
                }
            }
        }
    }

    public override Task DeleteThread(AgentThread thread)
    {
        return storeEnabled ? this._responseClient!.DeleteResponseAsync(thread.Id) : Task.CompletedTask;
    }

    public override async Task InitializeAsync()
    {
        OpenAIConfiguration configuration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        var options = new OpenAIClientOptions();
        this._responseClient = new(model: configuration.ChatModelId, credential: new ApiKeyCredential(configuration.ApiKey), options: options);

        var kernelBuilder = Kernel.CreateBuilder();
        Kernel kernel = kernelBuilder.Build();

        this._agent = new OpenAIResponseAgent(this._responseClient)
        {
            Name = "HelpfulAssistant",
            Instructions = "You are a helpful assistant.",
            StoreEnabled = storeEnabled,
            Kernel = kernel
        };
        this._thread = storeEnabled ? new OpenAIResponseAgentThread(this._responseClient) : new ChatHistoryAgentThread();

        var response = await this._responseClient.CreateResponseAsync([ResponseItem.CreateUserMessageItem("Hello")]);
        this._createdThread = new OpenAIResponseAgentThread(this._responseClient, response.Value.Id);

        var serviceFailingClient = new OpenAIResponseClient(configuration.ModelId, credential: new ApiKeyCredential("FakeApiKey"), options: options);
        this._serviceFailingAgentThread = new OpenAIResponseAgentThread(serviceFailingClient);

        this._createdServiceFailingAgentThread = new OpenAIResponseAgentThread(this._responseClient, "FakeId");
    }
}
