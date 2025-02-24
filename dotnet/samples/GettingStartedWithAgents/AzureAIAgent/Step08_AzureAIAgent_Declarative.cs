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

        var agent = await factory.CreateAgentFromYamlAsync(this._kernel, text) as AzureAIAgent;

        await InvokeAgentAsync(agent, "Use code to determine the values in the Fibonacci sequence that that are less then the value of 101?");
    }

    [Fact(Skip = "Support for tool configuration will be added in a later PR")]
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
                schema: '{"openapi":"3.1.0","info":{"title":"RestCountries.NET API","description":"Web API version 3.1 for managing country items, based on previous implementations from restcountries.eu and restcountries.com.","version":"v3.1"},"servers":[{"url":"https://restcountries.net"}],"auth":[],"paths":{"/v3.1/currency":{"get":{"description":"Search by currency.","operationId":"LookupCountryByCurrency","parameters":[{"name":"currency","in":"query","description":"The currency to search for.","required":true,"schema":{"type":"string"}}],"responses":{"200":{"description":"Success","content":{"text/plain":{"schema":{"type":"string"}}}}}}}},"components":{"schemes":{}}}'
            """;
        AzureAIAgentFactory factory = new();

        var agent = await factory.CreateAgentFromYamlAsync(this._kernel, text) as AzureAIAgent;

        await InvokeAgentAsync(agent, "Use code to determine the values in the Fibonacci sequence that that are less then the value of 101?");
    }

    [Fact]
    public async Task AzureAIAgentWithLocalFunctionsAsync()
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

        var agent = await factory.CreateAgentFromYamlAsync(this._kernel, text) as AzureAIAgent;

        await InvokeAgentAsync(agent, "What is the special soup and how much does it cost?");
    }

    #region private
    private readonly Kernel _kernel;

    /// <summary>
    /// Invoke the agent with the user input.
    /// </summary>
    private async Task InvokeAgentAsync(AzureAIAgent? agent, string input)
    {
        // Create a thread for the agent conversation.
        AgentThread thread = await this.AgentsClient.CreateThreadAsync(metadata: SampleMetadata);

        // Respond to user input
        try
        {
            await InvokeAsync(input);
        }
        finally
        {
            await this.AgentsClient.DeleteThreadAsync(thread.Id);
            await this.AgentsClient.DeleteAgentAsync(agent!.Id);
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
