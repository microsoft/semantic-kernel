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
              configuration:
                connection_string: {TestConfiguration.AzureAI.ConnectionString}
            """;
        AzureAIAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text) as AzureAIAgent;

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

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel) as AzureAIAgent;

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

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel) as AzureAIAgent;
        Assert.NotNull(agent);

        await InvokeAgentAsync(agent!, "Use code to determine the values in the Fibonacci sequence that that are less then the value of 101?");
    }

    [Fact]
    public async Task AzureAIAgentWithFunctionsViaOptionsAsync()
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
                function_choice_behavior:
                  type: auto
                  functions:
                    - MenuPlugin.GetSpecials
                    - MenuPlugin.GetItemPrice
            """;
        AzureAIAgentFactory factory = new();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        this._kernel.Plugins.Add(plugin);

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel) as AzureAIAgent;
        Assert.NotNull(agent);

        await InvokeAgentAsync(agent!, "What is the special soup and how much does it cost?");
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
              - name: GetSpecials
                type: function
                description: Get the specials from the menu.
              - name: GetItemPrice
                type: function
                description: Get the price of an item on the menu.
                configuration:
                  parameters:
                    - name: menuItem
                      type: string
                      required: true
                      description: The name of the menu item.  
            """;
        AzureAIAgentFactory factory = new();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        this._kernel.Plugins.Add(plugin);

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel) as AzureAIAgent;
        Assert.NotNull(agent);

        await InvokeAgentAsync(agent!, "What is the special soup and how much does it cost?", false);
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
                description: Grounding with Bing Search service.
                configuration:
                  tool_connections:
                    - {TestConfiguration.AzureAI.BingConnectionId}
            """;
        AzureAIAgentFactory factory = new();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        this._kernel.Plugins.Add(plugin);

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel) as AzureAIAgent;
        Assert.NotNull(agent);

        await InvokeAgentAsync(agent!, "What is the latest new about the Semantic Kernel?", false);
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
                configuration:
                  vector_store_ids:
                    - {TestConfiguration.AzureAI.VectorStoreId}
            """;
        AzureAIAgentFactory factory = new();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        this._kernel.Plugins.Add(plugin);

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel) as AzureAIAgent;
        Assert.NotNull(agent);

        await InvokeAgentAsync(agent!, "What are the key features of the Semantic Kernel?", false);
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
                name: GetCurrentWeather
                description: Retrieves current weather data for a location based on wttr.in.
                configuration:
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

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel) as AzureAIAgent;
        Assert.NotNull(agent);

        await InvokeAgentAsync(agent!, "What is the current weather in Dublin?", false);
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
                name: GetCurrentWeather
                description: Retrieves current weather data for a location based on wttr.in.
                configuration:
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

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel) as AzureAIAgent;
        Assert.NotNull(agent);

        await InvokeAgentAsync(agent!, "What is the current weather in Dublin?");
    }

    #region private
    private readonly Kernel _kernel;

    /// <summary>
    /// Invoke the agent with the user input.
    /// </summary>
    private async Task InvokeAgentAsync(AzureAIAgent agent, string input, bool? deleteAgent = true)
    {
        // Create a thread for the agent conversation.
        AgentThread thread = await agent.Client.CreateThreadAsync(metadata: SampleMetadata);

        try
        {
            // Invoke agent and display the response.
            await InvokeAsync(input);
        }
        finally
        {
            if (deleteAgent ?? true)
            {
                await agent.Client.DeleteThreadAsync(thread.Id);
                await agent.Client.DeleteAgentAsync(agent!.Id);
            }
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            await agent!.AddChatMessageAsync(thread.Id, message);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(thread.Id))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }
    #endregion
}
