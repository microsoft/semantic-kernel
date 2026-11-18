// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Projects.Agents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Resources;

namespace GettingStarted.FoundryPromptAgents;

/// <summary>
/// This example demonstrates using a Microsoft Foundry Prompt Agent through a <see cref="ChatCompletionAgent"/> with templatized instructions.
/// </summary>
/// <remarks>
/// A Foundry Prompt Agent is a versioned agent definition (model, instructions, and tools) stored in a Foundry project.
/// It replaces the OpenAI Assistants API, which OpenAI shut down on August 26, 2026.
/// </remarks>
public class Step01_FoundryPromptAgent(ITestOutputHelper output) : BaseFoundryAgentTest(output)
{
    [Fact]
    public async Task UseTemplateForFoundryPromptAgent()
    {
        // Define the Prompt Agent. It stores the model; the templatized instructions are rendered by Semantic Kernel on every invocation.
        ProjectsAgentVersion promptAgent =
            await this.CreatePromptAgentAsync(
                "StoryTeller",
                new DeclarativeAgentDefinition(DeploymentName));

        // Define the agent. Instructions, Name and Description properties defined via the config.
        string generateStoryYaml = EmbeddedResource.Read("GenerateStory.yaml");
        PromptTemplateConfig templateConfig = KernelFunctionYaml.ToPromptTemplateConfig(generateStoryYaml);
        ChatCompletionAgent agent =
            new(templateConfig, new KernelPromptTemplateFactory())
            {
                // The kernel's chat service sends every request to the Prompt Agent.
                Kernel = this.CreateKernel(promptAgent),
                Arguments = new()
                {
                    { "topic", "Dog" },
                    { "length", "3" }
                }
            };

        // Create a thread for the agent conversation.
        AgentThread thread = new ChatHistoryAgentThread();

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
            await thread.DeleteAsync();
            await this.DeletePromptAgentAsync(promptAgent);
        }

        // Local function to invoke agent and display the response.
        async Task InvokeAgentAsync(KernelArguments? arguments = null)
        {
            await foreach (ChatMessageContent response in agent.InvokeAsync(thread, options: new() { KernelArguments = arguments }))
            {
                WriteAgentChatMessage(response);
            }
        }
    }
}
