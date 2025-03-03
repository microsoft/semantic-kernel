// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI.Assistants;
using Resources;

namespace GettingStarted.OpenAIAssistants;

/// <summary>
/// This example demonstrates using <see cref="OpenAIAssistantAgent"/> with templatized instructions.
/// </summary>
public class Step01_Assistant(ITestOutputHelper output) : BaseAssistantTest(output)
{
    [Fact]
    public async Task UseTemplateForAssistantAgentAsync()
    {
        // Define the agent
        string generateStoryYaml = EmbeddedResource.Read("GenerateStory.yaml");
        PromptTemplateConfig templateConfig = KernelFunctionYaml.ToPromptTemplateConfig(generateStoryYaml);
        // Instructions, Name and Description properties defined via the PromptTemplateConfig.
        Assistant definition = await this.AssistantClient.CreateAssistantFromTemplateAsync(this.Model, templateConfig, metadata: SampleMetadata);
        OpenAIAssistantAgent agent = new(
            definition,
            this.AssistantClient,
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
        string threadId = await this.AssistantClient.CreateThreadAsync(metadata: SampleMetadata);

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
            await this.AssistantClient.DeleteThreadAsync(threadId);
            await this.AssistantClient.DeleteAssistantAsync(agent.Id);
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
