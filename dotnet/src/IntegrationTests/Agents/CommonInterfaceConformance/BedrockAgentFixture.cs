// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Amazon.BedrockAgent;
using Amazon.BedrockAgent.Model;
using Amazon.BedrockAgentRuntime;
using Amazon.BedrockAgentRuntime.Model;
using Amazon.Runtime;
using Azure;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Bedrock;
using Microsoft.SemanticKernel.ChatCompletion;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance;

internal sealed class BedrockAgentFixture : AgentFixture, IAsyncDisposable
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<BedrockAgentTests>()
        .Build();

    private Amazon.BedrockAgent.Model.Agent? _bedrockAgent;
    private BedrockAgent? _agent;
    private BedrockAgentThread? _thread;
    private BedrockAgentThread? _createdThread;
    private BedrockAgentThread? _serviceFailingAgentThread;
    private BedrockAgentThread? _createdServiceFailingAgentThread;
    private AmazonBedrockAgentRuntimeClient? _serviceFailingAgentClient;
    private readonly AmazonBedrockAgentClient _client = new();
    private readonly AmazonBedrockAgentRuntimeClient _runtimeClient = new();

    public override Microsoft.SemanticKernel.Agents.Agent Agent => this._agent!;

    public override AgentThread AgentThread => this._thread!;

    public override AgentThread CreatedAgentThread => this._createdThread!;

    public override AgentThread ServiceFailingAgentThread => this._serviceFailingAgentThread!;

    public override AgentThread CreatedServiceFailingAgentThread => this._createdServiceFailingAgentThread!;

    public override async Task DeleteThread(AgentThread thread)
    {
        await this._runtimeClient!.EndSessionAsync(new EndSessionRequest() { SessionIdentifier = thread.Id });
        await this._runtimeClient.DeleteSessionAsync(new DeleteSessionRequest() { SessionIdentifier = thread.Id });
    }

    async ValueTask IAsyncDisposable.DisposeAsync()
    {
        await this.DisposeAsync();
    }

    public override async Task DisposeAsync()
    {
        if (this._thread!.Id is not null)
        {
            try
            {
                await this._runtimeClient!.EndSessionAsync(new EndSessionRequest() { SessionIdentifier = this._thread!.Id });
                await this._runtimeClient!.DeleteSessionAsync(new DeleteSessionRequest() { SessionIdentifier = this._thread!.Id });
            }
            catch (RequestFailedException ex) when (ex.Status == 404)
            {
            }
        }

        if (this._createdThread!.Id is not null)
        {
            try
            {
                await this._runtimeClient!.EndSessionAsync(new EndSessionRequest() { SessionIdentifier = this._createdThread!.Id });
                await this._runtimeClient!.DeleteSessionAsync(new DeleteSessionRequest() { SessionIdentifier = this._createdThread!.Id });
            }
            catch (RequestFailedException ex) when (ex.Status == 404)
            {
            }
        }

        if (this._createdServiceFailingAgentThread!.Id is not null)
        {
            try
            {
                await this._runtimeClient!.EndSessionAsync(new EndSessionRequest() { SessionIdentifier = this._createdServiceFailingAgentThread!.Id });
                await this._runtimeClient!.DeleteSessionAsync(new DeleteSessionRequest() { SessionIdentifier = this._createdServiceFailingAgentThread!.Id });
            }
            catch (RequestFailedException ex) when (ex.Status == 404)
            {
            }
        }

        await this._client.DeleteAgentAsync(new DeleteAgentRequest() { AgentId = this._bedrockAgent!.AgentId });
        this._serviceFailingAgentClient?.Dispose();
        this._runtimeClient.Dispose();
        this._client.Dispose();
    }

    public override Task<ChatHistory> GetChatHistory()
    {
        // The BedrockAgentThread cannot read messages from the thread. This is a limitation of Bedrock Sessions.
        throw new NotImplementedException();
    }

    public override async Task InitializeAsync()
    {
        this._bedrockAgent = await this._client.CreateAndPrepareAgentAsync(this.GetCreateAgentRequest());

        var kernelBuilder = Kernel.CreateBuilder();
        Kernel kernel = kernelBuilder.Build();

        this._agent = new BedrockAgent(this._bedrockAgent, this._client, this._runtimeClient) { Kernel = kernel };
        this._thread = new BedrockAgentThread(this._runtimeClient);

        this._createdThread = new BedrockAgentThread(this._runtimeClient);
        await this._createdThread.CreateAsync();

        this._serviceFailingAgentClient = new AmazonBedrockAgentRuntimeClient(new BasicAWSCredentials("", ""));
        this._serviceFailingAgentThread = new BedrockAgentThread(this._serviceFailingAgentClient);

        var createdFailingThreadResponse = await this._runtimeClient.CreateSessionAsync(new CreateSessionRequest(), default);
        this._createdServiceFailingAgentThread = new BedrockAgentThread(this._serviceFailingAgentClient, createdFailingThreadResponse.SessionId);
    }

    private const string AgentName = "SKIntegrationTestAgent";
    private const string AgentDescription = "A helpful assistant who helps users find information.";
    private const string AgentInstruction = "You're a helpful assistant who helps users find information.";
    private CreateAgentRequest GetCreateAgentRequest()
    {
        BedrockAgentConfiguration bedrockAgentSettings = this._configuration.GetSection("BedrockAgent").Get<BedrockAgentConfiguration>()!;
        Assert.NotNull(bedrockAgentSettings);

        return new()
        {
            AgentName = $"{AgentName}-{Guid.NewGuid():n}",
            Description = AgentDescription,
            Instruction = AgentInstruction,
            AgentResourceRoleArn = bedrockAgentSettings.AgentResourceRoleArn,
            FoundationModel = bedrockAgentSettings.FoundationModel,
        };
    }
}
