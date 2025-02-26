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
            type: azureai_agent
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
            type: azureai_agent
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

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel) as AzureAIAgent;
        Assert.NotNull(agent);

        await InvokeAgentAsync(agent!, "Use code to determine the values in the Fibonacci sequence that that are less then the value of 101?");
    }

    [Fact]
    public async Task AzureAIAgentWithOpenApiAsync()
    {
        var text =
            """
            type: azureai_agent
            name: AzureAIAgent
            description: AzureAIAgent Description
            instructions: AzureAIAgent Instructions
            model:
              id: gpt-4o-mini
            tools:
              - type: openapi
                name: RestCountriesAPI
                description: Web API version 3.1 for managing country items, based on previous implementations from restcountries.eu and restcountries.com.
                specification: '{"openapi":"3.1.0","info":{"title":"Get Weather Data","description":"Retrieves current weather data for a location based on wttr.in.","version":"v1.0.0"},"servers":[{"url":"https://wttr.in"}],"auth":[],"paths":{"/{location}":{"get":{"description":"Get weather information for a specific location","operationId":"GetCurrentWeather","parameters":[{"name":"location","in":"path","description":"City or location to retrieve the weather for","required":true,"schema":{"type":"string"}},{"name":"format","in":"query","description":"Always use j1 value for this parameter","required":true,"schema":{"type":"string","default":"j1"}}],"responses":{"200":{"description":"Successful response","content":{"text/plain":{"schema":{"type":"string"}}}},"404":{"description":"Location not found"}},"deprecated":false}}},"components":{"schemes":{}}}'
            """;
        AzureAIAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel) as AzureAIAgent;
        Assert.NotNull(agent);

        await InvokeAgentAsync(agent!, "What country has Dublin as it's capital city?");
    }

    [Fact]
    public async Task AzureAIAgentWithFunctionsAsync()
    {
        var text =
            """
            type: azureai_agent
            name: RestaurantHost
            instructions: Answer questions about the menu.
            description: This agent answers questions about the menu.
            model:
              id: gpt-4o-mini
              options:
                temperature: 0.4
            tools:
              - type: function
                name: MenuPlugin.GetSpecials
                description: Retrieves the specials for the day.
              - type: function
                name: MenuPlugin.GetItemPrice
                description: Retrieves the price of an item on the menu.
                parameters: 
            """;
        AzureAIAgentFactory factory = new();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        this._kernel.Plugins.Add(plugin);

        var agent = await factory.CreateAgentFromYamlAsync(text, this._kernel) as AzureAIAgent;

        await InvokeAgentAsync(agent!, "What is the special soup and how much does it cost?");
    }

    [Fact]
    public async Task AzureAIAgentWithFunctionsViaOptionsAsync()
    {
        var text =
            """
            type: azureai_agent
            name: RestaurantHost
            instructions: Answer questions about the menu.
            description: This agent answers questions about the menu.
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

    #region private
    private readonly Kernel _kernel;

    /// <summary>
    /// Invoke the agent with the user input.
    /// </summary>
    private async Task InvokeAgentAsync(AzureAIAgent agent, string input)
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
            await agent.Client.DeleteThreadAsync(thread.Id);
            await agent.Client.DeleteAgentAsync(agent!.Id);
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
