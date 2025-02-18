// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Resources;

namespace GettingStarted.OpenAIAssistants;

/// <summary>
/// This example demonstrates similarity between using <see cref="OpenAIAssistantAgent"/>
/// and other agent types.
/// </summary>
public class Step01_Assistant(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public async Task UseTemplateForAssistantAgentAsync()
    {
        // Define the agent
        string generateStoryYaml = EmbeddedResource.Read("GenerateStory.yaml");
        PromptTemplateConfig templateConfig = KernelFunctionYaml.ToPromptTemplateConfig(generateStoryYaml);

        // Instructions, Name and Description properties defined via the config.
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateFromTemplateAsync(
                clientProvider: this.GetClientProvider(),
                capabilities: new OpenAIAssistantCapabilities(this.Model)
                {
                    Metadata = AssistantSampleMetadata,
                },
                kernel: new Kernel(),
                defaultArguments: new KernelArguments()
                {
                    { "topic", "Dog" },
                    { "length", "3" },
                },
                templateConfig);

        // Create a thread for the agent conversation.
        string threadId = await agent.CreateThreadAsync(new OpenAIThreadCreationOptions { Metadata = AssistantSampleMetadata });

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
            await agent.DeleteThreadAsync(threadId);
            await agent.DeleteAsync();
        }

        // Local function to invoke agent and display the response.
        async Task InvokeAgentAsync(KernelArguments? arguments = null)
        {
            await foreach (ChatMessageContent response in agent.InvokeAsync(threadId, arguments))
            {
                WriteAgentChatMessage(response);
            }
        }
    }
}
