// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
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
/// Unit tests for <see cref="YamlAgentFactoryExtensions"/> with <see cref="AzureAIAgentFactory"/>.
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
        this._kernel.Plugins.Add(KernelPluginFactory.CreateFromType<WeatherPlugin>());
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
    [InlineData("azure_ai_search")]
    public async Task VerifyRequestIncludesToolAsync(string type)
    {
        // Arrange
        var text =
            $"""
            type: foundry_agent
            name: FoundryAgent
            description: AzureAIAgent Description
            instructions: AzureAIAgent Instructions
            model:
              id: gpt-4o-mini
            tools:
                - type: {type}
            """;
        AzureAIAgentFactory factory = new();
        this.SetupResponse(HttpStatusCode.OK, AzureAIAgentFactoryTests.AzureAIAgentCreateResponse);

        // Act
        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = this._kernel });

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
            type: foundry_agent
            name: FoundryAgent
            description: AzureAIAgent Description
            instructions: AzureAIAgent Instructions
            model:
              id: gpt-4o-mini
            tools:
                - type: azure_function
                  id: function1
                  description: function1 description
                  options:
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
        this.SetupResponse(HttpStatusCode.OK, AzureAIAgentFactoryTests.AzureAIAgentCreateResponse);

        // Act
        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(agent);
        var requestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(requestContent);
        var requestJson = JsonSerializer.Deserialize<JsonElement>(requestContent);
        Assert.Equal(1, requestJson.GetProperty("tools").GetArrayLength());
        Assert.Equal("azure_function", requestJson.GetProperty("tools")[0].GetProperty("type").GetString());
    }

    /// <summary>
    /// Verify the request includes a Function when creating an Azure AI agent.
    /// </summary>
    [Fact]
    public async Task VerifyRequestIncludesFunctionAsync()
    {
        // Arrange
        var text =
            """
            type: foundry_agent
            name: FoundryAgent
            description: AzureAIAgent Description
            instructions: AzureAIAgent Instructions
            model:
              id: gpt-4o-mini
            tools:
                - type: function
                  id: WeatherPlugin.Current
                  description: Provides real-time weather information.
                  options:
                      parameters:
                          - name: location
                            type: string
                            description: The location to get the weather for.
            """;
        AzureAIAgentFactory factory = new();
        this.SetupResponse(HttpStatusCode.OK, AzureAIAgentFactoryTests.AzureAIAgentCreateResponse);

        // Act
        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(agent);
        var requestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(requestContent);
        var requestJson = JsonSerializer.Deserialize<JsonElement>(requestContent);
        Assert.Equal(1, requestJson.GetProperty("tools").GetArrayLength());
        Assert.Equal("function", requestJson.GetProperty("tools")[0].GetProperty("type").GetString());
    }

    /// <summary>
    /// Verify the request includes a Bing Grounding tool when creating an Azure AI agent.
    /// </summary>
    [Fact]
    public async Task VerifyRequestIncludesBingGroundingAsync()
    {
        // Arrange
        var text =
            """
            type: foundry_agent
            name: FoundryAgent
            description: AzureAIAgent Description
            instructions: AzureAIAgent Instructions
            model:
              id: gpt-4o-mini
            tools:
                - type: bing_grounding
                  options:
                    tool_connections:
                      - connection_string
            """;
        AzureAIAgentFactory factory = new();
        this.SetupResponse(HttpStatusCode.OK, AzureAIAgentFactoryTests.AzureAIAgentCreateResponse);

        // Act
        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(agent);
        var requestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(requestContent);
        var requestJson = JsonSerializer.Deserialize<JsonElement>(requestContent);
        Assert.Equal(1, requestJson.GetProperty("tools").GetArrayLength());
        Assert.Equal("bing_grounding", requestJson.GetProperty("tools")[0].GetProperty("type").GetString());
    }

    /// <summary>
    /// Verify the request includes a Microsoft Fabric tool when creating an Azure AI agent.
    /// </summary>
    [Fact]
    public async Task VerifyRequestIncludesMicrosoftFabricAsync()
    {
        // Arrange
        var text =
            """
            type: foundry_agent
            name: FoundryAgent
            description: AzureAIAgent Description
            instructions: AzureAIAgent Instructions
            model:
              id: gpt-4o-mini
            tools:
                - type: fabric_aiskill
                  options:
                      tool_connections:
                        - connection_string
            """;
        AzureAIAgentFactory factory = new();
        this.SetupResponse(HttpStatusCode.OK, AzureAIAgentFactoryTests.AzureAIAgentCreateResponse);

        // Act
        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(agent);
        var requestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(requestContent);
        var requestJson = JsonSerializer.Deserialize<JsonElement>(requestContent);
        Assert.Equal(1, requestJson.GetProperty("tools").GetArrayLength());
        Assert.Equal("fabric_dataagent", requestJson.GetProperty("tools")[0].GetProperty("type").GetString());
    }

    /// <summary>
    /// Verify the request includes a Open API tool when creating an Azure AI agent.
    /// </summary>
    [Fact]
    public async Task VerifyRequestIncludesOpenAPIAsync()
    {
        // Arrange
        var text =
            """
            type: foundry_agent
            name: FoundryAgent
            description: AzureAIAgent Description
            instructions: AzureAIAgent Instructions
            model:
              id: gpt-4o-mini
            tools:
                - type: openapi
                  id: function1
                  description: function1 description
                  options:
                    specification: {"openapi":"3.1.0","info":{"title":"Get Weather Data","description":"Retrieves current weather data for a location based on wttr.in.","version":"v1.0.0"},"servers":[{"url":"https://wttr.in"}],"auth":[],"paths":{"/{location}":{"get":{"description":"Get weather information for a specific location","operationId":"GetCurrentWeather","parameters":[{"name":"location","in":"path","description":"City or location to retrieve the weather for","required":true,"schema":{"type":"string"}},{"name":"format","in":"query","description":"Always use j1 value for this parameter","required":true,"schema":{"type":"string","default":"j1"}}],"responses":{"200":{"description":"Successful response","content":{"text/plain":{"schema":{"type":"string"}}}},"404":{"description":"Location not found"}},"deprecated":false}}},"components":{"schemes":{}}}
                - type: openapi
                  id: function2
                  description: function2 description
                  options:
                      specification: {"openapi":"3.1.0","info":{"title":"Get Weather Data","description":"Retrieves current weather data for a location based on wttr.in.","version":"v1.0.0"},"servers":[{"url":"https://wttr.in"}],"auth":[],"paths":{"/{location}":{"get":{"description":"Get weather information for a specific location","operationId":"GetCurrentWeather","parameters":[{"name":"location","in":"path","description":"City or location to retrieve the weather for","required":true,"schema":{"type":"string"}},{"name":"format","in":"query","description":"Always use j1 value for this parameter","required":true,"schema":{"type":"string","default":"j1"}}],"responses":{"200":{"description":"Successful response","content":{"text/plain":{"schema":{"type":"string"}}}},"404":{"description":"Location not found"}},"deprecated":false}}},"components":{"schemes":{}}}
                      authentication:
                          connection_id: connection_id
                - type: openapi
                  id: function3
                  description: function3 description
                  options:
                      specification: {"openapi":"3.1.0","info":{"title":"Get Weather Data","description":"Retrieves current weather data for a location based on wttr.in.","version":"v1.0.0"},"servers":[{"url":"https://wttr.in"}],"auth":[],"paths":{"/{location}":{"get":{"description":"Get weather information for a specific location","operationId":"GetCurrentWeather","parameters":[{"name":"location","in":"path","description":"City or location to retrieve the weather for","required":true,"schema":{"type":"string"}},{"name":"format","in":"query","description":"Always use j1 value for this parameter","required":true,"schema":{"type":"string","default":"j1"}}],"responses":{"200":{"description":"Successful response","content":{"text/plain":{"schema":{"type":"string"}}}},"404":{"description":"Location not found"}},"deprecated":false}}},"components":{"schemes":{}}}
                      authentication:
                          audience: audience
            """;
        AzureAIAgentFactory factory = new();
        this.SetupResponse(HttpStatusCode.OK, AzureAIAgentFactoryTests.AzureAIAgentCreateResponse);

        // Act
        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(agent);
        var requestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(requestContent);
        var requestJson = JsonSerializer.Deserialize<JsonElement>(requestContent);
        Assert.Equal(3, requestJson.GetProperty("tools").GetArrayLength());
        Assert.Equal("openapi", requestJson.GetProperty("tools")[0].GetProperty("type").GetString());
        Assert.Equal("openapi", requestJson.GetProperty("tools")[1].GetProperty("type").GetString());
        Assert.Equal("openapi", requestJson.GetProperty("tools")[2].GetProperty("type").GetString());
    }

    /// <summary>
    /// Verify the request includes a Sharepoint tool when creating an Azure AI agent.
    /// </summary>
    [Fact]
    public async Task VerifyRequestIncludesSharepointGroundingAsync()
    {
        // Arrange
        var text =
            """
            type: foundry_agent
            name: FoundryAgent
            description: AzureAIAgent Description
            instructions: AzureAIAgent Instructions
            model:
              id: gpt-4o-mini
            tools:
                - type: sharepoint_grounding
                  options:
                    tool_connections:
                        - connection_string
            """;
        AzureAIAgentFactory factory = new();
        this.SetupResponse(HttpStatusCode.OK, AzureAIAgentFactoryTests.AzureAIAgentCreateResponse);

        // Act
        var agent = await factory.CreateAgentFromYamlAsync(text, new() { Kernel = this._kernel });

        // Assert
        Assert.NotNull(agent);
        var requestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent!);
        Assert.NotNull(requestContent);
        var requestJson = JsonSerializer.Deserialize<JsonElement>(requestContent);
        Assert.Equal(1, requestJson.GetProperty("tools").GetArrayLength());
        Assert.Equal("sharepoint_grounding", requestJson.GetProperty("tools")[0].GetProperty("type").GetString());
    }

    #region private
    private void SetupResponse(HttpStatusCode statusCode, string response) =>
        this._messageHandlerStub.ResponseToReturn =
            new HttpResponseMessage(statusCode)
            {
                Content = new StringContent(response)
            };

    private sealed class WeatherPlugin
    {
        [KernelFunction, Description("Provides real-time weather information.")]
        public string Current([Description("The location to get the weather for.")] string location)
        {
            return $"The current weather in {location} is 72 degrees.";
        }

        [KernelFunction, Description("Forecast weather information.")]
        public string Forecast([Description("The location to get the weather for.")] string location)
        {
            return $"The forecast for {location} is 75 degrees tomorrow.";
        }
    }
    #endregion
}
