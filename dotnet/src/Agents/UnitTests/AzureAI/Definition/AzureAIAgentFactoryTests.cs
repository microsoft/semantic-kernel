// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.Projects;
using Azure.Core;
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
        builder.Services.AddSingleton<AzureAIClientProvider>(AzureAIClientProvider.FromClient(client));
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
    /// Verify can create an instance of <see cref="KernelAgent"/> using <see cref="OpenAIAssistantAgentFactory"/>
    /// </summary>
    [Fact]
    public async Task VerifyCanCreateOpenAIAssistantAsync()
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
                new Microsoft.SemanticKernel.Agents.ToolDefinition()
                {
                    Name = "tool1",
                    Type = Microsoft.SemanticKernel.Agents.ToolDefinition.CodeInterpreter,
                },
            ]
        };
        AzureAIAgentFactory factory = new();
        //this.SetupResponse(HttpStatusCode.OK, agentDefinition.GetOpenAIAssistantDefinition());

        // Act
        var agent = await factory.CreateAsync(this._kernel, agentDefinition);

        // Assert
        Assert.NotNull(agent);
        Assert.Equal(agentDefinition.Name, agent.Name);
        Assert.Equal(agentDefinition.Description, agent.Description);
        Assert.Equal(agentDefinition.Instructions, agent.Instructions);
        Assert.Equal(this._kernel, agent.Kernel);
    }


    #region private
    private class FakeTokenCredential : TokenCredential
    {
        /// <inheritdoc/>
        public override AccessToken GetToken(TokenRequestContext requestContext, CancellationToken cancellationToken)
        {
            return new AccessToken("fakeToken", DateTimeOffset.Now.AddHours(1));
        }

        /// <inheritdoc/>
        public override ValueTask<AccessToken> GetTokenAsync(TokenRequestContext requestContext, CancellationToken cancellationToken)
        {
            return new ValueTask<AccessToken>(new AccessToken("fakeToken", DateTimeOffset.Now.AddHours(1)));
        }
    }
    #endregion
}
