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
using OpenAI;
using SemanticKernel.Agents.UnitTests.AzureAI.Definition;
using SemanticKernel.Agents.UnitTests.OpenAI;
using SemanticKernel.Agents.UnitTests.OpenAI.Definition;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Yaml;

/// <summary>
/// Unit tests for <see cref="YamlAgentFactoryExtensions"/>.
/// </summary>
public class AgentYamlTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Kernel _kernel;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgentTests"/> class.
    /// </summary>
    public AgentYamlTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, disposeHandler: false);

        var builder = Kernel.CreateBuilder();

        // Add OpenAI client
        OpenAIClientOptions clientOptions = OpenAIClientProvider.CreateOpenAIClientOptions(endpoint: null, httpClient: this._httpClient);
        OpenAIClient openAIClient = new(new ApiKeyCredential("fakekey"), clientOptions);
        builder.Services.AddSingleton<OpenAIClient>(openAIClient);

        // Add Azure AI agents client
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
    /// Verify can create an instance of <see cref="AgentDefinition"/> from YAML text.
    /// </summary>
    [Fact]
    public void VerifyAgentDefinitionFromYaml()
    {
        // Arrange
        var text =
            """
            version: 1.0.0
            type: chat_completion_agent
            name: ChatCompletionAgent
            description: ChatCompletionAgent Description
            instructions: ChatCompletionAgent Instructions
            metadata:
                author: Microsoft
                created: 2025-02-21
            model:
                id: gpt-4o-mini
                options:
                    temperature: 0.4
                    function_choice_behavior:
                        type: auto
                connection:
                    type: azureai
            inputs:
                input1:
                    description: input1 description
                    required: true
                    default: input1 default
                    sample: input1 sample
                input2:
                    description: input2 description
                    required: false
                    default: input2 default
                    sample: input2 sample
            outputs:
                output1:
                    description: output1 description
            template:
                format: liquid
                parser: semantic-kernel
            tools:
                - id: tool1
                  type: code_interpreter
                - id: tool2
                  type: file_search
            """;

        // Act
        var agentDefinition = AgentDefinitionYaml.FromYaml(text);

        // Assert
        Assert.NotNull(agentDefinition);
    }

    /// <summary>
    /// Verify can create an instance of <see cref="Microsoft.SemanticKernel.Agents.Agent"/> using <see cref="ChatCompletionAgentFactory"/>
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
        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(agent);
        Assert.True(agent is ChatCompletionAgent);
        Assert.Equal("ChatCompletionAgent", agent.Name);
        Assert.Equal("ChatCompletionAgent Description", agent.Description);
        Assert.Equal("ChatCompletionAgent Instructions", agent.Instructions);
        Assert.Equal(this._kernel, agent.Kernel);
    }

    /// <summary>
    /// Verify can create an instance of <see cref="Microsoft.SemanticKernel.Agents.Agent"/> using <see cref="OpenAIAssistantAgentFactory"/>
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
                - id: tool1
                  type: code_interpreter
            """;
        OpenAIAssistantAgentFactory factory = new();
        this.SetupResponse(HttpStatusCode.OK, OpenAIAssistantAgentFactoryTests.OpenAIAssistantCreateResponse);

        // Act
        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(agent);
        Assert.True(agent is OpenAIAssistantAgent);
        Assert.Equal("OpenAIAssistantAgent", agent.Name);
        Assert.Equal("OpenAIAssistantAgent Description", agent.Description);
        Assert.Equal("OpenAIAssistantAgent Instructions", agent.Instructions);
        Assert.Equal(this._kernel, agent.Kernel);
    }

    /// <summary>
    /// Verify can create an instance of <see cref="Microsoft.SemanticKernel.Agents.Agent"/> using <see cref="AzureAIAgentFactory"/>
    /// </summary>
    [Fact]
    public async Task VerifyCanCreateAzureAIAgentAsync()
    {
        // Arrange
        var text =
            """
            type: foundry_agent
            name: AzureAIAgent
            description: AzureAIAgent Description
            instructions: AzureAIAgent Instructions
            model:
              id: gpt-4o-mini
            tools:
                - id: tool1
                  type: code_interpreter
            """;
        AzureAIAgentFactory factory = new();
        this.SetupResponse(HttpStatusCode.OK, AzureAIAgentFactoryTests.AzureAIAgentCreateResponse);

        // Act
        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(agent);
        Assert.True(agent is AzureAIAgent);
        Assert.Equal("AzureAIAgent", agent.Name);
        Assert.Equal("AzureAIAgent Description", agent.Description);
        Assert.Equal("AzureAIAgent Instructions", agent.Instructions);
        Assert.Equal(this._kernel, agent.Kernel);
    }

    #region private
    private void SetupResponse(HttpStatusCode statusCode, string response) =>
#pragma warning disable CA2000 // Dispose objects before losing scope
        this._messageHandlerStub.ResponseQueue.Enqueue(new(statusCode)
        {
            Content = new StringContent(response)
        });
    #endregion
}
