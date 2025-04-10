﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI.Definition;

/// <summary>
/// Unit tests for <see cref="OpenAIAssistantAgentFactory"/>.
/// </summary>
public class OpenAIAssistantAgentFactoryTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Kernel _kernel;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgentTests"/> class.
    /// </summary>
    public OpenAIAssistantAgentFactoryTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, disposeHandler: false);

        OpenAIClientOptions clientOptions = OpenAIClientProvider.CreateOpenAIClientOptions(endpoint: null, httpClient: this._httpClient);
        OpenAIClient openAIClient = new(new ApiKeyCredential("fakekey"), clientOptions);

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<OpenAIClient>(openAIClient);
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
    /// Verify can create an instance of <see cref="Agent"/> using <see cref="OpenAIAssistantAgentFactory"/>
    /// </summary>
    [Fact]
    public async Task VerifyCanCreateOpenAIAssistantAsync()
    {
        // Arrange
        AgentDefinition agentDefinition = new()
        {
            Type = OpenAIAssistantAgentFactory.OpenAIAssistantAgentType,
            Name = "OpenAIAssistantAgent",
            Description = "OpenAIAssistantAgent Description",
            Instructions = "OpenAIAssistantAgent Instructions",
            Model = new()
            {
                Id = "gpt-4o-mini"
            },
            Tools = [
                new AgentToolDefinition()
                {
                    Id = "tool1",
                    Type = "code_interpreter",
                },
            ]
        };
        OpenAIAssistantAgentFactory factory = new();
        this.SetupResponse(HttpStatusCode.OK, OpenAIAssistantResponse);

        // Act
        var agent = await factory.CreateAsync(this._kernel, agentDefinition);

        // Assert
        Assert.NotNull(agent);
        Assert.Equal(agentDefinition.Name, agent.Name);
        Assert.Equal(agentDefinition.Description, agent.Description);
        Assert.Equal(agentDefinition.Instructions, agent.Instructions);
        Assert.Equal(this._kernel, agent.Kernel);
    }

    /// <summary>
    /// OpenAI Assistant response.
    /// </summary>
    public const string OpenAIAssistantResponse =
        """
        {
          "id": "asst_z2BnUzSnnZ4QimeUCsVSdAug",
          "object": "assistant",
          "created_at": 1740137107,
          "name": "OpenAIAssistantAgent",
          "description": "OpenAIAssistantAgent Description",
          "model": "gpt-4o",
          "instructions": "OpenAIAssistantAgent Instructions",
          "tools": [
            {
              "type": "code_interpreter"
            }
          ],
          "top_p": 1.0,
          "temperature": 1.0,
          "reasoning_effort": null,
          "tool_resources": {
            "code_interpreter": {
              "file_ids": []
            }
          },
          "metadata": {},
          "response_format": "auto"
        }
        """;

    #region private
    private void SetupResponse(HttpStatusCode statusCode, string response) =>
        this._messageHandlerStub.SetupResponses(statusCode, [response]);
    #endregion
}
