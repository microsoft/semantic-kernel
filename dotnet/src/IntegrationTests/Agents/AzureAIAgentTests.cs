// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Azure.AI.Projects;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance;
using SemanticKernel.IntegrationTests.TestSettings;
using xRetry;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents;

public class AzureAIAgentTests
{
    private readonly Kernel _kernel;
    private readonly AzureAIConfiguration _configuration;
    private readonly AIProjectClient _client;
    private readonly AgentsClient _agentsClient;

    public AzureAIAgentTests()
    {
        var kernelBuilder = Kernel.CreateBuilder();
        this._kernel = kernelBuilder.Build();
        this._configuration = this.ReadAzureConfiguration();
        this._client = AzureAIAgent.CreateAzureAIClient(this._configuration.ConnectionString!, new AzureCliCredential());
        this._agentsClient = this._client.GetAgentsClient();
    }

    /// <summary>
    /// Integration test for <see cref="AzureAIAgent"/> adding override instructions to a thread on invocation via custom options.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task OpenAIAgentWithThreadCustomOptionsAsync()
    {
        var aiAgent =
            await this._agentsClient.CreateAgentAsync(
                this._configuration.ChatModelId,
                name: "HelpfulAssistant",
                description: "Helpful Assistant",
                instructions: "You are a helpful assistant.");
        var agent = new AzureAIAgent(aiAgent, this._agentsClient) { Kernel = this._kernel };

        AzureAIAgentThread agentThread = new(this._agentsClient);

        try
        {
            var message = new ChatMessageContent(AuthorRole.User, "What is the capital of France?");
            var responseMessages = await agent.InvokeAsync(
                message,
                agentThread,
                new AzureAIAgentInvokeOptions() { OverrideInstructions = "Respond to all user questions with 'Computer says no'." }).ToArrayAsync();

            Assert.Single(responseMessages);
            Assert.Contains("Computer says no", responseMessages[0].Message.Content);
        }
        finally
        {
            await agentThread.DeleteAsync();
            await this._agentsClient.DeleteAgentAsync(agent.Id);
        }
    }

    /// <summary>
    /// Integration test for <see cref="AzureAIAgent"/> adding override instructions to a thread on invocation via custom options.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task OpenAIAgentWithThreadCustomOptionsStreamingAsync()
    {
        var aiAgent =
            await this._agentsClient.CreateAgentAsync(
                this._configuration.ChatModelId,
                name: "HelpfulAssistant",
                description: "Helpful Assistant",
                instructions: "You are a helpful assistant.");
        var agent = new AzureAIAgent(aiAgent, this._agentsClient) { Kernel = this._kernel };

        AzureAIAgentThread agentThread = new(this._agentsClient);

        try
        {
            var message = new ChatMessageContent(AuthorRole.User, "What is the capital of France?");
            var responseMessages = await agent.InvokeStreamingAsync(
                message,
                agentThread,
                new AzureAIAgentInvokeOptions() { OverrideInstructions = "Respond to all user questions with 'Computer says no'." }).ToArrayAsync();
            var responseText = string.Join(string.Empty, responseMessages.Select(x => x.Message.Content));

            Assert.Contains("Computer says no", responseText);
        }
        finally
        {
            await agentThread.DeleteAsync();
            await this._agentsClient.DeleteAgentAsync(agent.Id);
        }
    }

    private AzureAIConfiguration ReadAzureConfiguration()
    {
        IConfigurationRoot configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<AzureAIAgentFixture>()
            .Build();

        return configuration.GetSection("AzureAI").Get<AzureAIConfiguration>()!;
    }
}
