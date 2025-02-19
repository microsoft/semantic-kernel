// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;
using Agent = Azure.AI.Projects.Agent;

namespace GettingStarted.AzureAgents;

/// <summary>
/// This example demonstrates invoking Open API functions using <see cref="AzureAIAgent" />.
/// </summary>
/// <remarks>
/// Note: Open API invocation does not involve kernel function calling or kernel filters.
/// Azure Function invocation is managed entirely by the Azure AI Agent service.
/// </remarks>
public class Step06_AzureAIAgent_OpenAPI(ITestOutputHelper output) : BaseAzureAgentTest(output)
{
    [Fact]
    public async Task UseOpenAPIToolWithAgentAsync()
    {
        // Retrieve Open API specifications
        string apiCountries = EmbeddedResource.Read("countries.json");
        string apiWeather = EmbeddedResource.Read("weather.json");

        // Define the agent
        Agent definition = await this.AgentsClient.CreateAgentAsync(
            TestConfiguration.AzureAI.ChatModelId,
            tools:
            [
                new OpenApiToolDefinition("RestCountries", "Retrieve country information", BinaryData.FromString(apiCountries), new OpenApiAnonymousAuthDetails()),
                new OpenApiToolDefinition("Weather", "Retrieve weather by location", BinaryData.FromString(apiWeather), new OpenApiAnonymousAuthDetails())
            ]);
        AzureAIAgent agent = new(definition, this.AgentsClient)
        {
            Kernel = new Kernel(),
        };

        // Create a thread for the agent conversation.
        AgentThread thread = await this.AgentsClient.CreateThreadAsync(metadata: SampleMetadata);

        // Respond to user input
        try
        {
            await InvokeAgentAsync("What is the name and population of the country that uses currency with abbreviation THB");
            await InvokeAgentAsync("What is the weather in the capitol city of that country?");
        }
        finally
        {
            await this.AgentsClient.DeleteThreadAsync(thread.Id);
            await this.AgentsClient.DeleteAgentAsync(agent.Id);
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            await agent.AddChatMessageAsync(thread.Id, message);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(thread.Id))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }
}
