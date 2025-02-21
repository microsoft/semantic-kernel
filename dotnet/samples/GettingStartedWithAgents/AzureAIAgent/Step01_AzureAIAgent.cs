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
public class Step01_AzureAIAgent(ITestOutputHelper output) : BaseAzureAgentTest(output)
{
    [Fact]
    public async Task UseTemplateForAzureAgentAsync()
    {
        // Define the agent
        string generateStoryYaml = EmbeddedResource.Read("GenerateStory.yaml");
        PromptTemplateConfig templateConfig = KernelFunctionYaml.ToPromptTemplateConfig(generateStoryYaml);
        // Instructions, Name and Description properties defined via the PromptTemplateConfig.
        Agent definition = await this.AgentsClient.CreateAgentAsync("gpt-4o", templateConfig.Name, templateConfig.Description, templateConfig.Template);
        AzureAIAgent agent = new(
            definition,
            this.AgentsClient,
            templateFactory: new KernelPromptTemplateFactory(),
            templateFormat: PromptTemplateConfig.SemanticKernelTemplateFormat)
        {
            Arguments =
            {
                { "topic", "Dog" },
                { "length", "3" }
            }
        };

        // Create a thread for the agent conversation.
        AgentThread thread = await this.AgentsClient.CreateThreadAsync(metadata: SampleMetadata);

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
            await this.AgentsClient.DeleteThreadAsync(thread.Id);
            await this.AgentsClient.DeleteAgentAsync(agent.Id);
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
