// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Azure.AI.Projects;
using Azure.Core.Pipeline;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using SemanticKernel.Agents.UnitTests.AzureAI.Definition;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Yaml;

/// <summary>
/// Unit tests for <see cref="KernelAgentFactoryYamlExtensions"/> with <see cref="AzureAIAgentFactory"/>.
/// </summary>
public class AzureAIKernelAgentYamlTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Kernel _kernel;

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAIKernelAgentYamlTests"/> class.
    /// </summary>
    public AzureAIKernelAgentYamlTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, disposeHandler: false);

        var builder = Kernel.CreateBuilder();

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
    /// Verify the request includes a tool of the specified when creating an Azure AI agent.
    /// </summary>
    [Theory]
    [InlineData("code_interpreter")]
    [InlineData("azure_aisearch")]
    public async Task VerifyRequestIncludesToolAsync(string type)
    {
        // Arrange
        var text =
            $"""
            type: azureai_agent
            name: AzureAIAgent
            description: AzureAIAgent Description
            instructions: AzureAIAgent Instructions
            model:
              id: gpt-4o-mini
            tools:
                - type: {type}
            """;
        AzureAIAgentFactory factory = new();
        this.SetupResponse(HttpStatusCode.OK, AzureAIAgentFactoryTests.AzureAIAgentResponse);

        // Act
        var agent = await factory.CreateAgentFromYamlAsync(this._kernel, text);

        // Assert
        Assert.NotNull(agent);
        var requestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(requestContent);
        var requestJson = JsonSerializer.Deserialize<JsonElement>(requestContent);
        Assert.Equal(1, requestJson.GetProperty("tools").GetArrayLength());
        Assert.Equal(type, requestJson.GetProperty("tools")[0].GetProperty("type").GetString());
    }

    /// <summary>
    /// Verify the request includes an Azure Function tool when creating an Azure AI agent.
    /// </summary>
    [Fact]
    public async Task VerifyRequestIncludesAzureFunctionAsync()
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
                - type: azure_function
                  name: function1
                  description: function1 description
                  input_binding:
                      storage_service_endpoint: https://storage_service_endpoint
                      queue_name: queue_name
                  output_binding:
                      storage_service_endpoint: https://storage_service_endpoint
                      queue_name: queue_name
                  parameters:
                      - name: param1
                        type: string
                        description: param1 description
                      - name: param2
                        type: string
                        description: param2 description
            """;
        AzureAIAgentFactory factory = new();
        this.SetupResponse(HttpStatusCode.OK, AzureAIAgentFactoryTests.AzureAIAgentResponse);

        // Act
        var agent = await factory.CreateAgentFromYamlAsync(this._kernel, text);

        // Assert
        Assert.NotNull(agent);
        var requestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(requestContent);
        var requestJson = JsonSerializer.Deserialize<JsonElement>(requestContent);
        Assert.Equal(1, requestJson.GetProperty("tools").GetArrayLength());
        Assert.Equal("azure_function", requestJson.GetProperty("tools")[0].GetProperty("type").GetString());
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
