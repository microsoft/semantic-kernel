// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Resources;
using Agent = Azure.AI.Projects.Agent;

namespace GettingStarted.AzureAgents;

/// <summary>
/// This example demonstrates similarity between using <see cref="AzureAIAgent"/>
/// and other agent types.
/// </summary>
public class Step01_AzureAIAgent(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseTemplateForAzureAgentAsync()
    {
        // Define the agent
        string generateStoryYaml = EmbeddedResource.Read("GenerateStory.yaml");
        PromptTemplateConfig templateConfig = KernelFunctionYaml.ToPromptTemplateConfig(generateStoryYaml);

        AzureAIClientProvider clientProvider = this.GetAzureProvider();
        AgentsClient client = clientProvider.Client.GetAgentsClient();
        Agent definition = await client.CreateAgentAsync("gpt-4o", templateConfig.Name, templateConfig.Description, templateConfig.Template);
        // Instructions, Name and Description properties defined via the config.
        AzureAIAgent agent = new(definition, clientProvider)
        {
            Kernel = new Kernel(),
            Arguments = new KernelArguments()
            {
                { "topic", "Dog" },
                { "length", "3" },
            },
        };

        // Create a thread for the agent conversation.
        AgentThread thread = await client.CreateThreadAsync(metadata: AssistantSampleMetadata);

        try
        {
            // Invoke the agent with the default arguments.
            await InvokeAgentAsync();

            // Invoke the agent with the override arguments.
            await InvokeAgentAsync(
                new()
                {
                    { "topic", "Cat" },
                    { "length", "3" },
                });
        }
        finally
        {
            await client.DeleteThreadAsync(thread.Id);
            await client.DeleteAgentAsync(agent.Id);
        }

        // Local function to invoke agent and display the response.
        async Task InvokeAgentAsync(KernelArguments? arguments = null)
        {
            await foreach (ChatMessageContent response in agent.InvokeAsync(thread.Id, arguments))
            {
                WriteAgentChatMessage(response);
            }
        }
    }
}
