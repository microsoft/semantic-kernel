// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Plugins;

namespace GettingStarted.AzureAgents;

/// <summary>
/// This example demonstrates how to declaratively create instances of <see cref="AzureAIAgent"/>.
/// </summary>
public class Step08_AzureAIAgent_Declarative : BaseAzureAgentTest
{
    public Step08_AzureAIAgent_Declarative(ITestOutputHelper output) : base(output)
    {
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<AIProjectClient>(this.Client);
        this._kernel = builder.Build();
    }

    [Fact]
    public async Task AzureAIAgentWithConfigurationAsync()
    {
        var text =
            $"""
            type: foundry_agent
            name: StoryAgent
            description: Store Telling Agent
            instructions: Tell a story suitable for children about the topic provided by the user.
            model:
              id: gpt-4o-mini
              connection:
                connection_string: {TestConfiguration.AzureAI.ConnectionString}
            """;
        AzureAIAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text);

        await InvokeAgentAsync(agent!, "Cats and Dogs");
    }

    [Fact]
    public async Task AzureAIAgentWithKernelAsync()
    {
        var text =
            """
            type: foundry_agent
            name: StoryAgent
            description: Store Telling Agent
            instructions: Tell a story suitable for children about the topic provided by the user.
            model:
              id: gpt-4o-mini
            """;
        AzureAIAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel);

        await InvokeAgentAsync(agent!, "Cats and Dogs");
    }

    [Fact]
    public async Task AzureAIAgentWithCodeInterpreterAsync()
    {
        var text =
            """
            type: foundry_agent
            name: CodeInterpreterAgent
            instructions: Use the code interpreter tool to answer questions which require code to be generated and executed.
            description: Agent with code interpreter tool.
            model:
              id: gpt-4o-mini
            tools:
              - type: code_interpreter
            """;
        AzureAIAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel);

        await InvokeAgentAsync(agent!, "Use code to determine the values in the Fibonacci sequence that that are less then the value of 101?");
    }

    [Fact]
    public async Task AzureAIAgentWithFunctionsAsync()
    {
        var text =
            """
            type: foundry_agent
            name: FunctionCallingAgent
            instructions: Use the provided functions to answer questions about the menu.
            description: This agent uses the provided functions to answer questions about the menu.
            model:
              id: gpt-4o-mini
              options:
                temperature: 0.4
            tools:
              - id: GetSpecials
                type: function
                description: Get the specials from the menu.
              - id: GetItemPrice
                type: function
                description: Get the price of an item on the menu.
                options:
                  parameters:
                    - name: menuItem
                      type: string
                      required: true
                      description: The name of the menu item.  
            """;
        AzureAIAgentFactory factory = new();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        this._kernel.Plugins.Add(plugin);

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel);

        await InvokeAgentAsync(agent!, "What is the special soup and how much does it cost?");
    }

    [Fact]
    public async Task AzureAIAgentWithBingGroundingAsync()
    {
        var text =
            $"""
            type: foundry_agent
            name: BingAgent
            instructions: Answer questions using Bing to provide grounding context.
            description: This agent answers questions using Bing to provide grounding context.
            model:
              id: gpt-4o
              options:
                temperature: 0.4
            tools:
              - type: bing_grounding
                options:
                  tool_connections:
                    - {TestConfiguration.AzureAI.BingConnectionId}
            """;
        AzureAIAgentFactory factory = new();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        this._kernel.Plugins.Add(plugin);

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel);

        await InvokeAgentAsync(agent!, "What is the latest new about the Semantic Kernel?");
    }

    [Fact]
    public async Task AzureAIAgentWithFileSearchAsync()
    {
        var text =
            $"""
            type: foundry_agent
            name: FileSearchAgent
            instructions: Answer questions using available files to provide grounding context.
            description: This agent answers questions using available files to provide grounding context.
            model:
              id: gpt-4o
              options:
                temperature: 0.4
            tools:
              - type: file_search
                description: Grounding with available files.
                options:
                  vector_store_ids:
                    - {TestConfiguration.AzureAI.VectorStoreId}
            """;
        AzureAIAgentFactory factory = new();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        this._kernel.Plugins.Add(plugin);

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel);
        Assert.NotNull(agent);

        await InvokeAgentAsync(agent!, "What are the key features of the Semantic Kernel?");
    }

    [Fact]
    public async Task AzureAIAgentWithOpenAPIAsync()
    {
        var text =
            """
            type: foundry_agent
            name: WeatherAgent
            instructions: Answer questions about the weather. For all other questions politely decline to answer.
            description: This agent answers question about the weather.
            model:
              id: gpt-4o-mini
              options:
                temperature: 0.4
            tools:
              - type: openapi
                id: GetCurrentWeather
                description: Retrieves current weather data for a location based on wttr.in.
                options:
                  specification: |
                    {
                      "openapi": "3.1.0",
                      "info": {
                        "title": "Get Weather Data",
                        "description": "Retrieves current weather data for a location based on wttr.in.",
                        "version": "v1.0.0"
                      },
                      "servers": [
                        {
                          "url": "https://wttr.in"
                        }
                      ],
                      "auth": [],
                      "paths": {
                        "/{location}": {
                          "get": {
                            "description": "Get weather information for a specific location",
                            "operationId": "GetCurrentWeather",
                            "parameters": [
                              {
                                "name": "location",
                                "in": "path",
                                "description": "City or location to retrieve the weather for",
                                "required": true,
                                "schema": {
                                  "type": "string"
                                }
                              },
                              {
                                "name": "format",
                                "in": "query",
                                "description": "Always use j1 value for this parameter",
                                "required": true,
                                "schema": {
                                  "type": "string",
                                  "default": "j1"
                                }
                              }
                            ],
                            "responses": {
                              "200": {
                                "description": "Successful response",
                                "content": {
                                  "text/plain": {
                                    "schema": {
                                      "type": "string"
                                    }
                                  }
                                }
                              },
                              "404": {
                                "description": "Location not found"
                              }
                            },
                            "deprecated": false
                          }
                        }
                      },
                      "components": {
                        "schemes": {}
                      }
                    }
            """;
        AzureAIAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel);
        Assert.NotNull(agent);

        await InvokeAgentAsync(agent!, "What is the current weather in Dublin?");
    }

    [Fact]
    public async Task AzureAIAgentWithOpenAPIYamlAsync()
    {
        var text =
            """
            type: foundry_agent
            name: WeatherAgent
            instructions: Answer questions about the weather. For all other questions politely decline to answer.
            description: This agent answers question about the weather.
            model:
              id: gpt-4o-mini
              options:
                temperature: 0.4
            tools:
              - type: openapi
                id: GetCurrentWeather
                description: Retrieves current weather data for a location based on wttr.in.
                options:
                  specification:
                    openapi: "3.1.0"  
                    info:  
                      title: "Get Weather Data"  
                      description: "Retrieves current weather data for a location based on wttr.in."  
                      version: "v1.0.0"  
                    servers:  
                      - url: "https://wttr.in"  
                    auth: []  
                    paths:  
                      /{location}:  
                        get:  
                          description: "Get weather information for a specific location"  
                          operationId: "GetCurrentWeather"  
                          parameters:  
                            - name: "location"  
                              in: "path"  
                              description: "City or location to retrieve the weather for"  
                              required: true  
                              schema:  
                                type: "string"  
                            - name: "format"  
                              in: "query"  
                              description: "Always use j1 value for this parameter"  
                              required: true  
                              schema:  
                                type: "string"  
                                default: "j1"  
                          responses:  
                            "200":  
                              description: "Successful response"  
                              content:  
                                text/plain:  
                                  schema:  
                                    type: "string"  
                            "404":  
                              description: "Location not found"  
                          deprecated: false  
                    components:  
                      schemes: {}  
            """;
        AzureAIAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel);
        Assert.NotNull(agent);

        await InvokeAgentAsync(agent!, "What is the current weather in Dublin?");
    }

    #region private
    private readonly Kernel _kernel;

    /// <summary>
    /// Invoke the agent with the user input.
    /// </summary>
    private async Task InvokeAgentAsync(KernelAgent agent, string input, bool? deleteAgent = true)
    {
        Microsoft.SemanticKernel.Agents.AgentThread? agentThread = null;
        try
        {
            await foreach (AgentResponseItem<ChatMessageContent> response in agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, input)))
            {
                agentThread = response.Thread;
                WriteAgentChatMessage(response);
            }
        }
        catch (Exception e)
        {
            Console.WriteLine($"Error invoking agent: {e.Message}");
        }
        finally
        {
            if (deleteAgent ?? true)
            {
                var azureaiAgent = agent as AzureAIAgent;
                Assert.NotNull(azureaiAgent);
                await azureaiAgent.Client.DeleteAgentAsync(azureaiAgent.Id);

                if (agentThread is not null)
                {
                    await azureaiAgent.Client.DeleteThreadAsync(agentThread.Id);
                }
            }
        }
    }
    #endregion
}
