// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Azure.AI.Projects;
using Azure.Core.Pipeline;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.AzureAI.Definition;

/// <summary>
/// Unit tests for <see cref="AzureAIAgentFactory"/>.
/// </summary>
public class AzureAIAgentFactoryTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Kernel _kernel;

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAIAgentFactoryTests"/> class.
    /// </summary>
    public AzureAIAgentFactoryTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, disposeHandler: false);

        var builder = Kernel.CreateBuilder();
        var client = new AIProjectClient(
            "endpoint;subscription_id;resource_group_name;project_name",
            new FakeTokenCredential(),
            new AIProjectClientOptions()
            { Transport = new HttpClientTransport(this._httpClient) });
        builder.Services.AddSingleton<AIProjectClient>(client);
        this._kernel = builder.Build();
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        GC.SuppressFinalize(this);
        this._messageHandlerStub.Dispose();
        this._httpClient.Dispose();
    }

    /// <summary>
    /// Verify can create an instance of <see cref="Microsoft.SemanticKernel.Agents.Agent"/> using <see cref="AzureAIAgentFactory"/>
    /// </summary>
    [Fact]
    public async Task VerifyCanCreateAzureAIAgentAsync()
    {
        // Arrange
        AgentDefinition agentDefinition = new()
        {
            Type = AzureAIAgentFactory.AzureAIAgentType,
            Name = "AzureAIAgent",
            Description = "AzureAIAgent Description",
            Instructions = "AzureAIAgent Instructions",
            Model = new()
            {
                Id = "gpt-4o-mini"
            },
            Tools = [
                new Microsoft.SemanticKernel.Agents.AgentToolDefinition()
                {
                    Id = "tool1",
                    Type = "code_interpreter",
                },
            ]
        };
        AzureAIAgentFactory factory = new();
        using var responseMessage = this.SetupResponse(HttpStatusCode.OK, AzureAIAgentCreateResponse);

        // Act
        var agent = await factory.CreateAsync(this._kernel, agentDefinition);

        // Assert
        Assert.NotNull(agent);
        Assert.Equal("asst_thdyqg4yVC9ffeILVdEWLONT", agent.Id);
        Assert.Equal(agentDefinition.Name, agent.Name);
        Assert.Equal(agentDefinition.Description, agent.Description);
        Assert.Equal(agentDefinition.Instructions, agent.Instructions);
        Assert.Equal(this._kernel, agent.Kernel);
    }

    /// <summary>
    /// Verify can create an instance of <see cref="Microsoft.SemanticKernel.Agents.Agent"/> using <see cref="AzureAIAgentFactory"/>
    /// </summary>
    [Fact]
    public async Task VerifyCanGetAzureAIAgentAsync()
    {
        // Arrange
        AgentDefinition agentDefinition = new()
        {
            Id = "asst_oKtAcmYQCtTj95BxpvL1RQBP",
            Type = AzureAIAgentFactory.AzureAIAgentType,
        };
        AzureAIAgentFactory factory = new();
        using var responseMessage = this.SetupResponse(HttpStatusCode.OK, AzureAIAgentGetResponse);

        // Act
        var agent = await factory.CreateAsync(this._kernel, agentDefinition);

        // Assert
        Assert.NotNull(agent);
        Assert.Equal("asst_oKtAcmYQCtTj95BxpvL1RQBP", agent.Id);
        Assert.Equal("HelpfulAssistant", agent.Name);
        Assert.Equal("Helpful Assistant", agent.Description);
        Assert.Equal("You are a helpful assistant.", agent.Instructions);
        Assert.Equal(this._kernel, agent.Kernel);
    }

    /// <summary>
    /// Azure AI Agent create response.
    /// </summary>
    public const string AzureAIAgentCreateResponse =
        """
        {
          "id": "asst_thdyqg4yVC9ffeILVdEWLONT",
          "object": "assistant",
          "created_at": 1739991984,
          "name": "AzureAIAgent",
          "description": "AzureAIAgent Description",
          "model": "gpt-4o",
          "instructions": "AzureAIAgent Instructions",
          "tools": [],
          "top_p": 1.0,
          "temperature": 1.0,
          "tool_resources": {},
          "metadata": {},
          "response_format": "auto"
        }
        """;

    /// <summary>
    /// Azure AI Agent get response.
    /// </summary>
    public const string AzureAIAgentGetResponse =
        """
        {
          "id": "asst_oKtAcmYQCtTj95BxpvL1RQBP",
          "object": "assistant",
          "created_at": 1744215200,
          "name": "HelpfulAssistant",
          "description": "Helpful Assistant",
          "model": "gpt-4o-mini",
          "instructions": "You are a helpful assistant.",
          "tools": [],
          "top_p": 1.0,
          "temperature": 1.0,
          "tool_resources": {},
          "metadata": {},
          "response_format": "auto"
        }
        """;

    #region private
    private HttpResponseMessage SetupResponse(HttpStatusCode statusCode, string response)
    {
        var responseMessage = new HttpResponseMessage(statusCode)
        {
            Content = new StringContent(response)
        };

        this._messageHandlerStub.ResponseQueue.Enqueue(responseMessage);

        return responseMessage;
    }
    #endregion
}
