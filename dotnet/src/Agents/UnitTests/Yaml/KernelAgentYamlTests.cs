// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Azure.AI.Projects;
using Azure.Core.Pipeline;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.Agents.OpenAI;
using SemanticKernel.Agents.UnitTests.AzureAI.Definition;
using SemanticKernel.Agents.UnitTests.OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Yaml;

/// <summary>
/// Unit tests for <see cref="KernelAgentYaml"/>.
/// </summary>
public class KernelAgentYamlTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Kernel _kernel;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgentTests"/> class.
    /// </summary>
    public KernelAgentYamlTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, disposeHandler: false);

        var builder = Kernel.CreateBuilder();

        // Add OpenAI client provider
        builder.Services.AddSingleton<OpenAIClientProvider>(OpenAIClientProvider.ForOpenAI(apiKey: new ApiKeyCredential("fakekey"), endpoint: null, this._httpClient));

        // Add Azure AI client provider
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
    /// Verify can create an instance of <see cref="KernelAgent"/> using <see cref="ChatCompletionAgentFactory"/>
    /// </summary>
    [Fact]
    public async Task VerifyCanCreateChatCompletionAgentAsync()
    {
        // Arrange
        var text =
            """
            type: chat_completion_agent
            name: ChatCompletionAgent
            description: ChatCompletionAgent Description
            instructions: ChatCompletionAgent Instructions
            model:
              id: gpt-4o-mini
              options:
                temperature: 0.4
                function_choice_behavior:
                  type: auto
            """;
        ChatCompletionAgentFactory factory = new();

        // Act
        var agent = await KernelAgentYaml.FromAgentYamlAsync(this._kernel, text, factory);

        // Assert
        Assert.NotNull(agent);
        Assert.True(agent is ChatCompletionAgent);
        Assert.Equal("ChatCompletionAgent", agent.Name);
        Assert.Equal("ChatCompletionAgent Description", agent.Description);
        Assert.Equal("ChatCompletionAgent Instructions", agent.Instructions);
        Assert.Equal(this._kernel, agent.Kernel);
    }

    /// <summary>
    /// Verify can create an instance of <see cref="KernelAgent"/> using <see cref="OpenAIAssistantAgentFactory"/>
    /// </summary>
    [Fact]
    public async Task VerifyCanCreateOpenAIAssistantAsync()
    {
        // Arrange
        var text =
            """
            type: openai_assistant
            name: OpenAIAssistantAgent
            description: OpenAIAssistantAgent Description
            instructions: OpenAIAssistantAgent Instructions
            model:
              id: gpt-4o-mini
            tools:
                - name: tool1
                  type: code_interpreter
            """;
        OpenAIAssistantAgentFactory factory = new();
        this.SetupResponse(HttpStatusCode.OK, KernelAgentYaml.ToAgentDefinition(text).GetOpenAIAssistantDefinition());

        // Act
        var agent = await KernelAgentYaml.FromAgentYamlAsync(this._kernel, text, factory);

        // Assert
        Assert.NotNull(agent);
        Assert.True(agent is OpenAIAssistantAgent);
        Assert.Equal("OpenAIAssistantAgent", agent.Name);
        Assert.Equal("OpenAIAssistantAgent Description", agent.Description);
        Assert.Equal("OpenAIAssistantAgent Instructions", agent.Instructions);
        Assert.Equal(this._kernel, agent.Kernel);
    }

    /// <summary>
    /// Verify can create an instance of <see cref="KernelAgent"/> using <see cref="AzureAIAgentFactory"/>
    /// </summary>
    [Fact]
    public async Task VerifyCanCreateAzureAIAgentAsync()
    {
        // Arrange
        var text =
            """
            type: azureai_agent
            name: AzureAIAgent
            description: AzureAIAgent Description
            instructions: AzureAIAgent Instructions
            model:
              id: gpt-4o-mini
            tools:
                - name: tool1
                  type: code_interpreter
            """;
        AzureAIAgentFactory factory = new();
        this.SetupResponse(HttpStatusCode.OK, AzureAIAgentFactoryTests.AzureAIAgentResponse);

        // Act
        var agent = await KernelAgentYaml.FromAgentYamlAsync(this._kernel, text, factory);

        // Assert
        Assert.NotNull(agent);
        Assert.True(agent is AzureAIAgent);
        Assert.Equal("AzureAIAgent", agent.Name);
        Assert.Equal("AzureAIAgent Description", agent.Description);
        Assert.Equal("AzureAIAgent Instructions", agent.Instructions);
        Assert.Equal(this._kernel, agent.Kernel);
    }

    #region private
    private void SetupResponse(HttpStatusCode statusCode, OpenAIAssistantDefinition definition) =>
        this._messageHandlerStub.SetupResponses(statusCode, OpenAIAssistantResponseContent.AssistantDefinition(definition));

    private void SetupResponse(HttpStatusCode statusCode, string response) =>
#pragma warning disable CA2000 // Dispose objects before losing scope
        this._messageHandlerStub.ResponseQueue.Enqueue(new(statusCode)
        {
            Content = new StringContent(response)
        });
    #endregion
}
